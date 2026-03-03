# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EventBooking(models.Model):
    _name = 'travel.event.booking'
    _description = 'Event Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    event_name = fields.Char(string='Event Name', required=True)
    event_type = fields.Selection([
        ('conference', 'Conference'),
        ('concert', 'Concert'),
        ('sports', 'Sports'),
        ('exhibition', 'Exhibition'),
        ('festival', 'Festival'),
        ('workshop', 'Workshop'),
        ('other', 'Other'),
    ], string='Event Type', default='conference', required=True)
    venue = fields.Char(string='Venue', required=True)
    city = fields.Char(string='City', required=True)
    country_id = fields.Many2one('res.country', string='Country')
    event_date = fields.Datetime(string='Event Date & Time', required=True, tracking=True)
    event_end_date = fields.Datetime(string='Event End Date & Time')
    num_tickets = fields.Integer(string='Number of Tickets', default=1, required=True)
    ticket_category = fields.Selection([
        ('general', 'General'),
        ('vip', 'VIP'),
        ('premium', 'Premium'),
        ('backstage', 'Backstage'),
    ], string='Ticket Category', default='general', required=True)
    seat_numbers = fields.Char(string='Seat Numbers')
    total_amount = fields.Float(string='Total Amount', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    cancellation_id = fields.Many2one('travel.booking.cancellation', string='Cancellation', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.event.booking') or _('New')
        return super().create(vals_list)

    @api.constrains('event_date', 'event_end_date')
    def _check_dates(self):
        for rec in self:
            if rec.event_date and rec.event_end_date and rec.event_date >= rec.event_end_date:
                raise ValidationError(_('End date must be after start date.'))

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Booking'),
            'res_model': 'travel.booking.cancellation',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_booking_type': 'event',
                'default_event_booking_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.total_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})
