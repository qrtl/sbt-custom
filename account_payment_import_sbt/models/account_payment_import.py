# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

import csv
import io
from base64 import b64decode
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError

IMPORT_FIELDS = [
    ["order_num", "注文番号", "char"],
    ["payment_amount", "入返金額", "float"],
    ["ip_exchange_rate", "為替レート", "float"],
    ["payment_date", "入金日", "date"],
    ["partner_ref", "shop CD", "char"],
    ["payment_method", "決済種別", "char"],
]


class AccountPaymentImport(models.TransientModel):
    _name = "account.payment.import"
    _description = "Account Payment Import"

    import_type = fields.Selection(
        [("sale", "Sales"), ("purchase", "Purchase")],
        string="Import Type",
        default="sale",
    )
    import_file = fields.Binary(string="File")
    file_name = fields.Char(string="File Name")

    def confirm_import_payment(self):
        sheet_fields, csv_iterator, error_log = self._load_import_file()
        model = "sale.order" if self.import_type == "sale" else "purchase.order"
        company = self.env.user.company_id
        write_off_account_id = company.write_off_account_id.id
        partner_dict = self._get_partner_dict(company)
        journal_dict = self._get_journal_dict(company)
        method_dict = self._get_method_dict()
        order_dicts = self._get_order_dicts(company)
        import_error = False
        payment_vals_list = []
        order_num_list = []
        for row in csv_iterator:
            row_dict, error_list = self._check_field_vals(row, sheet_fields)
            if row_dict["order_num"] in order_num_list:
                raise UserError(
                    _(
                        "There are records with the same order number: %s"
                        % (row_dict["order_num"])
                    )
                )
            order_num_list.append(row_dict["order_num"])

            row_dict, error_list = self._update_partner(
                row_dict, error_list, partner_dict
            )
            row_dict, error_list = self._update_invoice(
                model, row_dict, error_list, order_dicts, company
            )
            row_dict, error_list = self._update_journal(
                row_dict, error_list, journal_dict
            )
            # Create error log
            if error_list:
                import_error = True
                self.env["error.log.line"].create(
                    {
                        "log_id": error_log.id,
                        "row_no": csv_iterator.line_num,
                        "order_number": row_dict["order_num"],
                        "invoice_number": row_dict["invoice"],
                        "partner_ref": row_dict["partner_ref"],
                        "invoice_amount": row_dict["residual"],
                        "total_amount": row_dict["payment_amount"],
                        "journal": row_dict["payment_method"],
                        "error_message": "\n".join(error_list),
                    }
                )
            else:
                # Append vals to list
                payment_vals = self._get_payment_vals(
                    row_dict, error_log, company, method_dict, write_off_account_id
                )
                payment_vals_list.append(payment_vals)
        if not import_error:
            # Create payment
            for vals in payment_vals_list:
                self.env["account.payment"].create(vals)
            error_log.state = "done"
        return {
            "type": "ir.actions.act_window",
            "name": _("Import Result"),
            "res_model": "error.log",
            "view_type": "form",
            "view_mode": "form",
            "res_id": error_log.id,
            "view_id": self.env.ref("base_import_log.import_error_log_form").id,
            "target": "current",
        }

    def _get_partner_dict(self, company):
        res = {}
        partners = self.env["res.partner"].search(
            [
                "|",
                ("customer", "=", True),
                ("supplier", "=", True),
                ("ref", "!=", False),
                ("company_id", "=", company.id),
            ]
        )
        for partner in partners:
            res[partner.ref] = partner.id
        return res

    def _get_method_dict(self):
        res = {}
        methods = self.env["account.payment.method"].search([("code", "=", "manual")])
        for method in methods:
            res[method.payment_type] = method.id
        return res

    def _get_journal_dict(self, company):
        res = {}
        journals = self.env["account.journal"].search([("company_id", "=", company.id)])
        for journal in journals:
            currency = (
                journal.currency_id if journal.currency_id else company.currency_id
            )
            res[journal.name] = {
                "id": journal.id,
                "journal_currency_id": currency.id,
                "journal_currency_name": currency.name,
            }
        return res

    def _get_order_dicts(self, company):
        query = ""
        if self.import_type == "sale":
            query = """
SELECT
    so.name AS order,
    rp.ref AS partner_ref,
    base.invoice_id,
    ai.number AS invoice,
    ai.type,
    ai.reference,
    ai.residual,
    ai.currency_id,
    rc.name AS currency_name
FROM (
    WITH out_inv AS (
        SELECT
            sol.order_id,
            ail.invoice_id
        FROM sale_order_line_invoice_rel solir
            JOIN sale_order_line sol ON solir.order_line_id = sol.id
            JOIN account_invoice_line ail ON solir.invoice_line_id = ail.id
        WHERE
            ail.company_id = %(company_id)s
        GROUP BY
            sol.order_id,
            ail.invoice_id
    )
    SELECT * FROM out_inv
    UNION
    SELECT
        out_inv.order_id,
        rfai.id AS invoice_id
    FROM out_inv
        JOIN account_invoice ai ON out_inv.invoice_id = ai.id
        JOIN account_invoice rfai ON rfai.origin LIKE ai.number
            AND rfai.journal_id = ai.journal_id
    WHERE rfai.state = 'open'
        AND rfai.type = 'out_refund'
        AND rfai.origin IS NOT NULL
        AND ai.company_id = %(company_id)s
        AND rfai.company_id = %(company_id)s
    GROUP BY
        out_inv.order_id,
        rfai.id
) base
    JOIN sale_order so ON base.order_id = so.id
    JOIN account_invoice ai ON base.invoice_id = ai.id AND ai.state = 'open'
    JOIN res_partner rp ON ai.partner_id = rp.id
    JOIN res_currency rc ON ai.currency_id = rc.id
            """
            # This query may not perfectly capture the full records for
            # _get_invoiced() method of sale.order being rather complicated.
            # We implement the logic to salvage the corner-case invoices
            # (e.g. refund of refund) in _update_invoice() method of this
            # import.
        else:
            query = """
SELECT
    po.name AS order,
    rp.ref AS partner_ref,
    ai.id AS invoice_id,
    ai.number AS invoice,
    ai.type,
    ai.reference,
    ai.residual,
    ai.currency_id,
    rc.name AS currency_name
FROM account_invoice_purchase_order_rel aipor
    JOIN purchase_order po ON aipor.purchase_order_id = po.id
    JOIN res_partner rp ON po.partner_id = rp.id
    JOIN account_invoice ai ON aipor.account_invoice_id = ai.id
    JOIN res_currency rc ON ai.currency_id = rc.id
WHERE ai.state = 'open'
    AND ai.company_id = %(company_id)s
            """
        self._cr.execute(query, {"company_id": company.id})
        query_res = self._cr.dictfetchall()
        return query_res

    def _load_import_file(self):
        csv_data = b64decode(self.import_file)
        for encoding in ["shift-jis", "utf-8"]:
            try:
                csv_iterator = csv.reader(
                    io.StringIO(csv_data.decode(encoding)), delimiter=","
                )
                sheet_fields = next(csv_iterator)
                break
            except Exception:
                pass
        if not sheet_fields:
            raise UserError(_("Invalid file!"))

        missing_columns = list(
            {field[1] for field in IMPORT_FIELDS} - set(sheet_fields)
        )
        if missing_columns:
            raise UserError(
                _("Following columns are missing: \n %s" % ("\n".join(missing_columns)))
            )
        model = self.env["ir.model"].search([("model", "=", "account.payment.import")])
        ir_attachment = self.env["ir.attachment"].create(
            {
                "name": self.file_name,
                "datas": self.import_file,
                "datas_fname": self.file_name,
            }
        )
        error_log = self.env["error.log"].create(
            {
                "input_file": ir_attachment.id,
                "import_user_id": self.env.user.id,
                "import_date": datetime.now(),
                "state": "failed",
                "model_id": model.id,
            }
        )
        return sheet_fields, csv_iterator, error_log

    def _check_field_vals(self, row, sheet_fields):
        error_list = []
        row_dict = {}
        for field in IMPORT_FIELDS:
            field_key = field[0]
            field_value = row[sheet_fields.index(field[1])]
            field_type = field[2]
            row_dict[field_key] = field_value
            # missing field value
            if not field_value:
                error_list.append(_("%s is required." % field[1]))
            # numeric fields
            elif field_type == "float":
                try:
                    row_dict[field_key] = float(field_value)
                except Exception:
                    row_dict[field_key] = 0.0
                    error_list.append(_("%s only accepts numeric value." % field[1]))
            # date fields
            elif field_type == "date":
                try:
                    datetime.strptime(field_value, "%Y/%m/%d")
                except Exception:
                    error_list.append(_("Incorrect date format."))
        return row_dict, error_list

    def _update_partner(self, row_dict, error_list, partner_dict):
        row_dict["partner_id"] = partner_dict.get(row_dict["partner_ref"])
        if not row_dict["partner_id"]:
            error_list.append(_("Partner not found."))
        return row_dict, error_list

    def _update_invoice(self, model, row_dict, error_list, order_dicts, company):
        if model == "sale.order":
            invoice_type = (
                "out_invoice" if row_dict["payment_amount"] > 0 else "out_refund"
            )
        else:
            invoice_type = (
                "in_invoice" if row_dict["payment_amount"] > 0 else "in_refund"
            )
        row_dict["invoice"] = ""
        row_dict["invoice_id"] = False
        row_dict["reference"] = ""
        row_dict["residual"] = 0.0
        row_dict["currency_id"] = False
        row_dict["currency_name"] = ""
        odict = list(
            filter(
                lambda r: r["order"] == row_dict["order_num"]
                and r["type"] == invoice_type,
                order_dicts,
            )
        )
        if not odict:
            order = self.env[model].search(
                [("name", "=", row_dict["order_num"]), ("company_id", "=", company.id)],
                limit=1,
            )
            if not order:
                error_list.append(_("Order number not found."))
            else:
                # This part tries to salvage the corner-case invoices failed
                # to be captured in order_dicts.
                invoices = order.invoice_ids.filtered(
                    lambda x: x.type == invoice_type and x.state == "open"
                )
                if not invoices:
                    error_list.append(_("No open invoice for the order number."))
                elif len(invoices) > 1:
                    error_list.append(
                        _(
                            "Multiple invoices found %s"
                            % ",".join(invoice.number for invoice in invoices)
                        )
                    )
                elif row_dict["partner_ref"] != invoices.partner_id.ref:
                    error_list.append(
                        _(
                            "Partners are inconsistent between invoice and "
                            "payment: %s - %s"
                        )
                        % (row_dict["partner_ref"], invoices.partner_id.ref)
                    )
                else:
                    row_dict["invoice"] = invoices.number
                    row_dict["invoice_id"] = invoices.id
                    row_dict["residual"] = invoices.residual
                    row_dict["reference"] = invoices.reference
                    row_dict["currency_id"] = invoices.currency_id
                    row_dict["currency_name"] = invoices.currency_id.name
        elif len(odict) > 1:
            error_list.append(
                _("Multiple invoices found %s" % ",".join(o["invoice"] for o in odict))
            )
        elif row_dict["partner_ref"] != odict[0]["partner_ref"]:
            error_list.append(
                _("Partners are inconsistent between invoice and payment: %s - %s")
                % (row_dict["partner_ref"], odict[0]["partner_ref"])
            )
        else:
            row_dict["invoice"] = odict[0]["invoice"]
            row_dict["invoice_id"] = odict[0]["invoice_id"]
            row_dict["residual"] = odict[0]["residual"]
            row_dict["reference"] = odict[0]["reference"]
            row_dict["currency_id"] = odict[0]["currency_id"]
            row_dict["currency_name"] = odict[0]["currency_name"]
        return row_dict, error_list

    def _update_journal(self, row_dict, error_list, journal_dict):
        if row_dict["payment_method"] in journal_dict:
            jdict = journal_dict.get(row_dict["payment_method"])
            row_dict["journal_id"] = jdict["id"]
            if row_dict["currency_id"] != jdict["journal_currency_id"]:
                error_list.append(
                    _(
                        "Currencies are inconsistent between invoice and "
                        "journal: %s - %s"
                    )
                    % (
                        row_dict["currency_name"] or "N/A",
                        jdict["journal_currency_name"],
                    )
                )
        else:
            error_list.append(_("Journal not found."))
        return row_dict, error_list

    def _get_payment_vals(
        self, row_dict, log, company, method_dict, write_off_account_id
    ):
        payment_type = (
            "inbound"
            if row_dict["payment_amount"] >= 0
            and self.import_type == "sale"
            or row_dict["payment_amount"] < 0
            and self.import_type == "purchase"
            else "outbound"
        )
        return {
            "company_id": company.id,
            "payment_type": payment_type,
            "partner_type": "customer" if self.import_type == "sale" else "supplier",
            "partner_id": row_dict["partner_id"],
            "amount": abs(row_dict["payment_amount"]),
            "currency_id": row_dict["currency_id"],
            "payment_date": row_dict["payment_date"],
            "communication": row_dict["reference"],
            "payment_difference_handling": "open",
            "writeoff_label": "Write-Off",
            "journal_id": row_dict["journal_id"],
            "payment_method_id": method_dict.get(payment_type),
            "payment_token_id": False,
            "partner_bank_account_id": False,
            "writeoff_account_id": write_off_account_id,
            "invoice_ids": [(4, row_dict["invoice_id"], None)],
            "ip_exchange_rate": row_dict["ip_exchange_rate"],
            "is_imported": True,
            "log_id": log.id,
        }
