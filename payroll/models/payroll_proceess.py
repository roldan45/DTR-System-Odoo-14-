from odoo import models, fields, api

class PayrollPayslip(models.Model):
    _name = 'payroll.payslip'
    
    employee_id = fields.Many2one('pay.employee', string="Employee")
    payroll_period_id = fields.Many2one('base.payroll', string="Payroll Period")
    gross_pay = fields.Float(string="Gross Pay")
    deductions = fields.Float(string="Deductions")
    net_pay = fields.Float(string="Net Pay", compute='_compute_net_pay')
    basic_salary = fields.Float(string="Basic Salary")
    overtime_hours = fields.Float(string="Overtime Hours")

    @api.depends('gross_pay', 'deductions')
    def _compute_net_pay(self):
        for payslip in self:
            payslip.net_pay = payslip.gross_pay - payslip.deductions


class PayrollProcess(models.Model):
    _name = 'payroll.process'
    
    name = fields.Many2one('base.payroll', string="Paycode")
    date_from = fields.Datetime(string='Date From', readonly=True)
    date_to = fields.Datetime(string='Date To', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft', string="Status")

    @api.model
    def get_paycode(self, vals):
        createpaycode = super(PayrollProcess, self).create(vals)
        get_paycodes = self.env['base.payroll'].search([('state', '=', 'done')])
        paycode = {
            'name': get_paycodes.id,
            'date_from': get_paycodes.date_from,
            'date_to': get_paycodes.date_to,
        }
        get_paycodes.create(paycode)
        return createpaycode
        
