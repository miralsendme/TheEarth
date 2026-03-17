# -*- coding: utf-8 -*-
from odoo import models, fields


class InternationalAirline(models.Model):
    _name = 'travel.international.airline'
    _description = 'International Airline'
    _order = 'name'

    name = fields.Char(string='Airline Name', required=True, index=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Airline name must be unique!'),
    ]
