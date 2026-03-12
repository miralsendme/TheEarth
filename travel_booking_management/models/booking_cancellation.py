# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class BookingCancellation(models.Model):
    _name = 'travel.booking.cancellation'
    _description = 'Booking Cancellation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Cancellation Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    booking_type = fields.Selection([
        ('hotel', 'Hotel'),
        ('domestic_flight', 'Domestic Flight'),
        ('international_flight', 'International Flight'),
        ('train', 'Train'),
        ('bus', 'Bus'),
        ('car', 'Car'),
        ('insurance', 'Insurance'),
        ('visa', 'Visa'),
        ('package_tour', 'Package Tour'),
        ('event', 'Event'),
    ], string='Booking Type', required=True, tracking=True)
    booking_ref = fields.Char(string='Booking Reference', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)

    # Linked booking records
    hotel_booking_id = fields.Many2one('travel.hotel.booking', string='Hotel Booking')
    domestic_flight_booking_id = fields.Many2one('travel.domestic.flight.booking', string='Domestic Flight Booking')
    international_flight_booking_id = fields.Many2one('travel.international.flight.booking', string='Intl Flight Booking')
    train_booking_id = fields.Many2one('travel.train.booking', string='Train Booking')
    bus_booking_id = fields.Many2one('travel.bus.booking', string='Bus Booking')
    car_booking_id = fields.Many2one('travel.car.booking', string='Car Booking')
    insurance_booking_id = fields.Many2one('travel.insurance.booking', string='Insurance Booking')
    visa_booking_id = fields.Many2one('travel.visa.booking', string='Visa Booking')
    package_tour_booking_id = fields.Many2one('travel.package.tour.booking', string='Package Tour Booking')
    event_booking_id = fields.Many2one('travel.event.booking', string='Event Booking')

    cancellation_date = fields.Date(string='Cancellation Date', default=fields.Date.context_today, required=True)
    reason = fields.Selection([
        ('change_of_plans', 'Change of Plans'),
        ('medical', 'Medical Emergency'),
        ('weather', 'Weather / Natural Disaster'),
        ('personal', 'Personal Reasons'),
        ('duplicate', 'Duplicate Booking'),
        ('price', 'Price Issue'),
        ('service', 'Service Issue'),
        ('other', 'Other'),
    ], string='Cancellation Reason', required=True)
    reason_details = fields.Text(string='Reason Details')
    booking_amount = fields.Float(string='Booking Amount')
    cancellation_charge = fields.Float(string='Cancellation Charge')
    refund_amount = fields.Float(string='Refund Amount', compute='_compute_refund', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    refund_mode = fields.Selection([
        ('original', 'Original Payment Method'),
        ('bank', 'Bank Transfer'),
        ('credit', 'Credit Note'),
    ], string='Refund Mode', default='original')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('refunded', 'Refunded'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('booking_amount', 'cancellation_charge')
    def _compute_refund(self):
        for rec in self:
            rec.refund_amount = max(rec.booking_amount - rec.cancellation_charge, 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.booking.cancellation') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'
            # Mark the original booking as cancelled
            booking = rec._get_linked_booking()
            if booking:
                booking.write({'state': 'cancelled', 'cancellation_id': rec.id})

    def action_refund(self):
        self.write({'state': 'refunded'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def _get_linked_booking(self):
        self.ensure_one()
        mapping = {
            'hotel': self.hotel_booking_id,
            'domestic_flight': self.domestic_flight_booking_id,
            'international_flight': self.international_flight_booking_id,
            'train': self.train_booking_id,
            'bus': self.bus_booking_id,
            'car': self.car_booking_id,
            'insurance': self.insurance_booking_id,
            'visa': self.visa_booking_id,
            'package_tour': self.package_tour_booking_id,
            'event': self.event_booking_id,
        }
        return mapping.get(self.booking_type)
