# -*- coding: utf-8 -*-
from . import models
from . import wizard


def _hide_orphan_menus(env):
    """Hide top-level menus that have no XML ID (created via UI)."""
    menus_to_hide = env['ir.ui.menu'].search([
        ('parent_id', '=', False),
        ('name', 'ilike', 'Travel Booking'),
    ])
    menus_to_hide |= env['ir.ui.menu'].search([
        ('parent_id', '=', False),
        ('name', 'ilike', 'Travel Enquiry'),
    ])
    if menus_to_hide:
        menus_to_hide.write({'active': False})
