# Import necessary modules
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, time
import pytz
from collections import defaultdict


class EmployeeAttendance(models.Model):
	_name = "attendance.employee"
	_description = "Department DTR Data"
	_sort = 'name'

	dtr_line_ids = fields.One2many('attendance.employee.data', 'dtr_line_id')
	timelog_line_id = fields.Many2one('attendance.department', string="Timelog Line")
	paycode_id = fields.Many2one('base.payroll', string='Paycode')

	name = fields.Many2one('pay.employee', 'Name')
	emp_bio_id = fields.Integer('Bio ID')
	total_regular_hours = fields.Float(string='Reg (hrs)', compute="_compute_total_hours", store=True)
	total_overtime_hours = fields.Float(string='OT (hrs)', store=True)
	total_late_hours = fields.Float(string='Late (mins)',store=True)
	total_offset_hours = fields.Float(string='OFFS (hrs)', store=True)
	total_vacation_leave_hours = fields.Float(string='VL (hrs)', store=True)
	total_sick_leave_hours = fields.Float(string='SL (hrs)', store=True)
	total_leave_w_o_pay_hours = fields.Float(string='LWoP (hrs)', store=True)
	total_absent_hours = fields.Float(string='Absent (hrs)', store=True)
	total_undertime_hours = fields.Float(string='UT (hrs)', store=True)
 
	bday_leave = fields.Float(string='BL', store=True)
 
	all_verified = fields.Boolean('All Verified', compute='_compute_all_verified')
	is_verified = fields.Boolean("Verified", compute= '_compute_verified')
 

	@api.depends('dtr_line_ids.is_verified')
	def _compute_verified(self):
		for record in self:
			if any(not line.is_verified for line in record.dtr_line_ids):
				record.is_verified = False
			else:
				record.is_verified = True
		
	def refresh_data(self):
		print(self.name)
		print(self.paycode_id)

	@api.model
	def create(self, vals):
		datas = self.env['attendance.employee.data'].search([('name', '=', vals['name']), ('paycode_id', '=', vals['paycode_id'])])
		if len(datas) > 0:
			line_ids = []
			for data in datas:
				line_ids.append((4, data.id))
			vals['dtr_line_ids'] = line_ids
			return super(EmployeeAttendance, self).create(vals)
		else:
			return self

	@api.depends('dtr_line_ids.is_verified')
	def _compute_all_verified(self):
		for rec in self:
			rec.all_verified = all(rec.dtr_line_ids.mapped('is_verified')) if rec.dtr_line_ids else False

	@api.depends('dtr_line_ids')
	def _compute_total_hours(self):
		for record in self:
			record.total_regular_hours = sum([line_item.total_hours for line_item in record.dtr_line_ids])
			record.total_late_hours = sum([line_item.late_tardiness for line_item in record.dtr_line_ids])
			record.total_vacation_leave_hours = sum([line_item.vacation_leave for line_item in record.dtr_line_ids])
			record.total_sick_leave_hours = sum([line_item.sick_leave for line_item in record.dtr_line_ids])
			record.total_leave_w_o_pay_hours = sum([line_item.leave_wo_pay for line_item in record.dtr_line_ids])
			record.total_overtime_hours = sum([line_item.ot_hours for line_item in record.dtr_line_ids])
			record.total_offset_hours = sum([line_item.offset_hours for line_item in record.dtr_line_ids])
			record.total_absent_hours = sum([line_item.absent for line_item in record.dtr_line_ids])
			record.total_undertime_hours = sum([line_item.undertime for line_item in record.dtr_line_ids])
			record.bday_leave = sum([line_item.bday_leave for line_item in record.dtr_line_ids])

	def action_verify_all(self):
		self.dtr_line_ids.write({'is_verified': True})

	def action_unverify_all(self):
		self.dtr_line_ids.write({'is_verified': False})
  

class EmployeeAttendanceData(models.Model):
	_name = "attendance.employee.data"
	_description = "Department DTR Data"
	_sort = 'att_date asc'

	# Related Fields
	dtr_line_id = fields.Many2one('attendance.employee', string='att emp')
	att_summary_id = fields.Many2one('attendance.employee.summary', string='Summary')
	late_id = fields.Many2one('late.data', string='Late')
	discrepancy_id = fields.Many2one('base.payroll', string='Discrepancy', related='paycode_id')
	absent_id = fields.Many2one('base.payroll', string='Absent', related='paycode_id')
	paycode_id = fields.Many2one('base.payroll', string='Paycode')
	
	# Basic Information
	name = fields.Many2one('pay.employee', string="Name")
	att_date = fields.Date(string='Date')
	time_in = fields.Char(string="In")
	time_out = fields.Char(string="Out")
	raw_time_in = fields.Char(string="Raw Time-in")
	raw_time_out = fields.Char(string="Raw Time-out")

	# Leave Information
	vacation_leave = fields.Integer(string="VL")
	sick_leave = fields.Integer(string="SL")
	leave_wo_pay = fields.Integer(string="LWoP")
	bday_leave = fields.Integer(string="BL")
	
	# Time and Attendance
	total_hours = fields.Float(string="Reg (hrs)", compute='_compute', store=True)
	late_tardiness = fields.Float(string="Late (mins)", store=True)
	ot_hours = fields.Float(string="OT (hrs)")
	offset_hours = fields.Float(string="OFFS (hrs)")
	undertime = fields.Float(string="UT (mins)")
	absent = fields.Float(string="Absent (day)")
	remarks = fields.Char(string="Remarks")
 
	is_verified = fields.Boolean("Verified")
	discrepancy_status = fields.Selection([('ok', 'Ok'),('halfday', 'Halfday'),('undertime', 'Undertime'),('false_punch', 'False Punch'),('overtime', 'Overtime'),('absent', 'Absent')], string='Status', compute='_compute', store=True)
	tag_id = fields.Selection([('raw', 'Raw'),('edited', 'Edited'),('added', 'Added')], string='Tag', store=True, readonly=True)


	@api.depends('time_in', 'time_out')
	def _compute(self):
		for o in self:
			o.total_hours = o.late_tardiness = o.undertime = o.absent = 0
			discrepancy_status = None
			
			if o.time_in and o.time_out:
				time_in = datetime.strptime(o.time_in, '%H:%M').time()
				time_out = datetime.strptime(o.time_out, '%H:%M').time()
				work_start = datetime.combine(o.att_date, time(8, 00))
				am_grce_prd = datetime.combine(o.att_date, time(8, 15))
				work_end = datetime.combine(o.att_date, time(18, 00))
				lunch_start = datetime.combine(o.att_date, time(12, 00))
				lunch_end = datetime.combine(o.att_date, time(13, 00))
				pm_grce_prd = datetime.combine(o.att_date, time(13, 15))
				dt_in = datetime.combine(o.att_date, time_in)
				dt_out = datetime.combine(o.att_date, time_out)
				evnt_date_val = self.env['events'].search([]).mapped('event_date')
				evnt_or_wkend = o.att_date in evnt_date_val or o.att_date.weekday() >= 5
				grace_po = datetime.combine(o.att_date, time(11, 30))
				timeslap = datetime.combine(o.att_date, time(10, 00))

				if o.time_in != o.raw_time_in or o.time_out != o.raw_time_out:
					o.tag_id = 'edited'
				
				if dt_in <= am_grce_prd:
					dt_in = work_start
				elif grace_po <= dt_in < pm_grce_prd:
					dt_in = lunch_end
	 
				if dt_out > work_end:
					dt_out = work_end
				elif lunch_start < dt_out < pm_grce_prd:
					dt_out = lunch_start

				morn_work = min(dt_out, lunch_start) - dt_in
				aft_work = dt_out - max(dt_in, lunch_end)

				if dt_in < timeslap and dt_out > pm_grce_prd:
					total_work_s = morn_work.total_seconds() + aft_work.total_seconds()
	 
				elif (dt_in and dt_out) <= pm_grce_prd or (dt_in and dt_out) >= grace_po:
					total_work_s = (dt_out - dt_in).total_seconds()

				total_work_h = total_work_s / 3600
				late_min = max((dt_in - work_start).total_seconds() / 60, 0)
				ut_min = max((work_end - dt_out).total_seconds() / 60, 0)
	
				if (dt_in < dt_out and total_work_h > 1) and not evnt_or_wkend:
					o.total_hours = total_work_h
				
				if timeslap >= dt_in > am_grce_prd and not evnt_or_wkend:
					o.late_tardiness = late_min

				elif timeslap < dt_in <= grace_po and not evnt_or_wkend:
					o.absent += late_min / 60
 
				if total_work_h  < 1:
					discrepancy_status = 'false_punch'
				if (pm_grce_prd < dt_out < work_end or am_grce_prd < dt_out < lunch_start) and total_work_h  > 1 and not evnt_or_wkend:
					# o.undertime = ut_min
					o.absent += ut_min / 60
					discrepancy_status = 'undertime'
				if ((grace_po < dt_in and dt_out) or (dt_in and dt_out < pm_grce_prd)) and total_work_h  > 1 and not evnt_or_wkend:
					discrepancy_status = 'halfday'
					o.absent += 9 - total_work_h
				if evnt_or_wkend:
					discrepancy_status = 'overtime'
				if o.absent > 0 and discrepancy_status == None:
					discrepancy_status = 'absent'
     
				o.absent = o.absent / 9
				o.discrepancy_status = discrepancy_status
    
			elif not o.time_in and not o.time_out:
				o.tag_id = 'added'
				o.discrepancy_status = 'absent'
				o.absent = 1

	def fix_record(self):
		return {
			'name': 'Fix Record',
			'view_mode': 'form',
			'res_model': 'fix.record',
			'view_id': self.env.ref('payroll.fix_record_wizard_form').id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	@api.model
	def create(self, vals):
		record = super(EmployeeAttendanceData, self).create(vals)
		
		if record.name:
			summary = self.env['attendance.employee.summary'].search([('name', '=', record.name.id)], limit=1)
			if not summary:
				summary = self.env['attendance.employee.summary'].create({
					'name': record.name.id,})
			record.att_summary_id = summary
			
		return record

	def write(self, vals):
		result = super(EmployeeAttendanceData, self).write(vals)

		for record in self:
			if 'name' in vals:
				if record.name:
					summary = self.env['attendance.employee.summary'].search([('name', '=', record.name.id)], limit=1)
					if not summary:
						summary = self.env['attendance.employee.summary'].create({
							'name': record.name.id,
						})
					record.att_summary_id = summary
					
		return result
