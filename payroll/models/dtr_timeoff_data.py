import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class TimeOffData(models.Model):
	_name = "dtr.timeoff.data"
	_description = "Timeoff Data"

	time_off_id = fields.Many2one('dtr.timeoff', string='TimeOff')
 
	name = fields.Many2one('pay.employee', string='Employee Name')
	att_date = fields.Date(string='Date')
	time_in = fields.Char(string="In")
	time_out = fields.Char(string="Out")
 
	late_tardiness = fields.Float(string="Late (mins)", store=True)
	ot_hours = fields.Float(string="OT (hrs)")
	offset_hours = fields.Float(string="OFFS (hrs)")
	undertime = fields.Float(string="UT (mins)")
	absent = fields.Float(string="Absent (hrs)")
 
	vacation_leave = fields.Integer(string="VL")
	sick_leave = fields.Integer(string="SL")
	leave_wo_pay = fields.Integer(string="LWoP")
	bday_leave = fields.Integer(string="BL")
	total_hours = fields.Float(string="Reg (hrs)", compute='_compute', store=True)
	discrepancy_status = fields.Selection([('ok', 'Ok'),
										('halfday', 'Halfday'),
										('undertime', 'Undertime'),
										('false_punch', 'False Punch'),
										('overtime', 'Overtime'),
										('absent', 'Absent')], string='Status')
	is_applied = fields.Boolean(string='Is Applied', default=False)

	@api.onchange('name')
	def _get_default_name(self):
		if self.name.id == False:
			self.name = self.time_off_id.name.name.id

