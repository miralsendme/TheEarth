# -*- coding: utf-8 -*-
from odoo import models, fields


class HotelCity(models.Model):
    _name = 'travel.hotel.city'
    _description = 'Hotel City'
    _order = 'name'

    name = fields.Char(string='City Name', required=True, index=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'City name must be unique!'),
    ]
