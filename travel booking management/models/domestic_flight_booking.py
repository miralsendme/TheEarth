# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DomesticFlightBooking(models.Model):
    _name = 'travel.domestic.flight.booking'
    _description = 'Domestic Flight Booking'
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
    airline = fields.Char(string='Airline', required=True)
    flight_number = fields.Char(string='Flight Number (Onwards)')
    flight_number_return = fields.Char(string='Flight Number (Return)')
    origin_city = fields.Char(string='From City', required=True)
    destination_city = fields.Char(string='To City', required=True)
    departure_date = fields.Datetime(string='Departure Date & Time', required=True, tracking=True)
    arrival_date = fields.Datetime(string='Arrival Date & Time', required=True)
    trip_type = fields.Selection([
        ('one_way', 'One Way'),
        ('round_trip', 'Round Trip'),
    ], string='Trip Type', default='one_way', required=True)
    return_travel_date = fields.Datetime(string='Travel Date (Return)')
    return_origin = fields.Char(string='Return Origin')
    return_destination = fields.Char(string='Return Destination')
    return_departure_date = fields.Datetime(string='Return Departure')
    return_arrival_date = fields.Datetime(string='Return Arrival')
    travel_class = fields.Selection([
        ('economy', 'Economy'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business'),
    ], string='Class', default='economy', required=True)
    passenger_names = fields.Text(string='Name of Passenger(s)')
    num_passengers = fields.Integer(string='Passengers', compute='_compute_num_passengers',
                                    store=True, readonly=False)
    pnr_number = fields.Char(string='PNR Number')
    ticket_number = fields.Char(string='Ticket Number')
    baggage_allowance = fields.Char(string='Baggage Allowance')
    gross_amount = fields.Float(string='Gross Amount')
    total_amount = fields.Float(string='Net Amount', tracking=True)
    gst_amount = fields.Float(string='GST Amount')
    mode_of_payment = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
    ], string='Mode of Payment')
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
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.domestic.flight.booking') or _('New')
        return super().create(vals_list)

    @api.constrains('departure_date', 'arrival_date')
    def _check_dates(self):
        for rec in self:
            if rec.departure_date and rec.arrival_date and rec.departure_date >= rec.arrival_date:
                raise ValidationError(_('Arrival must be after departure.'))

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
                'default_booking_type': 'domestic_flight',
                'default_domestic_flight_booking_id': self.id,
                'default_partner_id': self.billing_company_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.total_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})
