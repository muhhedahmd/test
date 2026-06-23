from odoo import models , fields
class Accounting(models.Model):
    _inherit = "account.move"
    x_custom_field = fields.Char(string="Name")

