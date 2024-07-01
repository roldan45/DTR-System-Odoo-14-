# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions
from odoo.tools import ormcache
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

class BiometricLog(models.Model):
    _name = "bio.raw.logs"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Biometric Log File"

    name = fields.Many2one("pay.employee", string="Employee Name")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    employee_bio_id = fields.Char(string="Employee Bio ID", related="name.biometric_id")
    raw_timelogs = fields.Datetime(string="Raw Timelogs")
    in_morning = fields.Integer(string="IN Morning")
    out_morning = fields.Integer(string="OUT Morning")
    in_afternoon = fields.Integer(string="IN Afternoon")
    out_afternoon = fields.Integer(string="OUT Afternoon")
    
    tag_id  = fields.Selection([('import', 'System Import'),('sl', 'User: Sick Leave'),('vl', 'User: Vacation Leave'),('lwop', 'User: Leave without Pay'),('offset', 'User: Offset')], string='Record Type', default='import')

    def delete_all_records(self):
        # self.env['bio.raw.logs'].sudo().search([]).unlink()
        self.env['attendance.employee.data'].sudo().search([]).unlink()
        self.env['attendance.department'].sudo().search([]).unlink()
        self.env['attendance.employee'].sudo().search([]).unlink()
        self.env['late.data'].sudo().search([]).unlink()
        self.env['late.data.summary'].sudo().search([]).unlink()
        self.env['attendance.employee.summary'].sudo().search([]).unlink()
