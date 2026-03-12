# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ServiceInvoiceWizard(models.TransientModel):
    _name = 'travel.service.invoice.wizard'
    _description = 'Generate Consolidated Service Charge Invoice'

    partner_id = fields.Many2one(
        'res.partner', string='Billing Company', required=True,
        domain="[('customer_rank', '>', 0)]",
    )
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    so_line_ids = fields.Many2many(
        'sale.order.line', string='Service Charge Lines',
        compute='_compute_so_lines', store=False,
    )
    line_count = fields.Integer(compute='_compute_so_lines', store=False)

    @api.depends('partner_id', 'date_from', 'date_to')
    def _compute_so_lines(self):
        for wiz in self:
            lines = self.env['sale.order.line']
            if wiz.partner_id and wiz.date_from and wiz.date_to:
                sc_product = self.env['product.product'].search(
                    [('default_code', '=', 'product_service_charge')], limit=1)
                if sc_product:
                    lines = self.env['sale.order.line'].search([
                        ('order_id.partner_id', '=', wiz.partner_id.id),
                        ('order_id.date_order', '>=', wiz.date_from),
                        ('order_id.date_order', '<=', wiz.date_to),
                        ('product_id', '=', sc_product.id),
                        ('invoice_lines', '=', False),  # not yet invoiced
                    ])
            wiz.so_line_ids = lines
            wiz.line_count = len(lines)

    def action_preview(self):
        """Reopen the wizard to refresh the preview after changing filters."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generate_invoice(self):
        """Create a consolidated draft invoice from service charge SO lines."""
        self.ensure_one()
        if not self.partner_id or not self.date_from or not self.date_to:
            raise UserError(_("Please fill in all fields."))

        sc_product = self.env['product.product'].search(
            [('default_code', '=', 'product_service_charge')], limit=1)
        if not sc_product:
            raise UserError(_("Travel Service Charge product not found."))

        so_lines = self.env['sale.order.line'].search([
            ('order_id.partner_id', '=', self.partner_id.id),
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('product_id', '=', sc_product.id),
            ('invoice_lines', '=', False),
        ])
        if not so_lines:
            raise UserError(_(
                "No uninvoiced service charge lines found for %s in the selected date range."
            ) % self.partner_id.name)

        # Get CGST/SGST sale taxes
        company = self.env.company
        cgst = self.env['account.tax'].search([
            ('name', '=', 'CGST 9%'),
            ('company_id', '=', company.id),
            ('type_tax_use', '=', 'sale'),
        ], limit=1)
        sgst = self.env['account.tax'].search([
            ('name', '=', 'SGST 9%'),
            ('company_id', '=', company.id),
            ('type_tax_use', '=', 'sale'),
        ], limit=1)
        tax_ids = [t.id for t in (cgst | sgst) if t]

        # Build invoice lines — one per SO service charge line
        invoice_lines = []
        so_ids = set()
        for sol in so_lines:
            so = sol.order_id
            so_ids.add(so.id)
            invoice_lines.append((0, 0, {
                'product_id': sc_product.id,
                'name': sol.name or f"Service Charge - {so.name}",
                'quantity': sol.product_uom_qty,
                'price_unit': sol.price_unit,
                'tax_ids': [(6, 0, tax_ids)],
                'sale_line_ids': [(4, sol.id)],
            }))

        # Create draft invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'currency_id': company.currency_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': ', '.join(
                self.env['sale.order'].browse(list(so_ids)).mapped('name')
            ),
            'narration': (
                f"Consolidated Service Charge Invoice for "
                f"{self.partner_id.name} ({self.date_from} to {self.date_to})"
            ),
            'invoice_line_ids': invoice_lines,
        })

        # Copy annexure PDFs from all related SOs to this invoice
        for so_id in so_ids:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', so_id),
                ('name', 'like', 'Annexure_'),
                ('mimetype', '=', 'application/pdf'),
            ])
            for att in attachments:
                att.copy({
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                })

        # Open the created invoice
        return {
            'type': 'ir.actions.act_window',
            'name': _('Service Charge Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
