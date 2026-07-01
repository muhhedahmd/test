# pyrefly: ignore [missing-import]
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class EstateType (models.Model):
    _name = 'estate.type'
    _description = 'Estate Type'
    # _rec_name = 'name'
    _order = "id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    estateType = fields.One2many('estate', 'Test2', string='Estate Type')
   
    def action_test_1(self):
        properties = self.env["estate"].search([])
        _logger.info("properties: %s", properties)
        return True
    #test 
    def action_test(self):
        _logger.info("test")
        for rec in self:
            _logger.info("record: %s", rec)
