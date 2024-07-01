from odoo import api, fields, models


class Events(models.Model):
    _name = "events"
    _description = "Events"
    _order = 'event_date desc'
    
    name = fields.Char(string='Holiday Event', store=True)
    type_id = fields.Selection([
        ('holiday', 'Holiday'),
        ('others', 'Others')
    ], string='Type')
    event_date = fields.Date(string='Event Date', store=True)
    is_nonworking = fields.Boolean('Is Non-working?')
    
