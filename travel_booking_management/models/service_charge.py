# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ServiceChargeMaster(models.Model):
    _name = 'travel.service.charge'
    _description = 'Service Charge Master'
    _order = 'booking_type, sub_type'

    booking_type = fields.Selection([
        ('hotel', 'Hotel Booking'),
        ('domestic_flight_one_way', 'Domestic Flight - One Way'),
        ('domestic_flight_round_trip', 'Domestic Flight - Round Trip'),
        ('international_flight_one_way', 'International Flight - One Way'),
        ('international_flight_round_trip', 'International Flight - Round Trip'),
        ('train_general', 'Train - General'),
        ('train_tatkal', 'Train - Tatkal'),
        ('bus', 'Bus Booking'),
        ('event', 'Event Booking'),
        ('bus_cancellation', 'Bus Cancellation'),
        ('train_cancellation', 'Train Cancellation'),
        ('domestic_flight_one_way_cancel', 'Domestic Flight Cancellation - One Way'),
        ('domestic_flight_round_trip_cancel', 'Domestic Flight Cancellation - Round Trip'),
        ('intl_flight_one_way_cancel', 'Intl Flight Cancellation - One Way'),
        ('intl_flight_round_trip_cancel', 'Intl Flight Cancellation - Round Trip'),
        ('hotel_cancellation', 'Hotel Cancellation'),
    ], string='Booking / Cancellation Type', required=True)
    sub_type = fields.Char(string='Sub Type', help='Additional qualifier (e.g. tatkal, one_way)')
    charge_type = fields.Selection([
        ('fixed', 'Fixed Amount (per pax)'),
        ('percentage', 'Percentage of Booking Amount'),
    ], string='Charge Type', required=True, default='fixed')
    amount = fields.Float(string='Amount / Percentage', required=True,
                          help='Fixed amount per pax or percentage value depending on charge type')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_booking_type', 'unique(booking_type)',
         'A service charge entry already exists for this booking type.'),
    ]

    @api.model
    def get_service_charge(self, booking_type, booking_amount=0.0, num_pax=1):
        """Return the service charge amount for a given booking type."""
        record = self.search([('booking_type', '=', booking_type)], limit=1)
        if not record:
            return 0.0
        if record.charge_type == 'fixed':
            return round(record.amount * max(num_pax, 1), 2)
        else:
            return round(booking_amount * record.amount / 100.0, 2)
