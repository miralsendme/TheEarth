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
    employee_code = fields.Char(string='Employee Code')
    billing_company_id = fields.Many2one('res.partner', string='Billing Company', required=True, tracking=True)
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
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
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
