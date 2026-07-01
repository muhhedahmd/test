# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ir_model(models.Model):
    _inherit = 'ir.model'

    abstract = fields.Boolean('Abstract', readonly=True)

    @api.depends_context('is_access_rights')
    def _compute_display_name(self):
        super()._compute_display_name()
        if self.env.context.get('is_access_rights'):
            for model in self:
                model.display_name = "{} ({})".format(model.name, model.model)


class IrModelField(models.Model):
    _inherit = 'ir.model.fields'

    @api.depends_context('is_access_rights')
    def _compute_display_name(self):
        super()._compute_display_name()
        if self.env.context.get('is_access_rights'):
            for field in self:
                field.display_name = "{} => {} ({})".format(field.field_description, field.name, field.model_id.model)


class ir_module_module(models.Model):
    _inherit = 'ir.module.module'

    def _button_immediate_function(self, function):
        res = super(ir_module_module, self)._button_immediate_function(function)
        if function.__name__ in ['button_install', 'button_upgrade']:
            for record in self.env['ir.model'].search([]):
                if record.name == 'Email Thread':
                    pass
                record.abstract = self.env[record.model]._abstract
        return res
