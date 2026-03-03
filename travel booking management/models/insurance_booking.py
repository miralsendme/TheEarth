# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InsuranceBooking(models.Model):
    _name = 'travel.insurance.booking'
    _description = 'Travel Insurance Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    insurance_provider = fields.Char(string='Insurance Provider', required=True)
    policy_number = fields.Char(string='Policy Number')
    insurance_type = fields.Selection([
        ('travel_medical', 'Travel Medical'),
        ('trip_cancellation', 'Trip Cancellation'),
        ('baggage_loss', 'Baggage Loss'),
        ('flight_delay', 'Flight Delay'),
        ('comprehensive', 'Comprehensive'),
    ], string='Insurance Type', default='comprehensive', required=True)
    coverage_amount = fields.Float(string='Coverage Amount')
    destination_country_id = fields.Many2one('res.country', string='Destination Country')
    start_date = fields.Date(string='Coverage Start Date', required=True, tracking=True)
    end_date = fields.Date(string='Coverage End Date', required=True, tracking=True)
    num_travellers = fields.Integer(string='Number of Travellers', default=1, required=True)
    nominee_name = fields.Char(string='Nominee Name')
    nominee_relation = fields.Char(string='Nominee Relation')
    premium_amount = fields.Float(string='Premium Amount', tracking=True)
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.insurance.booking') or _('New')
        return super().create(vals_list)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date >= rec.end_date:
                raise ValidationError(_('End date must be after start date.'))

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
                'default_booking_type': 'insurance',
                'default_insurance_booking_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.premium_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})
