from odoo import api, fields, models, _

class CreatePositionWizard(models.TransientModel):
    _name = "create.position.wizard"
    _description = "Create Position Wizard"

    name = fields.Char(string='Position')
    department_id = fields.Many2one('pay.department', string="Department", required=True)

    @api.model
    def default_get(self, fields):
        res = super(CreatePositionWizard, self).default_get(fields)
        active_id = self._context.get('active_id')
        if active_id:
        
            active_record = self.env['pay.department'].browse(active_id)
            res['department_id'] = active_record.id
        return res

    def action_create_position_wizard(self):
        position_vals = {
            'name': self.name,
            'department_id': self.department_id.id,
        }
        position = self.env['pay.position'].create(position_vals)
        
        # Redirect to the department form
        department = self.env['pay.department'].browse(self.department_id.id)
        return {
            'name': _('Position Created'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pay.department',
            'res_id': department.id,
        }