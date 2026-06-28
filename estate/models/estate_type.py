# pyrefly: ignore [missing-import]
from odoo import models, fields
class EstateType (models.Model):
    _name = 'estate.type'
    _description = 'Estate Type'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    estateType = fields.One2many('estate', 'Test2', string='Estate Type')
