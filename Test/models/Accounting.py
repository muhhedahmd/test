from odoo import models, fields

class AccountCustomType(models.Model):
    _name = "account.custom.type"
    _description = "des"

    type = fields.Char(string="Name")
    des = fields.Char(string="des")

class Acconting(models.Model):
    _name = "account.move"
    account_custom_id = fields.Many2one("account.custom.type")
    name = fields.Char(string="name")