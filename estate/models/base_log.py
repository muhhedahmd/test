# pyrefly: ignore [missing-import]
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)

class Base(models.AbstractModel):
    _inherit = 'base'

    def _should_log(self):
        # 1. Ensure registry is fully loaded and estate.log exists
        if not self.pool.ready or 'estate.log' not in self.env:
            return False
        # 2. Exclude the log model itself, system logging, and Odoo internal models
        if self._name in ['estate.log', 'res.users.log'] or \
           self._name.startswith('ir.') or \
           self._name.startswith('mail.') or \
           self._name.startswith('bus.') or \
           self._name.startswith('web.'):
            return False
        return True

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Base, self).create(vals_list)
        if self._should_log():
            ip = False
            try:
                from odoo.http import request
                if request and request.httprequest:
                    ip = request.httprequest.remote_addr
            except Exception:
                pass

            for record in records:
                try:
                    rec_name = record.display_name or ''
                    self.env['estate.log'].sudo().create({
                        'name': f"Created {self._description or self._name}: {rec_name}",
                        'action_type': 'create',
                        'model_name': self._name,
                        'model_desc': self._description,
                        'res_id': record.id,
                        'res_name': rec_name,
                        'ip_address': ip,
                        'description': f"Created with values: {vals_list}",
                    })
                except Exception as e:
                    _logger.error("Failed to log create event for model %s: %s", self._name, str(e))
        return records

    def write(self, vals):
        if not self._should_log():
            return super(Base, self).write(vals)

        # Get old values before write
        old_values = {}
        fields_to_track = list(vals.keys())
        for record in self:
            old_vals = {}
            for field in fields_to_track:
                if field in record._fields:
                    try:
                        val = record[field]
                        if isinstance(val, models.BaseModel):
                            old_vals[field] = val.display_name if val else ''
                        else:
                            old_vals[field] = val
                    except Exception:
                        old_vals[field] = ''
            old_values[record.id] = old_vals

        result = super(Base, self).write(vals)

        ip = False
        try:
            from odoo.http import request
            if request and request.httprequest:
                ip = request.httprequest.remote_addr
        except Exception:
            pass

        for record in self:
            desc_lines = []
            for field, val in vals.items():
                if field not in record._fields:
                    continue
                old_val = old_values.get(record.id, {}).get(field, '')
                # Format new value
                new_val = record[field]
                if isinstance(new_val, models.BaseModel):
                    new_val_str = new_val.display_name if new_val else ''
                else:
                    new_val_str = str(new_val)
                
                desc_lines.append(f"- {field}: from '{old_val}' to '{new_val_str}'")

            if desc_lines:
                try:
                    rec_name = record.display_name or ''
                    self.env['estate.log'].sudo().create({
                        'name': f"Updated {self._description or self._name}: {rec_name}",
                        'action_type': 'write',
                        'model_name': self._name,
                        'model_desc': self._description,
                        'res_id': record.id,
                        'res_name': rec_name,
                        'ip_address': ip,
                        'description': '\n'.join(desc_lines),
                    })
                except Exception as e:
                    _logger.error("Failed to log write event for model %s: %s", self._name, str(e))
        return result

    def unlink(self):
        if self._should_log():
            ip = False
            try:
                from odoo.http import request
                if request and request.httprequest:
                    ip = request.httprequest.remote_addr
            except Exception:
                pass

            for record in self:
                try:
                    rec_name = record.display_name or ''
                    self.env['estate.log'].sudo().create({
                        'name': f"Deleted {self._description or self._name}: {rec_name}",
                        'action_type': 'unlink',
                        'model_name': self._name,
                        'model_desc': self._description,
                        'res_id': record.id,
                        'res_name': rec_name,
                        'ip_address': ip,
                        'description': f"Record ID {record.id} was deleted.",
                    })
                except Exception as e:
                    _logger.error("Failed to log unlink event for model %s: %s", self._name, str(e))
        return super(Base, self).unlink()

    def read(self, fields=None, load='_classic_read'):
        res = super(Base, self).read(fields=fields, load=load)
        # Log read operations for estate models when viewed individually (len == 1)
        if self._name in ['estate', 'estate.type'] and len(self) == 1 and not self.env.context.get('skip_read_log'):
            if self._should_log():
                try:
                    from odoo.http import request
                    if request and request.httprequest:
                        ip = request.httprequest.remote_addr
                        # Use skip_read_log context key to prevent recursion when reading display_name
                        self_sudo = self.sudo().with_context(skip_read_log=True)
                        rec_name = self_sudo.display_name or ''
                        self.env['estate.log'].sudo().with_context(skip_read_log=True).create({
                            'name': f"Viewed {self_sudo._description or self_sudo._name}: {rec_name}",
                            'action_type': 'read',
                            'model_name': self_sudo._name,
                            'model_desc': self_sudo._description,
                            'res_id': self_sudo.id,
                            'res_name': rec_name,
                            'ip_address': ip,
                            'description': f"User viewed the details of record: {rec_name}",
                        })
                except Exception as e:
                    _logger.error("Failed to log read event for model %s: %s", self._name, str(e))
        return res
