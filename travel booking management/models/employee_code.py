# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class TravelEmployeeCode(models.Model):
    _name = 'travel.employee.code'
    _description = 'Employee Code Directory'
    _order = 'employee_name asc'
    _rec_name = 'display_name_custom'

    entity = fields.Char(string='Entity / Company', required=True, index=True)
    employee_code = fields.Char(string='Employee Code', required=True, index=True)
    employee_name = fields.Char(string='Employee Name', index=True)
    display_name_custom = fields.Char(string='Display Name', compute='_compute_display_name_custom', store=True)

    @api.depends('employee_code', 'employee_name', 'entity')
    def _compute_display_name_custom(self):
        for rec in self:
            if rec.employee_name:
                rec.display_name_custom = f"{rec.employee_code} - {rec.employee_name} ({rec.entity})"
            else:
                rec.display_name_custom = f"{rec.employee_code} ({rec.entity})"
