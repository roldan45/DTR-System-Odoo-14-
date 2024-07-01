# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo import tools, _
from odoo import modules
from odoo.exceptions import ValidationError, Warning
from odoo.modules.module import get_module_resource
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.modules.module import get_module_resource
from werkzeug.urls import url_encode
from collections import defaultdict
import random
import logging
import time
import base64


class DepartmentId(models.Model):
	_name = "pay.department"
	_description = "Department"
	_order = 'name'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	name = fields.Char(string='Department')
	department_manager = fields.Char(string='Department Manager')
	position_ids = fields.One2many('pay.position', 'department_id', string="Job Position", readonly="1")
	
	@api.onchange('name')
	def _onchange_name(self):
		if self.name:
			positions = self.env['pay.position'].search([('department_id.name', '=', self.name)])
			self.position_ids = [(6, 0, positions.ids)]
		return {}
	

class PositionId(models.Model):
	_name = "pay.position"
	_description = "Position ID"
	_order = 'name'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	name = fields.Char(string='Job Position')
	department_id = fields.Many2one('pay.department', string="Department", required=True)
	job_description = fields.Text(string="Job Description")
	

class ProjectId(models.Model):
	_name = "pay.project"
	_description = "Project ID"
	_order = 'name'
	
	name = fields.Char(string='Project')


class PayrollDTR(models.Model):
	_name = "base.payroll"
	_description = "Base Payroll"

	department_line_ids = fields.One2many('attendance.department', 'base_payroll_id', string='Departments')
	discrepancy_ids = fields.One2many('attendance.employee.data', 'discrepancy_id', string='Discrepancy Report', domain=[('discrepancy_status', '!=', 'ok'), ('discrepancy_status', '!=', None), ('discrepancy_status', '!=', 'absent')])
	absent_ids = fields.One2many('attendance.employee.data', 'absent_id', string='Absent', domain=[('absent', '=', 1)])
	holiday_id = fields.Many2one('events')
 
	name = fields.Char(string="Paycode")
	date_from = fields.Date(string='Date From')
	date_to = fields.Date(string='Date To')
	all_verified = fields.Boolean(string="All Verified", compute='_compute_all_verified')
	state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done')], default='draft', string="Status", compute="_compute_state")
	total_workdays = fields.Integer(string='Total Workdays', compute='_compute_total')
	total_holiday = fields.Integer(string='Total Holiday', compute='_compute_total')
 
 
	@api.depends('holiday_id.event_date')
	def _compute_total(self):
	 
		existing_dates = self.env['attendance.employee.data'].search([('att_date', '>=', self.date_from),('att_date', '<=', self.date_to)]).mapped('att_date')
		date_counts = defaultdict(int)
		for date in existing_dates:
			date_counts[date] += 1
		working_days = [date for date, count in date_counts.items() if count > 10 and fields.Date.from_string(date).weekday() < 5]
		holiday_count = self.env['events'].search([
			('event_date', '<=', self.date_to),
			('event_date', '>=', self.date_from),
			('event_date', 'in', working_days)
		])
		self.total_holiday = len(holiday_count)
		self.total_workdays = len(working_days) - self.total_holiday
  
	def debug(self):
		abs_ids = self.absent_ids
		for abs_id in abs_ids:
			abs_id._compute_total_hours()
		
	def create_absent(self):

		existing_dates = self.env['attendance.employee.data'].search([('att_date', '>=', self.date_from),('att_date', '<=', self.date_to)]).mapped('att_date')
		date_counts = defaultdict(int)
		for date in existing_dates:
			date_counts[date] += 1
   
		# for date, count in date_counts.items():
		# 	print(f"{date}: {count}")

		working_days = [date for date, count in date_counts.items() if count > 10 and fields.Date.from_string(date).weekday() < 5]
		# print('working days: ', len(working_days))
		event_date_values = self.env['events'].search([
			('event_date', '<=', self.date_to), 
			('event_date', '>=', self.date_from)
		]).mapped('event_date') 

		employees = self.env['attendance.employee.data'].search([])
		employees_attendance = defaultdict(list)
		for employee in employees:
			employees_attendance[employee.name].append(employee.att_date)

		for employee, attendance_dates in employees_attendance.items():
			for day in working_days:
				if day not in attendance_dates and day not in event_date_values:
					employee_record = self.env['attendance.employee'].search([('paycode_id', '=', self.name), ('name', '=', employee.id)])
					for record in employee_record:
						if record:
							self.env['attendance.employee.data'].create({
								'name': employee.id,
								'dtr_line_id': record.id,
								'att_date': day,
								# 'absent': 9,
								'paycode_id': self.id
							})

	@api.depends('department_line_ids.state')
	def _compute_all_verified(self):
		for record in self:
			if not record.department_line_ids:
				record.all_verified = False
			else:
				record.all_verified = all(department.state == 'done' for department in record.department_line_ids)

	@api.depends('department_line_ids', 'all_verified')
	def _compute_state(self):
		for record in self:
			if record.all_verified == True:
				record.state = 'done'
			elif record.department_line_ids:
				record.state = 'in_progress'
			elif record.all_verified == False:
				record.state = 'draft'
 
	def process_data(self):
		self._delete_records('attendance.employee.data', [('paycode_id', '=', self.id)])
		self._delete_records('attendance.employee', [('paycode_id', '=', self.id)])
		self._delete_records('attendance.department', [('paycode_id', '=', self.id)])
		self.process_raw_logs()
		
	def process_raw_logs(self):
		log_records = self._get_log_records()
		if log_records:
			for i in log_records:
				self._create_employee_data(i)
			self.create_depts()
		else:
			pass
		self.create_absent()
		
	def _get_log_records(self):
		query = """
			SELECT 
				name,
				DATE(raw_timelogs AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila') AS log_date,
				MIN(raw_timelogs AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila') AS time_in_ph,
				MAX(raw_timelogs AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila') AS time_out_ph
			FROM 
				bio_raw_logs
			WHERE 
				DATE(raw_timelogs AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila') >= %s 
				AND DATE(raw_timelogs AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila') < %s
			GROUP BY 
				name, DATE(raw_timelogs AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')
		"""
		self.env.cr.execute(query, (self.date_from, self.date_to))
		return self.env.cr.dictfetchall()
	
	def _create_employee_data(self, i):
		if not i['name'] or i.get('tag_id') =='edited':
			return

		time_in = i['time_in_ph'].time()
		time_out = i['time_out_ph'].time()
		vals = {
			'name': i['name'],
			'paycode_id': self.id,
			'att_date': i['log_date'],
			'time_in': time_in.strftime("%H:%M"),
			'time_out': time_out.strftime("%H:%M"),
			'raw_time_in': time_in.strftime("%H:%M"),
			'raw_time_out': time_out.strftime("%H:%M"),
   			'tag_id': 'raw'
		}
		self.env['attendance.employee.data'].create(vals)

	def create_depts(self):
		depts = self.env['pay.department'].search([])
		dept_items = [(0, 0, {'name': dept.id, 'paycode_id': self.id}) for dept in depts]
		self.write({'department_line_ids': dept_items})

	def _delete_records(self, model, domain):
		self.env[model].search(domain).unlink()

	def unlink(self):
		for i in self:
			self.env['attendance.department'].search([('base_payroll_id','=', i.id)]).unlink()
			self.env['attendance.employee'].search([('paycode_id','=', i.id)]).unlink()
			self.env['attendance.employee.data'].search([('paycode_id','=', i.id)]).unlink()
			return super(PayrollDTR, self).unlink()

	
class DepartmentAttendance(models.Model):
	_name = "attendance.department"
	_description = "Department DTR"
	_order = 'name'

	timelog_line_ids = fields.One2many('attendance.employee', 'timelog_line_id')
	base_payroll_id = fields.Many2one('base.payroll', string="Paycode")
 
	name = fields.Many2one('pay.department', string="Department")
	total_employees = fields.Integer(string='Total Employees', compute='_compute_employees')
	state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft', string="Status", compute='_compute_state')
	paycode_id = fields.Many2one('base.payroll', string='Paycode', store=True)
 
	date_from = fields.Date(string='Date From', compute='_compute_dates', store=True)
	date_to = fields.Date(string='Date To', compute='_compute_dates', store=True)
 
	all_verified = fields.Boolean('All Verified', compute='_compute_all_verified')
	
	@api.depends('state','all_verified')
	def _compute_state(self):
		for record in self:
			if record.all_verified == True:
				record.state = 'done'
			else:
				record.state = 'draft'

	def action_verify_all(self):
	 
		i = self.timelog_line_ids
		i.write({'is_verified': True})

		o = i.dtr_line_ids
		o.write({'is_verified': True})

	def action_unverify_all(self):
		i = self.timelog_line_ids
		i.write({'is_verified': False})

		o = i.dtr_line_ids
		o.write({'is_verified': False})
	
	def refresh_data(self):
		self.refresh()

	def action_draft(self):
		self.write({'state': 'draft'})
	
	def action_done(self):
		self.write({'state': 'done'})
  
	@api.depends('paycode_id')
	def _compute_dates(self):
		for i in self:
			if i.paycode_id:
				i.date_from = i.paycode_id.date_from
				i.date_to = i.paycode_id.date_to
	 
	@api.depends('timelog_line_ids')
	def _compute_employees(self):
		for s in self:
			s.total_employees = len(s.timelog_line_ids)

	@api.model
	def create(self, vals):
		vals['timelog_line_ids'] = self.get_att_employee(vals)
		return super(DepartmentAttendance, self).create(vals)

	def get_line_items(self):
		employee_line = []
		for i in self:
			vals = {'name': i.name.id,
					'paycode_id': i.paycode_id,
					'emp_bio_id': i.name.biometric_id}
			employee_line = i.get_att_employee(vals)
			i.write({'timelog_line_ids': employee_line})

	def get_att_employee(self, vals):
		emps = self.env['pay.employee'].search([('department_id', '=', vals['name'])])
		employee_line_obj = []
		for i in emps:
			emp_vals = {'name': i.id,
						'paycode_id': vals['paycode_id'],
						'emp_bio_id': i.biometric_id}
			emp_dtr = self.env['attendance.employee'].create(emp_vals)
			employee_line_obj.append((4, emp_dtr.id))
		return employee_line_obj

	@api.onchange('timelog_line_ids.is_verified')
	def _compute_all_verified(self):
		for i in self:
			i.all_verified = all(i.timelog_line_ids.mapped('is_verified')) if i.timelog_line_ids or len(i.timelog_line_ids) == 0 else False
	
