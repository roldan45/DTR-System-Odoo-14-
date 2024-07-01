from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError

class LateDataSummary(models.Model):
    _name = "late.data.summary"
    _description = "Late Summary"

    line_item_ids = fields.One2many('late.data', 'line_item_id', string='Employee Late List')
    most_late_ids = fields.One2many('late.data', 'most_late_id')
    name = fields.Char(string='Late Summary Month')
    paycode_start_id = fields.Many2one('base.payroll', string="Start Paycode", domain="[('name', 'like', '%A%')]")
    date_from = fields.Date(string='Date From', related='paycode_start_id.date_from', store=True)
    paycode_end_id = fields.Many2one('base.payroll', string="End Paycode", domain="[('name', 'like', '%B%')]")
    date_to = fields.Date(string='Date to', related='paycode_end_id.date_to', store=True)
    

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError("Start date cannot be after end date!")

    def get_late_days(self):
        late_dates = []
        for record in self.line_item_ids:
            for lates in record.late_dtr_ids:
                late_dates.append(datetime.strptime(str(lates.att_date), '%Y-%m-%d').date())
        unique_late_dates = list(set(late_dates))
        sorted_late_dates = sorted(unique_late_dates)
        sorted_late_days = [date.day for date in sorted_late_dates]
        month_names = sorted(set(date.strftime('%B %Y') for date in sorted_late_dates), key=lambda x: datetime.strptime(x, '%B %Y'))
        month_item_count = [[month, sum(1 for date in unique_late_dates if date.strftime('%B') == month)] for month in [month.split()[0] for month in month_names]]
        return [month_item_count, sorted_late_days]

    @api.depends('line_item_ids', 'line_item_ids.late_dtr_ids')
    def automated(self):
        late_summary = self.create_data()
        return late_summary
        
    def create_data(self):
        
        self.env['late.data'].search([('line_item_id', '=', self.id)]).unlink()
        employees_dtrs = self.env['pay.employee'].search([])
        data_to_append = []
        over_late = []
        for employee in employees_dtrs:
            employee_data_start = self.env['attendance.employee.data'].search([
                ('name', '=', employee.id),
                ('paycode_id', '=', self.paycode_start_id.id),
                '|', ('late_tardiness', '>', 0), ('undertime', '>', 0),
            ])
            employee_data_end = self.env['attendance.employee.data'].search([
                ('name', '=', employee.id),
                ('paycode_id', '=', self.paycode_end_id.id),
                '|', ('late_tardiness', '>', 0), ('undertime', '>', 0),
            ])
            employee_data = employee_data_start | employee_data_end
            late_dtrs = [(4, late.id) for late in employee_data]
            vals = {'line_item_id': self.id, 'name': employee.id, 'late_dtr_ids': late_dtrs}
            created_data = self.env['late.data'].create(vals)
            data_to_append.append((4, created_data.id))
            if created_data.total_late_tardiness > 120 or created_data.late_count >= 10:
                over_late.append((4, created_data.id))
        self.write({'line_item_ids': data_to_append, 'most_late_ids': over_late})
        

class LateData(models.Model):
    _name = "late.data"
    _description = "Late"
    _order = 'name asc'

    line_item_id = fields.Many2one('late.data.summary', string='Employee Late List')
    most_late_id = fields.Many2one('late.data.summary', string='Employee Late List')
    late_dtr_ids = fields.One2many('attendance.employee.data', 'late_id')

    name = fields.Many2one('pay.employee', string="Employee Name", index=True)
    department_id = fields.Many2one('pay.department', string='Department', related='name.department_id')
    position_id = fields.Many2one('pay.position',string='Position', related='name.position_id')

    total_late_tardiness = fields.Float(string='Total Late(mins)', compute='_compute_late', store=True)
    late_count = fields.Integer(string='Late Count')

    total_undertime = fields.Float(string='Total Undertime')
    undertime_count = fields.Integer(string='Undertime Count', compute='_compute_undertime', store=True)

    @api.depends('late_dtr_ids')
    def _compute_late(self):
        for record in self:
            record.total_late_tardiness = sum([late.late_tardiness for late in record.late_dtr_ids])
            record.late_count = sum(1 for dtr in record.late_dtr_ids if dtr.late_tardiness > 0)

    @api.depends('late_dtr_ids')
    def _compute_undertime(self):
        for record in self:
            undertime_sum = sum([undertime.undertime for undertime in record.late_dtr_ids])
            record.undertime_count = sum(1 for dtr in record.late_dtr_ids if dtr.undertime > 0)
            record.total_undertime = undertime_sum