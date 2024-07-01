from odoo import api, fields, models
from datetime import datetime, timedelta



class PrintLateSummary(models.TransientModel):
    _name = "print.latesummary"
    _description = "Print Late Summary Wizard"

    name = fields.Many2one('late.data.summary', string='Month Period')
    
    def print(self):
        pass