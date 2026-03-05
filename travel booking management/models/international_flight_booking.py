# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class InternationalFlightBooking(models.Model):
    _name = 'travel.international.flight.booking'
    _description = 'International Flight Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, tracking=True)
    booking_executive = fields.Many2one('res.users', string='Booking Executive',
                                        default=lambda self: self.env.user, tracking=True)
    passenger_names = fields.Text(string='Name of Passenger(s)')
    num_passengers = fields.Integer(string='Number of Passenger(s)', compute='_compute_num_passengers',
                                    store=True, readonly=False)
    employee_code = fields.Char(string='Employee Code')
    billing_company_id = fields.Many2one('res.partner', string='Billing Company', required=True, tracking=True)
    document_number = fields.Char(string='Doc. no./Req. by')
    origin_city = fields.Char(string='Onward - Origin', required=True)
    destination_city = fields.Char(string='Onward - Destination', required=True)
    return_origin = fields.Char(string='Return Origin')
    return_destination = fields.Char(string='Return Destination')
    trip_type = fields.Selection([
        ('one_way', 'One Way'),
        ('round_trip', 'Round Trip'),
    ], string='Travel Type', default='one_way', required=True)
    travel_date_onward = fields.Date(string='Travel Date (Onward)', required=True, tracking=True)
    return_date = fields.Date(string='Return Date (Return)')
    ticket_number = fields.Char(string='Ticket Number')
    pnr_number = fields.Char(string='PNR Number',
                              help="USE CRS PNR / BOOKING REFERENCE NO IF LCC AIRLINE (DON'T PUT AO NO)")
    flight_number = fields.Char(string='Flight Number Onward')
    flight_number_return = fields.Char(string='Flight Number Return')
    travel_class = fields.Selection([
        ('economy', 'Economy'),
        ('business', 'Business'),
        ('first', 'First'),
    ], string='Class of Booking', default='economy', required=True)
    airline = fields.Char(string='Airline Name', required=True)
    gross_amount = fields.Float(string='Gross Amount (Total value)')
    total_amount = fields.Float(string='Net Amount (Total value)', tracking=True)
    gst_amount = fields.Float(string='GST Amount')
    mode_of_payment = fields.Selection([
        ('akbar_new', 'Akbar Online Booking Company Pvt Ltd - New'),
        ('akbar_old', 'Akbar Online Booking Company Pvt Ltd - Old'),
        ('akbar_travels', 'Akbar Travels of India'),
        ('aman_travels', 'Aman Travels Ltd'),
        ('axis_cc_ace_ketan_8304', 'Axis CC ACE Ketan Thakkar - 8304'),
        ('axis_cc_vistara_deep_1236', 'Axis CC Vistara Deep Thakkar - 1236'),
        ('axis_cc_vistara_ketan_0710', 'Axis CC Vistara Ketan Thakkar - 0710'),
        ('axis_cc_vistara_nirav_1868', 'Axis CC Vistara Nirav Thakkar - 1868'),
        ('axis_cc_flipkart_nirav_7148', 'Axis CC Flipkart Nirav Thakkar - 7148'),
        ('axis_cc_flipkart_deep_5592', 'Axis CC Flipkart Deep Thakkar - 5592'),
        ('hdfc_bank_ac_card_2697', 'Hdfc Bank Ac: 50200006844535 / Card - xx2697'),
        ('hdfc_earth_card_0481', 'HDFC The Earth Travel Card - 0481'),
        ('hdfc_cc_nirav_4323', 'Hdfc CC Nirav Thakkar - 4323'),
        ('hdfc_debit_nirav_5100', 'Hdfc Debit Nirav - 5100'),
        ('icici_cc_meril_india_1003', 'Icici CC - Meril India - 1003'),
        ('icici_cc_meril_pvt_2001', 'Icici CC - Meril Pvt - 2001'),
        ('go_airlines', 'Go Airlines (India) Ltd'),
        ('interglobe', 'Interglobe Aviation Limited'),
        ('spicejet', 'Spicejet Limited'),
        ('air_asia', 'Air Asia (India) Limited'),
        ('riya_offline', 'Riya Travels & Tours - Offline'),
        ('riya_online', 'Riya Travel & Tours - Online'),
        ('ideal_visum', 'Ms Ideal Visum India Pvt Ltd'),
        ('hdfc_cc_nirav_9222', 'HDFC CC Nirav Thakkar - 9222'),
        ('kotak_dc_deep_5555', 'Kotak DC Deep Thakkar - 5555'),
        ('kotak_dc_ketan_5423', 'Kotak DC Ketan Thakkar - 5423'),
        ('axis_debit_deep_2100', 'Axis Debit Deep - 2100 / Card - 5434'),
        ('axis_cc_nirav_1902', 'AXIS CC Nirav Thakkar-1902'),
        ('akasa_airline', 'Akasa Airline'),
        ('axis_nirav_2448_dc_9297', 'AXIS Nirav Thakkar 2448/ DC 9297'),
        ('hdfc_earth_cc_0952', 'HDFC The Earth CC - 0952'),
        ('hdfc_nirav_cc_5721', 'HDFC Nirav CC 5721'),
        ('hdfc_earth_cc_2873', 'HDFC The Earth CC - 2873'),
        ('earth_hdfc_cc_1554', 'The Earth HDFC CC- 1554'),
        ('ketan_axis_cc_ace_7929', 'Ketan Thakkar Axis CC Ace -7929/0735'),
        ('axis_dc_nirav_1446', 'Axis DC Nirav Thakkar-1446'),
        ('hdfc_nirav_cc_7122', 'HDFC Nirav CC-7122'),
        ('axis_debit_nirav_2448', 'AXIS Debit Nirav Thakkar -2448/5349/8819/7578'),
        ('hdfc_earth_cc_3026', 'HDFC EARTH CC-3026'),
        ('axis_cc_nirav_2281', 'Axis CC Nirav Thakkar-2281-7179/9743'),
        ('akbar_offshore', 'AKBAR OFFSHORE PVT LTD'),
        ('pcc_akbar_offshore', 'PCC AKBAR OFFSHORE PVT LTD'),
        ('hdfc_nirav_cc_1583', 'HDFC NIRAV CC - 1583'),
        ('hdfc_cc_deep_0943', 'HDFC CC Deep Thakkar-0943'),
        ('hdfc_cc_deep_6223', 'HDFC CC Deep Thakkar-6223'),
        ('icici_deep_cc_0003', 'ICICI DEEP CC-0003'),
        ('icici_ketan_cc_9005', 'ICICI Ketan CC-9005'),
    ], string='Mode of Payment')
    remarks = fields.Text(string='Remarks')
    confirmed_by = fields.Many2one('res.users', string='Confirmed By', tracking=True)

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
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.international.flight.booking') or _('New')
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
                'default_booking_type': 'international_flight',
                'default_international_flight_booking_id': self.id,
                'default_partner_id': self.billing_company_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.total_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})
