# pyrefly: ignore [missing-import]
from odoo import models, fields

class EstateLog(models.Model):
    _name = 'estate.log'
    _description = 'User Action Log'
    _order = 'date desc, id desc'

    name = fields.Char(string='Action Name', required=True)
    user_id = fields.Many2one('res.users', string='User', required=False, default=lambda self: self.env.user)
    date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    action_type = fields.Selection([
        ('login', 'User Login'),
        ('create', 'Record Created'),
        ('write', 'Record Updated'),
        ('unlink', 'Record Deleted'),
        ('read', 'Record Read/Viewed'),
        ('custom', 'Custom Action')
    ], string='Action Type', required=True)
    
    model_name = fields.Char(string='Model Technical Name')
    model_desc = fields.Char(string='Model Description')
    res_id = fields.Integer(string='Record ID')
    res_name = fields.Char(string='Record Name')
    
    ip_address = fields.Char(string='IP Address')
    description = fields.Text(string='Action Details')
