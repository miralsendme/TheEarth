# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMoveTravel(models.Model):
    _inherit = 'account.move'

    is_travel_service_invoice = fields.Boolean(
        compute='_compute_travel_doc_type', store=False)
    is_travel_debit_note = fields.Boolean(
        compute='_compute_travel_doc_type', store=False)
    is_travel_credit_note = fields.Boolean(
        compute='_compute_travel_doc_type', store=False)
    is_cancellation_service_invoice = fields.Boolean(
        string='Cancellation Service Invoice', default=False,
        help='Set when this invoice is for cancellation service charges (uses CN labels)')

    @api.depends('invoice_line_ids.product_id', 'move_type', 'is_cancellation_service_invoice')
    def _compute_travel_doc_type(self):
        for move in self:
            product_codes = move.invoice_line_ids.mapped(
                'product_id.default_code')
            has_sc = 'product_service_charge' in product_codes
            has_fare = 'product_travel_fare' in product_codes
            # Tax Invoice: service charge on booking (out_invoice, not cancellation)
            move.is_travel_service_invoice = (
                has_sc and move.move_type == 'out_invoice'
                and not move.is_cancellation_service_invoice)
            # Debit Note: fare on booking (out_invoice, not cancellation)
            move.is_travel_debit_note = (
                has_fare and move.move_type == 'out_invoice')
            # Credit Note: cancellation service charge (out_invoice with CN flag)
            #   OR fare refund (out_refund)
            move.is_travel_credit_note = (
                move.is_cancellation_service_invoice
                or (has_fare and move.move_type == 'out_refund'))

    def action_print_tax_invoice(self):
        return self.env.ref(
            'travel_booking_management.action_report_tax_invoice'
        ).report_action(self)

    def action_print_debit_note(self):
        return self.env.ref(
            'travel_booking_management.action_report_debit_note'
        ).report_action(self)

    def action_print_credit_note(self):
        return self.env.ref(
            'travel_booking_management.action_report_credit_note'
        ).report_action(self)


class SaleOrderTravelAnnexure(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Copy travel annexure attachments from SO to created invoices."""
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        for move in moves:
            # Find all SOs linked to this invoice
            so_ids = move.invoice_line_ids.mapped(
                'sale_line_ids.order_id').ids
            for so_id in so_ids:
                annexures = self.env['ir.attachment'].search([
                    ('res_model', '=', 'sale.order'),
                    ('res_id', '=', so_id),
                    ('name', 'like', 'Annexure_'),
                ])
                for att in annexures:
                    # Don't duplicate if already attached
                    existing = self.env['ir.attachment'].search([
                        ('res_model', '=', 'account.move'),
                        ('res_id', '=', move.id),
                        ('name', '=', att.name),
                    ], limit=1)
                    if not existing:
                        att.copy({
                            'res_model': 'account.move',
                            'res_id': move.id,
                        })
        return moves
