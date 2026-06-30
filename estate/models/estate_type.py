# pyrefly: ignore [missing-import]
from odoo import models, fields
class EstateType (models.Model):
    _name = 'estate.type'
    _description = 'Estate Type'
    # _rec_name = 'name'
    _order = "id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    estateType = fields.One2many('estate', 'Test2', string='Estate Type')
    def action_test(self):
        properties = self.env["estate"].search([])
        print(properties)
        return True
