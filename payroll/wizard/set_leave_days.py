from odoo import api, fields, models
import logging
import pytz
from datetime import datetime, timedelta
import time
import threading


class SetLeaveDays(models.TransientModel):
    _name = "attendance.setleave"
    _description = "Set Leave Days Wizard"

    name = fields.Many2one('attendance.employee.summary', string='Employee')
    
    set_vacation_leave_days = fields.Integer('Set Vacation Leave Days', default=7)
    set_sick_leave_days = fields.Integer('Set Sick Leave Days', default=7)
    set_birthday_leave_days = fields.Integer('Set Birthday Leave Days', default=1)
    date_set = fields.Date(compute="compute_date_now", string="Date Set")
    
    @api.depends('name')
    def compute_date_now(self):
        for wizard in self:
            wizard.date_set = fields.Date.today()
            
            
    def set_leave(self):
        summary = self.env['attendance.employee.summary'].search([])
        for employee in summary:
            employee.vacation_leave_credits = self.set_vacation_leave_days
            employee.sick_leave_credits = self.set_sick_leave_days
            employee.birthday_leave_credits = self.set_birthday_leave_days
