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
    partner_id = fields.Many2one('res.partner', string='Billing Company', required=True, tracking=True)
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, tracking=True)
    booking_executive = fields.Many2one('res.users', string='Booking Executive',
                                        default=lambda self: self.env.user, tracking=True)
    employee_code = fields.Char(string='Employee Code / Mats Number')
    document_number = fields.Char(string='Document Number / Requested By')
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
    city = fields.Char(string='City', required=True)
    country_id = fields.Many2one('res.country', string='Country')
    location_type = fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International'),
    ], string='Location Type', default='domestic')
    checkin_date = fields.Date(string='Check In Date', tracking=True)
    checkout_date = fields.Date(string='Check Out Date', tracking=True)
    num_nights = fields.Integer(string='Number of Nights', compute='_compute_num_nights', store=True)
    hotel_name = fields.Char(string='Hotel Name')
    num_tickets = fields.Integer(string='Number of Guest(s)', default=1, required=True)
    seat_numbers = fields.Char(string='Seat Numbers')
    invoice_number = fields.Char(string='Invoice Number')
    mode_of_payment = fields.Selection([
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online'),
    ], string='Mode of Payment')
    payment_date = fields.Date(string='Payment Date')
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

    @api.depends('checkin_date', 'checkout_date')
    def _compute_num_nights(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date:
                rec.num_nights = (rec.checkout_date - rec.checkin_date).days
            else:
                rec.num_nights = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.event.booking') or _('New')
        return super().create(vals_list)

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
