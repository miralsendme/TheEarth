# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CarBooking(models.Model):
    _name = 'travel.car.booking'
    _description = 'Car Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    billing_company_id = fields.Many2one('res.partner', string='Billing Company', required=True, tracking=True)
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, tracking=True)
    booking_executive = fields.Many2one('res.users', string='Booking Executive',
                                        default=lambda self: self.env.user, tracking=True)
    employee_code = fields.Char(string='Employee Code')
    document_number = fields.Char(string='Document Number / Requested By')
    confirmed_by = fields.Char(string='Confirmed By')
    cab_vendor = fields.Char(string='Cab Vendor')
    reference_number = fields.Char(string='Reference Number')
    description = fields.Text(string='Description')
    passenger_names = fields.Text(string='Name of Passenger(s)')
    num_passengers = fields.Integer(string='Passengers', compute='_compute_num_passengers',
                                    store=True, readonly=False)
    car_type = fields.Selection([
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('hatchback', 'Hatchback'),
        ('luxury', 'Luxury'),
        ('minivan', 'Minivan'),
        ('tempo', 'Tempo Traveller'),
    ], string='Car Type', default='sedan', required=True)
    rental_type = fields.Selection([
        ('self_drive', 'Self Drive'),
        ('with_driver', 'With Driver'),
        ('outstation', 'Outstation'),
        ('airport_transfer', 'Airport Transfer'),
    ], string='Rental Type', default='with_driver', required=True)
    pickup_location = fields.Char(string='Pickup Location', required=True)
    drop_location = fields.Char(string='Drop Location', required=True)
    pickup_date = fields.Datetime(string='Pickup Date & Time', required=True, tracking=True)
    drop_date = fields.Datetime(string='Drop Date & Time', required=True)
    driver_name = fields.Char(string='Driver Name')
    driver_phone = fields.Char(string='Driver Phone')
    vehicle_number = fields.Char(string='Vehicle Number')
    mode_of_payment = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
    ], string='Mode of Payment')
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

    @api.depends('passenger_names')
    def _compute_num_passengers(self):
        for rec in self:
            if rec.passenger_names:
                rec.num_passengers = len([l for l in rec.passenger_names.strip().splitlines() if l.strip()])
            else:
                rec.num_passengers = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.car.booking') or _('New')
        return super().create(vals_list)

    @api.constrains('pickup_date', 'drop_date')
    def _check_dates(self):
        for rec in self:
            if rec.pickup_date and rec.drop_date and rec.pickup_date >= rec.drop_date:
                raise ValidationError(_('Drop date must be after pickup date.'))

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
                'default_booking_type': 'car',
                'default_car_booking_id': self.id,
                'default_partner_id': self.billing_company_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.total_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})
