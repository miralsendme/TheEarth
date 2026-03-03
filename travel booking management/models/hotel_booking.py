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
    billing_company_id = fields.Many2one('res.partner', string='Billing Company', required=True, tracking=True)
    hotel_name = fields.Char(string='Hotel Name', required=True)
    location = fields.Char(string='Location', required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)
    checkin_date = fields.Date(string='Check-in Date', required=True, tracking=True)
    checkout_date = fields.Date(string='Check-out Date', required=True, tracking=True)
    num_nights = fields.Integer(string='Number of Nights', compute='_compute_num_nights', store=True)
    num_rooms = fields.Integer(string='Number of Rooms', default=1, required=True)
    room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
        ('deluxe', 'Deluxe'),
        ('family', 'Family'),
    ], string='Room Type', default='double', required=True)
    guest_names = fields.Text(string='Name of Guest(s)')
    num_adults = fields.Integer(string='Number of Guest(s)', compute='_compute_num_adults', store=True, readonly=False)
    num_children = fields.Integer(string='Children', default=0)
    employee_code = fields.Char(string='Employee Code')
    document_number = fields.Char(string='Document Number / Requested By')
    mode_of_payment = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
    ], string='Mode of Payment')
    remark = fields.Text(string='Remark')
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, tracking=True)
    booking_service_provider = fields.Char(string='Booking Service Provider')
    booking_executive = fields.Many2one('res.users', string='Booking Executive', default=lambda self: self.env.user, tracking=True)
    meal_plan = fields.Selection([
        ('none', 'Room Only'),
        ('breakfast', 'Bed & Breakfast'),
        ('half_board', 'Half Board'),
        ('full_board', 'Full Board'),
        ('all_inclusive', 'All Inclusive'),
    ], string='Meal Plan', default='breakfast')
    total_amount = fields.Float(string='Total Amount', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    special_requests = fields.Text(string='Special Requests')
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
