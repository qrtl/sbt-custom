# Copyright 2020 Quartile Limited
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ErrorLogLine(models.Model):
    _name = "error.log.line"

    row_no = fields.Integer("Row Number")
    error_message = fields.Text("message")
    log_id = fields.Many2one("error.log", string="Log")


class ErrorLog(models.Model):
    _name = "error.log"
    _rec_name = "model_id"

    import_date = fields.Datetime("Imported On")
    import_user_id = fields.Many2one("res.users", "Imported By")
    log_line_ids = fields.One2many("error.log.line", "log_id", string="Log Lines")
    input_file = fields.Many2one("ir.attachment", string="File")
    file_path = fields.Binary(related="input_file.datas", string="Imported File")
    file_name = fields.Char(related="input_file.datas_fname", string="File")
    state = fields.Selection(
        [("done", "Succeed"), ("failed", "Failed")], string="Status"
    )
    model_id = fields.Many2one("ir.model", string="Model")
    model_name = fields.Char(related="model_id.model", string="Model Name")