# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelBooking(models.Model):
    _name = 'travel.hotel.booking'
    _description = 'Hotel Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, tracking=True)
    booking_executive = fields.Many2one('res.users', string='Booking Executive',
                                        default=lambda self: self.env.user, tracking=True)
    guest_names = fields.Text(string='Name of Guest(s)')
    num_adults = fields.Integer(string='Number of Guest(s)', compute='_compute_num_adults', store=True, readonly=False)
    employee_code = fields.Char(string='Employee Code')
    billing_company_id = fields.Many2one('res.partner', string='Billing Company', required=True, tracking=True)
    document_number = fields.Char(string='Doc. no./Req. by')
    location = fields.Char(string='Location', required=True)
    location_type = fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International'),
    ], string='Location Type')
    checkin_date = fields.Date(string='Check-in Date', required=True, tracking=True)
    checkout_date = fields.Date(string='Check-out Date', required=True, tracking=True)
    num_nights = fields.Integer(string='Number of Nights', compute='_compute_num_nights', store=True)
    hotel_name = fields.Char(string='Hotel Name', required=True)
    total_amount = fields.Float(string='Total Amount', tracking=True)
    mode_of_payment = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
    ], string='Mode of Payment')
    booking_service_provider = fields.Selection([
        ('aman_travels', 'Aman Travels Ltd (GRN)'),
        ('makemytrip', 'MAKEMYTRIP'),
        ('treebo', 'TREEBO'),
        ('goibibo', 'GOIBIBO'),
        ('airbnb', 'AIRBNB'),
        ('meril_travel_desk', 'Meril Travel Desk'),
        ('travel_plus', 'Travel Plus'),
        ('other', 'Other'),
    ], string='Booking Service Provider')
    remark = fields.Selection([
        ('corporate', 'CORPORATE'),
        ('retail', 'RETAIL'),
        ('same_day_checking', 'SAME DAY CHECKING(IF NOT MAPPED)'),
        ('not_available', 'CORPORATE HOTEL NOT AVAILABLE AT LOCATION'),
        ('pax_not_agreed', 'PAX NOT AGREED FOR CORPORATE'),
        ('sold_out', 'CORPORATE SOLD OUT'),
        ('not_in_budget', 'CORPORATE HOTEL NOT IN BUDGET'),
        ('rate_expired', 'Contracted rate expired'),
        ('other', 'Other'),
    ], string='Remarks')
    confirmed_by = fields.Many2one('res.users', string='Confirmed By', tracking=True)

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
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.hotel.booking') or _('New')
        return super().create(vals_list)

    @api.depends('guest_names')
    def _compute_num_adults(self):
        for rec in self:
            if rec.guest_names:
                rec.num_adults = len([line for line in rec.guest_names.strip().splitlines() if line.strip()])
            else:
                rec.num_adults = 0

    @api.depends('checkin_date', 'checkout_date')
    def _compute_num_nights(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date and rec.checkout_date > rec.checkin_date:
                rec.num_nights = (rec.checkout_date - rec.checkin_date).days
            else:
                rec.num_nights = 0

    @api.constrains('checkin_date', 'checkout_date')
    def _check_dates(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date and rec.checkin_date >= rec.checkout_date:
                raise ValidationError(_('Check-out date must be after check-in date.'))

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
                'default_booking_type': 'hotel',
                'default_hotel_booking_id': self.id,
                'default_partner_id': self.billing_company_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.total_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})
