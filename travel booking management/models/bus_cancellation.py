# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class BusCancellation(models.Model):
    _name = 'travel.bus.cancellation'
    _description = 'Bus Cancellation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Cancellation Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    cancellation_date = fields.Date(string='Date of Cancellation', default=fields.Date.context_today,
                                    required=True, tracking=True)
    travel_date = fields.Date(string='Travel Date', tracking=True)
    booking_executive = fields.Many2one('res.users', string='Booking Executive',
                                        default=lambda self: self.env.user, tracking=True)
    passenger_names = fields.Text(string='Name of Passenger(s)')
    num_passengers = fields.Integer(string='Number of Passenger(s)', compute='_compute_num_passengers',
                                    store=True, readonly=False)
    employee_code = fields.Char(string='Employee Code', compute='_compute_employee_code',
                                store=True, readonly=False)
    billing_company_id = fields.Many2one('res.partner', string='Billing Company', tracking=True,
                                         domain=[('is_company', '=', True)],
                                         compute='_compute_billing_company', store=True, readonly=False)
    document_number = fields.Char(string='Doc. no./Req. by')
    origin_station = fields.Char(string='From - Origin')
    destination_station = fields.Char(string='To - Destination')
    pnr_number = fields.Char(string='PNR Number')
    total_amount = fields.Float(string='Total Amount', tracking=True)
    refund_amount = fields.Float(string='Refund Amount', tracking=True)
    mode_of_refund = fields.Selection([
        ('air_asia', 'Air Asia (India) Limited'),
        ('akasa_airline', 'Akasa Airline'),
        ('akbar_offshore', 'AKBAR OFFSHORE PVT LTD'),
        ('akbar_new', 'Akbar Online Booking Company Pvt Ltd - New'),
        ('akbar_old', 'Akbar Online Booking Company Pvt Ltd - Old'),
        ('aman_travels', 'Aman Travels Ltd'),
        ('interglobe', 'Interglobe Aviation Limited'),
        ('mmt_wallet', 'MMT Wallet'),
        ('pcc_akbar_offshore', 'PCC AKBAR OFFSHORE PVT LTD'),
        ('plus_wallet', 'Plus Wallet'),
        ('riya_offline', 'Riya Travels & Tours - Offline'),
        ('riya_online', 'Riya Travel & Tours - Online'),
        ('spicejet', 'Spicejet Limited'),
        ('axis_cc_vistara_deep_1236', 'Axis CC Vistara Deep Thakkar - 1236'),
        ('axis_debit_deep_2100', 'Axis Debit Deep - 2100 / Card - 5434'),
        ('hdfc_cc_deep_0943', 'HDFC CC Deep Thakkar-0943'),
        ('hdfc_cc_deep_6223', 'HDFC CC Deep Thakkar-6223'),
        ('ketan_axis_cc_ace_7929', 'Ketan Thakkar Axis CC Ace -7929/0735'),
        ('axis_cc_nirav_2281', 'Axis CC Nirav Thakkar-2281-7179/9743'),
        ('axis_debit_nirav_2448', 'AXIS Debit Nirav Thakkar -2448/5349/8819/7578'),
        ('hdfc_cc_nirav_9912', 'HDFC CC Nirav-9912 / 5100'),
        ('hdfc_nirav_cc_1583', 'HDFC NIRAV CC - 1583'),
        ('hdfc_nirav_cc_7122', 'HDFC Nirav CC-7122'),
        ('hdfc_earth_cc_3026', 'HDFC EARTH CC-3026'),
        ('hdfc_earth_cc_7209', 'HDFC The Earth CC - 7209/6804'),
        ('hdfc_earth_card_0481', 'HDFC The Earth Travel Card - 0481'),
        ('earth_hdfc_cc_1554', 'The Earth HDFC CC- 1554'),
        ('icici_deep_cc_0003', 'ICICI DEEP CC-0003'),
        ('icici_ketan_cc_9005', 'ICICI Ketan CC-9005'),
    ], string='Mode of Refund')
    remarks = fields.Text(string='Remarks')
    confirmed_by = fields.Many2one('res.users', string='Confirmed By', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('refunded', 'Refunded'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('passenger_names')
    def _compute_num_passengers(self):
        for rec in self:
            if rec.passenger_names:
                rec.num_passengers = len([l for l in rec.passenger_names.strip().splitlines() if l.strip()])
            else:
                rec.num_passengers = 0

    @api.depends('passenger_names')
    def _compute_employee_code(self):
        for rec in self:
            if rec.passenger_names:
                names = [n.strip() for n in rec.passenger_names.strip().splitlines() if n.strip()]
                codes = []
                for name in names:
                    records = self.env['travel.employee.code'].search([
                        ('employee_name', 'ilike', name),
                    ], limit=1)
                    if records:
                        codes.append(records[0].employee_code)
                rec.employee_code = ', '.join(codes) if codes else False
            else:
                rec.employee_code = False

    @api.depends('passenger_names')
    def _compute_billing_company(self):
        for rec in self:
            if rec.passenger_names:
                name = rec.passenger_names.strip().splitlines()[0].strip() if rec.passenger_names.strip() else False
                if name:
                    emp = self.env['travel.employee.code'].search([
                        ('employee_name', 'ilike', name),
                    ], limit=1)
                    if emp:
                        partner = self.env['res.partner'].search([
                            ('name', 'ilike', emp.entity),
                            ('is_company', '=', True),
                        ], limit=1)
                        if partner:
                            rec.billing_company_id = partner.id
                            continue
            rec.billing_company_id = rec.billing_company_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.bus.cancellation') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_refund(self):
        self.write({'state': 'refunded'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})
