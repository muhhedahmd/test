# pyrefly: ignore [missing-import]
from odoo import models, api, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    def _login(cls, db, login, password, user_agent_env=None):
        user_id = super(ResUsers, cls)._login(db, login, password, user_agent_env=user_agent_env)
        if user_id:
            try:
                ip = False
                try:
                    from odoo.http import request
                    if request and request.httprequest:
                        ip = request.httprequest.remote_addr
                except Exception:
                    pass

                from odoo.registry import Registry
                # Create a new cursor to write to log and commit immediately
                with Registry(db).cursor() as cr:
                    env = api.Environment(cr, user_id, {})
                    if 'estate.log' in env:
                        env['estate.log'].sudo().create({
                            'name': f"User logged in: {login}",
                            'action_type': 'login',
                            'user_id': user_id,
                            'ip_address': ip,
                            'description': f"User with login '{login}' successfully authenticated.",
                        })
            except Exception:
                pass
        return user_id
