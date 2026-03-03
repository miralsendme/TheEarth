# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VisaBooking(models.Model):
    _name = 'travel.visa.booking'
    _description = 'Visa Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    destination_country_id = fields.Many2one('res.country', string='Destination Country', required=True)
    visa_type = fields.Selection([
        ('tourist', 'Tourist'),
        ('business', 'Business'),
        ('transit', 'Transit'),
        ('student', 'Student'),
        ('work', 'Work'),
        ('medical', 'Medical'),
    ], string='Visa Type', default='tourist', required=True)
    passport_number = fields.Char(string='Passport Number', required=True)
    passport_expiry = fields.Date(string='Passport Expiry Date', required=True)
    application_date = fields.Date(string='Application Date', required=True, tracking=True)
    travel_date = fields.Date(string='Intended Travel Date', required=True)
    return_date = fields.Date(string='Intended Return Date')
    duration_of_stay = fields.Integer(string='Duration of Stay (Days)')
    embassy_appointment_date = fields.Datetime(string='Embassy Appointment')
    processing_time = fields.Char(string='Processing Time')
    service_charge = fields.Float(string='Service Charge', tracking=True)
    visa_fee = fields.Float(string='Visa Fee')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    cancellation_id = fields.Many2one('travel.booking.cancellation', string='Cancellation', readonly=True)

    @api.depends('service_charge', 'visa_fee')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = rec.service_charge + rec.visa_fee

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.visa.booking') or _('New')
        return super().create(vals_list)

    @api.constrains('travel_date', 'return_date')
    def _check_dates(self):
        for rec in self:
            if rec.travel_date and rec.return_date and rec.travel_date >= rec.return_date:
                raise ValidationError(_('Return date must be after travel date.'))

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_processing(self):
        self.write({'state': 'processing'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Booking'),
            'res_model': 'travel.booking.cancellation',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_booking_type': 'visa',
                'default_visa_booking_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.total_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})
