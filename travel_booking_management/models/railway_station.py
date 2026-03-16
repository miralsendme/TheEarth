# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RailwayStation(models.Model):
    _name = 'travel.railway.station'
    _description = 'Indian Railway Station'
    _order = 'name'

    name = fields.Char(string='Station Name', required=True, index=True)
    code = fields.Char(string='Station Code', required=True, index=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Station code must be unique.'),
    ]

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.name} ({rec.code})" if rec.code else rec.name
            result.append((rec.id, display))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            records = self.search([
                '|',
                ('name', operator, name),
                ('code', operator, name),
            ] + args, limit=limit)
        else:
            records = self.search(args, limit=limit)
        return records.name_get()
