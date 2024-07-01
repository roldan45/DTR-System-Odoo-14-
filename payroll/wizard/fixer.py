from odoo import models, fields, api

class FixRecordWizard(models.TransientModel):
	_name = 'fix.record'
	_description = 'Fix Record Wizard'

	name = fields.Many2one(string='Name')
	att_date = fields.Date(string='Date')
	time_in = fields.Char(string="Time-in")
	time_out = fields.Char(string="Time-out")
 
	@api.model
	def default_get(self, fields):
		res = super(FixRecordWizard, self).default_get(fields)
		active_id = self._context.get('active_id')
		if active_id:
			active_record = self.env['attendance.employee.data'].sudo().browse(active_id)
			res['name'] = active_record.id
		return res

	def action_fix_record(self):
		data = {
			'name': self.name.id,
			'time_in': self.time_in,
			'time_out': self.time_out,
		}
		
		record = self.env['attendance.employee.data'].create(data)
		return {
			'name': _('Fixed'),
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'base.payroll',
			'res_id': record.id,
		}