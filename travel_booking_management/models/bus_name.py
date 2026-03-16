# -*- coding: utf-8 -*-
from odoo import models, fields


class TravelBusName(models.Model):
    _name = 'travel.bus.name'
    _description = 'Bus Name Master'
    _order = 'name'

    name = fields.Char(string='Bus Name', required=True, index=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Bus name must be unique.'),
    ]
