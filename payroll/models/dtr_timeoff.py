import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class TimeOff(models.Model):
	_name = "dtr.timeoff"
	_description = "Create Timeoff"

	
	department_id = fields.Many2one('pay.department', string='Department', related='name.name.department_id')
	supervisor_id = fields.Many2one('pay.employee', string='Supervisor')
 
	name = fields.Many2one('attendance.employee.summary', string='Employee Name')
	date_request = fields.Date(string='Date of Request', default=datetime.datetime.today().date())
	date_from = fields.Date(string='Date From')
	date_to = fields.Date(string='Date To')
	time_in = fields.Char(string='Time In', default=8.0)
	time_out = fields.Char(string='Time Out', default='08 : 00 : 00')
	no_of_hrs = fields.Float(string='Number of Hours', compute='_compute_no_of_hrs')
	no_of_days = fields.Float(string='No of Days', compute='_compute_no_of_days')
	reason = fields.Text(string='Reason')

	time_off_type = fields.Selection(selection=[
		('sick', 'Sick Leave'),
		('vacation', 'Vacation Leave'),
		('birthday', 'Birthday Leave'),
		('lwop', 'Leave w/o Pay'),
		('overtime', 'Overtime'),
		('undertime', 'Undertime'),
		('offset', 'OFFset'),
	], string='Time OFF Type', required=True)
 
	vl_before = fields.Float(string='VL Before', readonly=True)
	sl_before = fields.Float(string='SL Before', readonly=True)
	offs_before = fields.Float(string='Offset Before', readonly=True)
	bl_before = fields.Float(string='B-Day Before',  readonly=True)
 
	vl_after = fields.Float(string='VL After', readonly=True)
	sl_after = fields.Float(string='SL After', readonly=True)
	offs_after = fields.Float(string='Offset After', readonly=True)
	bl_after = fields.Float(string='B-Day After', readonly=True)
	
	is_approved = fields.Boolean(string='Is Approved', default=False)
 
	state = fields.Selection(selection=[
		('unapproved', 'Unapproved'),
		('approved', 'Approved'),
		('applied', 'Applied'),
	], default='unapproved', string='State')

	record_ids = fields.One2many('dtr.timeoff.data', 'time_off_id', ondelete="cascade")
	initial_computation_done = fields.Boolean(default=False, string='Initial Computation Done', store=True)
 
 
	@api.depends('time_in', 'time_out')
	def _compute_no_of_hrs(self):
		for record in self:
			if record.time_in and record.time_out:
				record.no_of_hrs = record.time_out - record.time_in
			else:
				record.no_of_hrs = 0
 
	# @api.depends('name')
	def debug(self):#detect applied
		for record in self:
			employee_data = self.env['attendance.employee.data'].search([
				('name.id', '=', record.name.name.id),
				('att_date', '>=', record.date_from),
				('att_date', '<=', record.date_to)
			])
			print(employee_data)
			if (employee_data.name.id == record.name.name.id) and (employee_data.att_date == record.record_ids.att_date) and (employee_data.vacation_leave == record.record_ids.vacation_leave) and \
				(employee_data.sick_leave == record.record_ids.sick_leave) and \
				(employee_data.leave_wo_pay == record.record_ids.leave_wo_pay) and \
				(employee_data.bday_leave == record.record_ids.bday_leave):
				print(employee_data.name.id)
				print(record.name.name.id)
				print(employee_data.att_date)
				print(record.record_ids.att_date)
				print(employee_data.vacation_leave)
				print(record.record_ids.vacation_leave)
				print('match')
				record.state = 'applied'
			else:
				print('falsssee')

	
	def approved(self):
		data = self.record_ids
		days_per_date = self.no_of_days / len(data) if len(data) > 0 else 0
		for record in data:
			
			if self.time_off_type == 'vacation':
				record['vacation_leave'] = days_per_date
				
			elif self.time_off_type == 'sick':
				record['sick_leave'] = days_per_date
				
			elif self.time_off_type == 'lwop':
				record['leave_wo_pay'] = days_per_date
				
			elif self.time_off_type == 'birthday':
				record['bday_leave'] = days_per_date

			record['time_in'] = '8:00'
			record['time_out'] = '18:00'
			self.state = 'approved'
	
 
	def apply_value(self):
		employeee_data = self.env['attendance.employee.data'].search([
			('name.id', '=', self.name.name.id),
			('att_date', '>=', self.date_from),
			('att_date', '<=', self.date_to)
		])
		if employeee_data and self.state == 'approved':
			
			for record in self.record_ids:
				emp_data = {
					'vacation_leave': record.vacation_leave,
					'sick_leave': record.sick_leave,
					'leave_wo_pay': record.leave_wo_pay,
					'bday_leave': record.bday_leave,
					'time_in': record.time_in,
					'time_out': record.time_out,
				}
				employeee_data.filtered(lambda r: self.date_from <= r.att_date <= self.date_to).write(emp_data)
				self.state = 'applied'
		

	@api.depends('date_from', 'date_to')
	def _compute_no_of_days(self):
		for record in self:
			if record.date_from and record.date_to:
				delta_days = (record.date_to - record.date_from).days + 1
				no_of_days = 0
				for i in range(delta_days):
					current_date = record.date_from + timedelta(days=i)
					if current_date.weekday() < 5: 
						no_of_days += 1
				record.no_of_days = no_of_days
			else:
				record.no_of_days = 0
			record.compute_leave_after()
		
  
	@api.onchange('name', 'time_off_type')
	def compute_leave(self):
		for rec in self:
			if not rec.initial_computation_done and rec.name:
				rec.vl_before = rec.name.remaining_vacation_leave
				rec.sl_before = rec.name.remaining_sick_leave
				rec.bl_before = rec.name.remaining_birthday_leave
				rec.offs_before = rec.name.remaining_offset

				rec.vl_after = rec.vl_before
				rec.sl_after = rec.sl_before
				rec.bl_after = rec.bl_before
				rec.offs_after = rec.offs_before
				rec.initial_computation_done = True
	
			rec.compute_leave_after()

	def compute_leave_after(self):
		for liv in self:
			if liv.time_off_type == 'vacation':
				liv.vl_after = liv.vl_before - liv.no_of_days
			if liv.time_off_type == 'sick':
				liv.sl_after = liv.sl_before - liv.no_of_days
			if liv.time_off_type == 'birthday':
				liv.bl_after = liv.bl_before - liv.no_of_days
			if liv.time_off_type == 'overtime':
				liv.offs_after = liv.offs_before - liv.no_of_days
	
			# if liv.vl_after < 0 or liv.sl_after < 0 or liv.bl_after < 0 or liv.offs_after < 0:
			# 	raise ValidationError(_("Negative leave credits not allowed."))


	@api.onchange('name', 'date_to')
	def create_timeoff_data(self):
		timeoff_data = self.env['dtr.timeoff.data'].search([('time_off_id', '=', self.id)])
		timeoff_data.unlink()
		
		employees = self.env['attendance.employee.data'].search([
			('name.id', '=', self.name.name.id),
			('att_date', '>=', self.date_from),
			('att_date', '<=', self.date_to),
			('discrepancy_status', '!=', 'ok'),
   			('discrepancy_status', '!=', None)
		])
		self.record_ids = [(5, 0, 0)]
		for record in employees:
			emp_data = {
				'time_off_id': self.id,
				'name': record.name.id,
				'att_date': record.att_date,
				'time_in': record.time_in,
				'time_out': record.time_out,
	
				'late_tardiness': record.late_tardiness,
				'ot_hours': record.ot_hours,
				'offset_hours': record.offset_hours,
				'undertime': record.undertime,
				'absent': record.absent,
	
				'vacation_leave': record.vacation_leave,
				'sick_leave': record.sick_leave,
				'leave_wo_pay': record.leave_wo_pay,
				'bday_leave': record.bday_leave,
	
				'total_hours': record.total_hours,
				'discrepancy_status': record.discrepancy_status,
			}
			self.env['dtr.timeoff.data'].create(emp_data)
	
		
