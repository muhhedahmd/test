from odoo import models , fields
class Accounting(models.Model):
    _inherit = "account.move"
    custom_type = fields.Char(string="Name")

