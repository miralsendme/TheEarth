# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PackageTourBooking(models.Model):
    _name = 'travel.package.tour.booking'
    _description = 'Package Tour Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    package_name = fields.Char(string='Package Name', required=True)
    tour_type = fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International'),
    ], string='Tour Type', default='domestic', required=True)
    destination = fields.Char(string='Destination', required=True)
    country_id = fields.Many2one('res.country', string='Country')
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    duration_days = fields.Integer(string='Duration (Days)', compute='_compute_duration', store=True)
    num_adults = fields.Integer(string='Adults', default=1, required=True)
    num_children = fields.Integer(string='Children', default=0)
    includes_hotel = fields.Boolean(string='Hotel Included', default=True)
    includes_flight = fields.Boolean(string='Flight Included', default=False)
    includes_meals = fields.Boolean(string='Meals Included', default=True)
    includes_sightseeing = fields.Boolean(string='Sightseeing Included', default=True)
    includes_transfer = fields.Boolean(string='Transfer Included', default=True)
    includes_insurance = fields.Boolean(string='Insurance Included', default=False)
    itinerary = fields.Text(string='Itinerary')
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

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                rec.duration_days = (rec.end_date - rec.start_date).days
            else:
                rec.duration_days = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('travel.package.tour.booking') or _('New')
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
                'default_booking_type': 'package_tour',
                'default_package_tour_booking_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_booking_ref': self.name,
                'default_booking_amount': self.total_amount,
            },
        }

    def action_draft(self):
        self.write({'state': 'draft'})
