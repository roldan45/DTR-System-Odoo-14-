from odoo import api, fields, models


class EmployeeAttendanceSummary(models.Model):
    _name = "attendance.employee.summary"
    _description = "Employee Attendance Summary"
    _sort = 'name asc'

    attendance_ids = fields.One2many('attendance.employee.data', 'att_summary_id', string="Dtr")
    name = fields.Many2one('pay.employee', string='Employee', store=True)

    total_regular_hours_per_year = fields.Float(string='Regular hrs', compute="_compute_all", store=True)
    total_late_hours_per_year = fields.Float(string='Late mins', compute="_compute_all", store=True)
    total_vacation_leave_hours_per_year = fields.Float(string='VL hrs', compute="_compute_all", store=True)
    total_sick_leave_hours_per_year = fields.Float(string='SL hrs', compute="_compute_all", store=True)
    total_leave_w_o_pay_hours_per_year = fields.Float(string='L w/o P hrs', compute="_compute_all", store=True)
    total_overtime_hours_per_year = fields.Float(string='OT hrs', compute="_compute_all", store=True)
    total_offset_hours_per_year = fields.Float(string='Offset hrs', compute="_compute_all", store=True)
    total_undertime_hours_per_year = fields.Float(string='Undertime mins', compute="_compute_all", store=True)
    total_birthday = fields.Float(string='Birthday', compute="_compute_all")
    total_absent = fields.Float(string='Absent', compute="_compute_all")
    
    vacation_leave_credits = fields.Float(string='Vacation Credits', store=True)
    sick_leave_credits = fields.Float(string='Sick Credits', store=True)
    birthday_leave_credits = fields.Float(string='Birthday Credits', store=True)

    remaining_offset = fields.Float(string='Remaining Offset', compute='_compute_all', store=True)
    remaining_vacation_leave = fields.Float(string='Remaining VL', compute='_compute_all', store=True)
    remaining_sick_leave = fields.Float(string='Remaining SL', compute='_compute_all', store=True)
    remaining_birthday_leave = fields.Float(string='Remaining B-day', compute='_compute_all', store=True)

    progress_late = fields.Float(string='Late Progress', compute='_compute_all')
    progress_vacation_leave = fields.Float(string='VL Progress', compute='_compute_all')
    progress_sick_leave = fields.Float(string='SL Progress', compute='_compute_all')

    @api.depends('attendance_ids', 'attendance_ids.total_hours', 'attendance_ids.late_tardiness', 'attendance_ids.vacation_leave',
                 'attendance_ids.sick_leave', 'attendance_ids.leave_wo_pay', 'attendance_ids.ot_hours', 'attendance_ids.offset_hours',
                 'attendance_ids.undertime', 'attendance_ids.bday_leave', 'vacation_leave_credits', 'sick_leave_credits', 'birthday_leave_credits')
    def _compute_all(self):
        for record in self:
            
            record.total_regular_hours_per_year = sum(record.attendance_ids.mapped('total_hours'))
            record.total_late_hours_per_year = sum(record.attendance_ids.mapped('late_tardiness'))
            record.total_vacation_leave_hours_per_year = sum(record.attendance_ids.mapped('vacation_leave'))
            record.total_sick_leave_hours_per_year = sum(record.attendance_ids.mapped('sick_leave'))
            record.total_leave_w_o_pay_hours_per_year = sum(record.attendance_ids.mapped('leave_wo_pay'))
            record.total_overtime_hours_per_year = sum(record.attendance_ids.mapped('ot_hours'))
            record.total_offset_hours_per_year = sum(record.attendance_ids.mapped('offset_hours'))
            record.total_undertime_hours_per_year = sum(record.attendance_ids.mapped('undertime'))
            record.total_birthday = sum(record.attendance_ids.mapped('bday_leave'))
            record.total_absent = sum(record.attendance_ids.mapped('absent'))

            record.remaining_vacation_leave = record.vacation_leave_credits - record.total_vacation_leave_hours_per_year
            record.remaining_sick_leave = record.sick_leave_credits - record.total_sick_leave_hours_per_year
            record.remaining_birthday_leave = record.birthday_leave_credits - record.total_birthday
            record.remaining_offset = record.total_overtime_hours_per_year - record.total_offset_hours_per_year

            progress_late = (100 - ((record.total_late_hours_per_year / 120) * 100))
            record.progress_late = progress_late if progress_late >= 0 else 0
            
            if record.vacation_leave_credits != 0:
                record.progress_vacation_leave = (record.remaining_vacation_leave / record.vacation_leave_credits) * 100
            else:
                record.progress_vacation_leave = 0
                
            if record.sick_leave_credits != 0:
                record.progress_sick_leave = (record.remaining_sick_leave / record.sick_leave_credits) * 100
            else:
                record.progress_sick_leave = 0
                
    def refresh(self):
        records = self.env['attendance.employee.summary'].search([])
        for record in records:
            record._compute_all()
        return True
