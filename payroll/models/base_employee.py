# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo import tools, _
from odoo import modules
from odoo.exceptions import ValidationError, Warning
from odoo.modules.module import get_module_resource
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.modules.module import get_module_resource
from werkzeug.urls import url_encode
import random
import logging
import time
import base64


class Employee(models.Model):
    _name = "pay.employee"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]
    _description = "Employee File"
    _order = "name"


    name = fields.Char(string="Employee Name", compute="_compute_full_name", store=True)
    employee_id = fields.Char(string="Employee Id")
    image_employee = fields.Image(string="Image", store=True)
    
    # General Info
    lastname = fields.Char(string="Last Name", required=True)
    firstname = fields.Char(string="First Name", required=True)
    middlename = fields.Char(string="Middle Name")
    suffixname = fields.Char(string="Suffix Name")
    gender = fields.Selection([('male', 'Male'),('female', 'Female'),('other', 'Other')], string='Gender')
    birthday = fields.Date(string="Birthday", required=True)
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    email = fields.Char(string="Email")
    mobile_no = fields.Char(string="Mobile No.")

    # Employment
    position_id = fields.Many2one("pay.position", string="Position", domain="[('department_id', '=', department_id)]")
    department_id = fields.Many2one("pay.department", string="Department")
    project_id = fields.Many2one("pay.project", string="Projects")
    rfid_number = fields.Char(string="RFID Number")
    biometric_id = fields.Char(string="Biometric ID")
    date_start = fields.Date(string="Date Start",required=True)
    date_resigned = fields.Date(string="Date End")
    is_resigned = fields.Boolean(string="Resigned / In-Active")
    date_resigned_in_past = fields.Boolean(string="Resignation Date in Past", compute="_compute_resignation_date_in_past", store=True)
    gen_info_verified = fields.Boolean(string='Gen. Info Verified')
    
    # Bank Information
    bank_acct_no = fields.Char(string="Bank Account No.")
    atm_no = fields.Char(string="ATM No.")
    atm_cash = fields.Selection([('atm', 'ATM'),('cash', 'Cash')], string="ATM/Cash")
    sort_no = fields.Integer(string="Sort No.")
    
    # Government Id
    sss_no = fields.Char(string="SSS No.")
    philhealth_no = fields.Char(string="Philhealth No.")
    hdmf_no = fields.Char(string="HDMF/Pagibig No.")
    tin_no = fields.Char(string="TIN")
    
    sss_verified = fields.Boolean(string='SSS Verified')
    philhealth_verified = fields.Boolean(string='Philhealth Verified')
    hdmf_verified = fields.Boolean(string='HDMF Verified')
    tin_verified = fields.Boolean(string='Tin Verified')
    
    # Deductions
    sss_cont = fields.Float(string="SSS Contribution")
    philhealth_cont = fields.Float(string="Philhealth Contribution")
    hdmf_cont = fields.Float(string="Pagibig Contribution")
    
    sss_loan = fields.Float(string="SSS Loan")
    sss_loan_end = fields.Date(string="SSS Loan End Date")
    hdmf_loan = fields.Float(string="Pagibig Loan")
    hdmf_loan_end = fields.Date(string="Pagibig Loan End Date")
    
    salary_per_month = fields.Float(string="Salary Per Month", tracking=True)
    salary_per_day = fields.Float(string="Salary Per Day", tracking=True)
    
    sss_cal_loan = fields.Float(string="SSS Calamity Loan", tracking=True)
    sss_cal_loan_end = fields.Date(string="SSS Calamity Loan End Date", tracking=True)
    hdmf_cal_loan = fields.Float(string="Pagibig Calamity Loan", tracking=True)
    hdmf_cal_loan_end = fields.Date(string="Pagibig Loan End Date", tracking=True)
    

    @api.depends("firstname", "lastname", "middlename", "suffixname")
    def _compute_full_name(self):
        for i in self:
            names = [i.lastname, i.firstname, i.middlename, i.suffixname]
            i.name = ", ".join(filter(None, names))

    @api.depends("birthday")
    def _compute_age(self):
        for record in self:
            if record.birthday:
                birth_date = fields.Date.from_string(record.birthday)
                today = fields.Date.context_today(record)
                if birth_date > today:
                    raise ValidationError("Birth date cannot be in the future.")
                record.age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    @api.onchange("firstname", "lastname", "middlename", "suffixname")
    def _onchange_capitalize_names(self):
        for field in ["firstname", "lastname", "middlename", "suffixname"]:
            if getattr(self, field):
                setattr(self, field, getattr(self, field).title())

    @api.constrains("birthday")
    def _check_valid_birthday(self):
        for i in self:
            if i.birthday and i.birthday > fields.Date.today():
                raise ValidationError("Birthday cannot be in the future.")

    @api.constrains("date_start", "date_resigned")
    def _check_valid_dates(self):
        for i in self:
            if (i.date_start and i.date_resigned and i.date_resigned < i.date_start):
                raise ValidationError("Resignation date cannot be earlier than the start date.")

    @api.depends("date_resigned")
    def _compute_resignation_date_in_past(self):
        for i in self:
            i.date_resigned_in_past = i.date_resigned and i.date_resigned < fields.Date.today()
            i.is_resigned = bool(i.date_resigned)
    
    @api.constrains('mobile_no')
    def _check_mobile_no(self):
        for i in self:
            if i.mobile_no:
                if not i.mobile_no.isdigit():
                    raise ValidationError("Mobile number should only contain digits.")
                if len(i.mobile_no) != 11: 
                    raise ValidationError("Mobile number should be 11 digits.")
