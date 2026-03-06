# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class VisaCancellation(models.Model):
    _name = 'travel.visa.cancellation'
    _description = 'Visa Cancellation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Cancellation Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    cancellation_date = fields.Date(string='Cancellation Date', default=fields.Date.context_today,
                                    required=True, tracking=True)
    booking_executive = fields.Many2one('res.users', string='Booking Executive',
                                        default=lambda self: self.env.user, tracking=True)
    booking_type = fields.Selection([
        ('visa', 'Visa'),
        ('gvk_pranam', 'GVK Pranam Service'),
    ], string='Type of Booking', tracking=True)
    passenger_name = fields.Char(string='Passenger Name')
    passenger_names = fields.Text(string='Name of Passenger(s)')
    employee_code = fields.Char(string='Employee Code', compute='_compute_from_passenger',
                                store=True, readonly=False)
    billing_company_id = fields.Many2one('res.partner', string='Billing Company', tracking=True,
                                         domain=[('is_company', '=', True)],
                                         compute='_compute_from_passenger', store=True, readonly=False)
    document_number = fields.Char(string='Doc. no./Req. by')
    reference_number = fields.Char(string='Reference Number')
    description = fields.Text(string='Description')
    total_fare = fields.Float(string='Total Fare', tracking=True)
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
    def _compute_from_passenger(self):
        for rec in self:
            if rec.passenger_names:
                names = [n.strip() for n in rec.passenger_names.strip().splitlines() if n.strip()]
                codes = []
                first_emp = None
                for pname in names:
                    emp = self.env['travel.employee.code'].search([
                        ('employee_name', 'ilike', pname),
                    ], limit=1)
                    if emp:
                        codes.append(emp.employee_code)
                        if not first_emp:
                            first_emp = emp
                rec.employee_code = ', '.join(codes) if codes else False
                if first_emp:
                    entity = first_emp.entity
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
                    rec.billing_company_id = partner.id if partner else rec.billing_company_id
                else:
                    rec.billing_company_id = rec.billing_company_id
            else:
                rec.employee_code = False
                rec.billing_company_id = rec.billing_company_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.visa.cancellation') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_refund(self):
        self.write({'state': 'refunded'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})
