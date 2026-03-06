# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TrainBooking(models.Model):
    _name = 'travel.train.booking'
    _description = 'Train Booking'
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
    employee_code = fields.Char(string='Employee Code', compute='_compute_employee_code', store=True, readonly=False)
    billing_company_id = fields.Many2one('res.partner', string='Billing Company', tracking=True,
                                        domain=[('is_company', '=', True)],
                                        compute='_compute_billing_company', store=True, readonly=False)
    document_number = fields.Char(string='Doc. no./Req. by')
    origin_station = fields.Char(string='From - Origin', required=True)
    destination_station = fields.Char(string='To - Destination', required=True)
    travel_class = fields.Selection([
        ('sleeper', 'Sleeper'),
        ('ac_3tier', 'AC 3 Tier'),
        ('ac_2tier', 'AC 2 Tier'),
        ('ac_first', 'AC First Class'),
        ('chair_car', 'Chair Car'),
        ('executive', 'Executive'),
    ], string='Class', default='ac_3tier', required=True)
    quota = fields.Selection([
        ('general', 'General'),
        ('ladies', 'Ladies'),
        ('tatkal', 'Tatkal'),
        ('premium_tatkal', 'Premium Tatkal'),
        ('senior_citizen', 'Senior Citizen'),
        ('handicapped', 'Handicapped / Divyangjan'),
        ('defence', 'Defence'),
        ('foreign_tourist', 'Foreign Tourist'),
    ], string='Quota', default='general')
    pnr_number = fields.Char(string='PNR Number')
    travel_date = fields.Date(string='Travel Date', required=True, tracking=True)
    train_number = fields.Char(string='Train Number', required=True)
    total_amount = fields.Float(string='Total Fare', tracking=True)
    gst_amount = fields.Float(string='GST Amount')
    mode_of_payment = fields.Selection([
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
    ], string='Mode of Payment')
    booking_account = fields.Char(string='Booking Account')
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
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.train.booking') or _('New')
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
                'default_booking_type': 'train',
                'default_train_booking_id': self.id,
                'default_partner_id': self.billing_company_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.total_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})

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
                        entity = emp.entity
                        partner = self.env['res.partner'].search([
                            ('name', 'ilike', entity),
                            ('is_company', '=', True),
                        ], limit=1)
                        if not partner:
                            core = entity
                            for suffix in ['Private Limited', 'Pvt Ltd', 'Pvt. Ltd.', 'Pvt Ltd.', 'Ltd', 'Ltd.']:
                                core = core.replace(suffix, '').strip().rstrip(',').strip()
                            if core:
                                partner = self.env['res.partner'].search([
                                    ('name', 'ilike', core),
                                    ('is_company', '=', True),
                                ], limit=1)
                        if partner:
                            rec.billing_company_id = partner.id
                            continue
            rec.billing_company_id = rec.billing_company_id
