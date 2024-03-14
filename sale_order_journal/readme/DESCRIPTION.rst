This module does the following:

- Adds "Payment Method" (account.journal) field to sale order.
- Adds "Advance Received Account" field to journal. Then, If this field is assigned
  to a journal and that journal is selected in a sale order, the "Advance Received Account"
  will be propagated to the account_id of the invoice.
  