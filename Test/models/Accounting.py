from odoo import models, fields

class AccountCustomType(models.Model):
    _name = "account.custom.type"
    _description = "Accounting Custom Types"

    custom_type = fields.Char(string="Name")