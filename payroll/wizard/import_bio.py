from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, time
import pytz
import base64
from multiprocessing import Process


class WizardImportTimelogs(models.TransientModel):
    _name = "import.bio.logs.wizard"
    _description = "Import Timelog Wizard"

    name = fields.Binary(string='Timelog file', required=True)
    paycode = fields.Many2one('base.payroll', string='Paycode')
    from_date = fields.Date('FROM Date', required=True)
    to_date = fields.Date('TO Date', required=True)

    @api.onchange('paycode')
    def onchange_paycode(self):
        self.from_date = self.paycode.date_from
        self.to_date = self.paycode.date_to

    def check_file(self):
        decoded_file = base64.b64decode(self.name).decode('utf-8')
        rows = decoded_file.strip().split('\n')

        start_datetime = self.convert_to_utc(datetime.combine(self.from_date, time.min))
        end_datetime = self.convert_to_utc(datetime.combine(self.to_date, time.max.replace(microsecond=0)))

        self.delete_raw_logs(start_datetime, end_datetime)

        for row in rows:
            columns = row.strip().split('\t')

            emp_obj = self.env['pay.employee'].search([('biometric_id', '=', columns[0])])
            timelog = self.convert_to_utc(datetime.strptime(columns[1], "%Y-%m-%d %H:%M:%S"))

            raw_vals = {
                'name': emp_obj.id,
                'date_from': self.from_date,
                'date_to': self.to_date,
                'employee_bio_id': columns[0],
                'raw_timelogs': timelog,
                'in_morning': columns[2],
                'out_morning': columns[3],
                'in_afternoon': columns[4],
                'out_afternoon': columns[5],
            }

            if start_datetime <= timelog <= end_datetime:
                self.env['bio.raw.logs'].create(raw_vals)

    def delete_raw_logs(self, start_datetime, end_datetime):
        del_raw_logs = Process(target=self.unlink_raw_logs(start_datetime, end_datetime))
        del_raw_logs.start()
        del_raw_logs.join()

    def unlink_raw_logs(self, start_datetime, end_datetime):
        self.env['bio.raw.logs'].search([
            ('raw_timelogs', '>=', start_datetime),
            ('raw_timelogs', '<=', end_datetime),
            ('tag_id', '=', 'import')
        ]).unlink()

    @staticmethod
    def convert_to_utc(date_time):
        if isinstance(date_time, str):
            datetime_obj = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
        elif isinstance(date_time, datetime):
            datetime_obj = date_time
        else:
            raise ValueError("Input must be a string or datetime object")

        ph_timezone = pytz.timezone('Asia/Manila')
        localized_datetime_obj = ph_timezone.localize(datetime_obj)
        utc_datetime_object = localized_datetime_obj.astimezone(pytz.utc)

        return utc_datetime_object.replace(tzinfo=None)
