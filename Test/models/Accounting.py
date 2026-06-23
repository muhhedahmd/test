from odoo import models, fields

class AccountCustomType(models.Model):
    _name = "account.custom.type"
    _description = "des"

    type = fields.Char(string="Name")
    des = fields.Char(string="des")