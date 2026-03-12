# -*- coding: utf-8 -*-
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Mapping of mode_of_payment keys to vendor names for Purchase Orders
VENDOR_MAP = {
    'air_asia': 'Air Asia (India) Limited',
    'akasa_airline': 'Akasa Airline',
    'akbar_offshore': 'AKBAR OFFSHORE PVT LTD',
    'akbar_new': 'Akbar Online Booking Company Pvt Ltd',
    'akbar_old': 'Akbar Online Booking Company Pvt Ltd',
    'aman_travels': 'Aman Travels Ltd',
    'interglobe': 'Interglobe Aviation Limited',
    'mmt_wallet': 'MakeMyTrip',
    'pcc_akbar_offshore': 'PCC AKBAR OFFSHORE PVT LTD',
    'plus_wallet': 'Plus Wallet',
    'riya_offline': 'Riya Travels & Tours',
    'riya_online': 'Riya Travel & Tours',
    'spicejet': 'Spicejet Limited',
    # Credit card payments — vendor is The Earth itself (internal)
    'axis_cc_vistara_deep_1236': False,
    'axis_debit_deep_2100': False,
    'hdfc_cc_deep_0943': False,
    'hdfc_cc_deep_6223': False,
    'ketan_axis_cc_ace_7929': False,
    'axis_cc_nirav_2281': False,
    'axis_debit_nirav_2448': False,
    'hdfc_cc_nirav_9912': False,
    'hdfc_nirav_cc_1583': False,
    'hdfc_nirav_cc_7122': False,
    'hdfc_earth_cc_3026': False,
    'hdfc_earth_cc_7209': False,
    'hdfc_earth_card_0481': False,
    'earth_hdfc_cc_1554': False,
    'icici_deep_cc_0003': False,
    'icici_ketan_cc_9005': False,
}

# Hotel-specific service provider to vendor mapping
HOTEL_PROVIDER_MAP = {
    'aman_travels': 'Aman Travels Ltd',
    'makemytrip': 'MakeMyTrip',
    'treebo': 'Treebo',
    'goibibo': 'Goibibo',
    'airbnb': 'Airbnb',
    'meril_travel_desk': 'Meril Travel Desk',
    'travel_plus': 'Travel Plus',
    'other': False,
}


class TravelSalePurchaseMixin(models.AbstractModel):
    _name = 'travel.sale.purchase.mixin'
    _description = 'Mixin for auto-generating Draft SO and PO from bookings'

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True, copy=False)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True, copy=False)

    def _get_booking_description(self):
        """Override in each booking model to return a descriptive line name."""
        return self.name or 'Travel Booking'

    def _get_booking_type_label(self):
        """Override in each booking model to return the booking type label."""
        return 'Travel'

    def _get_ticket_amount(self):
        """Return the ticket/fare amount (non-taxable). Override if field name differs."""
        if hasattr(self, 'total_amount') and self.total_amount:
            return self.total_amount
        if hasattr(self, 'amount') and self.amount:
            return self.amount
        return 0.0

    def _get_service_charge_amount(self):
        """Return the service charge amount (taxable). Override if not applicable."""
        if hasattr(self, 'service_charge') and self.service_charge:
            return self.service_charge
        return 0.0

    def _get_customer_partner(self):
        """Return the customer (billing company) for the SO."""
        if hasattr(self, 'billing_company_id') and self.billing_company_id:
            return self.billing_company_id
        return False

    def _get_vendor_partner(self):
        """Return or create the vendor partner for the PO."""
        vendor_name = False

        # For hotel bookings, prefer booking_service_provider
        if hasattr(self, 'booking_service_provider') and self.booking_service_provider:
            vendor_name = HOTEL_PROVIDER_MAP.get(self.booking_service_provider)

        # Fall back to mode_of_payment
        if not vendor_name and hasattr(self, 'mode_of_payment') and self.mode_of_payment:
            vendor_name = VENDOR_MAP.get(self.mode_of_payment)

        if not vendor_name:
            return False

        # Find or create vendor partner
        partner = self.env['res.partner'].search([
            ('name', '=ilike', vendor_name),
            ('supplier_rank', '>', 0),
        ], limit=1)
        if not partner:
            partner = self.env['res.partner'].search([
                ('name', '=ilike', vendor_name),
            ], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': vendor_name,
                'supplier_rank': 1,
                'is_company': True,
            })
        elif not partner.supplier_rank:
            partner.sudo().write({'supplier_rank': partner.supplier_rank + 1})
        return partner

    def _get_passenger_info(self):
        """Return passenger/guest names for SO line description."""
        for field in ('passenger_names', 'guest_names', 'passenger_name'):
            if hasattr(self, field):
                val = getattr(self, field)
                if val:
                    return val.strip()
        return ''

    def _get_passenger_list(self):
        """Return list of passenger names for annexure."""
        for field in ('passenger_names', 'guest_names'):
            if hasattr(self, field):
                val = getattr(self, field)
                if val:
                    return [n.strip() for n in val.strip().splitlines() if n.strip()]
        if hasattr(self, 'passenger_name') and self.passenger_name:
            return [self.passenger_name.strip()]
        return []

    def _get_pnr_info(self):
        """Return PNR/ticket number if available."""
        for field in ('pnr_number', 'ticket_number', 'reference_number'):
            if hasattr(self, field):
                val = getattr(self, field)
                if val:
                    return val.strip()
        return ''

    def _get_travel_dates_info(self):
        """Return a list of dicts with travel date info for annexure. Override per model."""
        dates = []
        # Flight-style: onward + return
        if hasattr(self, 'travel_date_onward') and self.travel_date_onward:
            dates.append({'label': 'Onward', 'date': self.travel_date_onward})
            if hasattr(self, 'return_date') and self.return_date:
                dates.append({'label': 'Return', 'date': self.return_date})
        # Train/Bus: single travel_date
        elif hasattr(self, 'travel_date') and self.travel_date:
            dates.append({'label': 'Travel Date', 'date': self.travel_date})
        # Hotel/Event: checkin/checkout
        elif hasattr(self, 'checkin_date') and self.checkin_date:
            dates.append({'label': 'Check-in', 'date': self.checkin_date})
            if hasattr(self, 'checkout_date') and self.checkout_date:
                dates.append({'label': 'Check-out', 'date': self.checkout_date})
        # Car: pickup/drop
        elif hasattr(self, 'pickup_date') and self.pickup_date:
            dates.append({'label': 'Pickup', 'date': self.pickup_date})
            if hasattr(self, 'drop_date') and self.drop_date:
                dates.append({'label': 'Drop', 'date': self.drop_date})
        # Booking date as fallback
        if not dates and hasattr(self, 'booking_date') and self.booking_date:
            dates.append({'label': 'Booking Date', 'date': self.booking_date})
        return dates

    def _get_route_info(self):
        """Return origin-destination info if available."""
        if hasattr(self, 'origin_city') and self.origin_city:
            route = self.origin_city
            if hasattr(self, 'destination_city') and self.destination_city:
                route += ' → ' + self.destination_city
            return route
        if hasattr(self, 'origin_station') and self.origin_station:
            route = self.origin_station
            if hasattr(self, 'destination_station') and self.destination_station:
                route += ' → ' + self.destination_station
            return route
        if hasattr(self, 'pickup_location') and self.pickup_location:
            route = self.pickup_location
            if hasattr(self, 'drop_location') and self.drop_location:
                route += ' → ' + self.drop_location
            return route
        if hasattr(self, 'location') and self.location:
            return self.location
        return ''

    def _get_or_create_product(self, xmlid, name, product_type='service'):
        """Get or create a product by xmlid for SO/PO lines."""
        product = self.env.ref(f'travel_booking_management.{xmlid}', raise_if_not_found=False)
        if not product:
            product = self.env['product.product'].search([('default_code', '=', xmlid)], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'name': name,
                'default_code': xmlid,
                'type': product_type,
                'sale_ok': True,
                'purchase_ok': True,
                'taxes_id': [(5, 0, 0)],
                'supplier_taxes_id': [(5, 0, 0)],
            })
        return product

    def _get_fare_product(self):
        return self._get_or_create_product('product_travel_fare', 'Travel Fare Reimbursement')

    def _get_service_charge_product(self):
        return self._get_or_create_product('product_service_charge', 'Travel Service Charge')

    def _get_or_create_gst_taxes(self):
        """Get or create CGST 9% and SGST 9% taxes for service charge."""
        company = self.env.company
        cgst = self.env['account.tax'].search([
            ('name', '=', 'CGST 9%'),
            ('company_id', '=', company.id),
            ('type_tax_use', '=', 'sale'),
        ], limit=1)
        if not cgst:
            cgst = self.env['account.tax'].create({
                'name': 'CGST 9%',
                'type_tax_use': 'sale',
                'amount_type': 'percent',
                'amount': 9.0,
                'company_id': company.id,
                'description': 'CGST @ 9%',
            })
        sgst = self.env['account.tax'].search([
            ('name', '=', 'SGST 9%'),
            ('company_id', '=', company.id),
            ('type_tax_use', '=', 'sale'),
        ], limit=1)
        if not sgst:
            sgst = self.env['account.tax'].create({
                'name': 'SGST 9%',
                'type_tax_use': 'sale',
                'amount_type': 'percent',
                'amount': 9.0,
                'company_id': company.id,
                'description': 'SGST @ 9%',
            })
        return cgst, sgst

    def _get_or_create_purchase_gst_taxes(self):
        """Get or create CGST 9% and SGST 9% taxes for purchase."""
        company = self.env.company
        cgst = self.env['account.tax'].search([
            ('name', '=', 'CGST 9%'),
            ('company_id', '=', company.id),
            ('type_tax_use', '=', 'purchase'),
        ], limit=1)
        if not cgst:
            cgst = self.env['account.tax'].create({
                'name': 'CGST 9%',
                'type_tax_use': 'purchase',
                'amount_type': 'percent',
                'amount': 9.0,
                'company_id': company.id,
                'description': 'CGST @ 9%',
            })
        sgst = self.env['account.tax'].search([
            ('name', '=', 'SGST 9%'),
            ('company_id', '=', company.id),
            ('type_tax_use', '=', 'purchase'),
        ], limit=1)
        if not sgst:
            sgst = self.env['account.tax'].create({
                'name': 'SGST 9%',
                'type_tax_use': 'purchase',
                'amount_type': 'percent',
                'amount': 9.0,
                'company_id': company.id,
                'description': 'SGST @ 9%',
            })
        return cgst, sgst

    def _create_draft_sale_order(self):
        """Create a Draft Sales Order with ticket cost + service charge lines."""
        self.ensure_one()
        customer = self._get_customer_partner()
        if not customer:
            return False

        ticket_amount = self._get_ticket_amount()
        sc_amount = self._get_service_charge_amount()
        if not ticket_amount and not sc_amount:
            return False

        booking_type = self._get_booking_type_label()
        passenger = self._get_passenger_info()
        pnr = self._get_pnr_info()

        # Build description lines
        ticket_desc = f"{booking_type} Fare Reimbursement As Per Attached Annex."
        if pnr:
            ticket_desc += f"\nPNR/Ref: {pnr}"
        if passenger:
            ticket_desc += f"\nPassenger(s): {passenger}"

        sc_desc = f"Service Charges for {booking_type} Booking"
        if pnr:
            sc_desc += f"\nPNR/Ref: {pnr}"
        if passenger:
            sc_desc += f"\nPassenger(s): {passenger}"

        company_currency = self.env.company.currency_id.id
        fare_product = self._get_fare_product()
        sc_product = self._get_service_charge_product()

        order_lines = []
        # Line 1: Ticket cost — non-taxable
        if ticket_amount:
            order_lines.append((0, 0, {
                'product_id': fare_product.id,
                'name': ticket_desc,
                'product_uom_qty': 1,
                'price_unit': ticket_amount,
                'tax_id': [(5, 0, 0)],  # No tax
                'currency_id': company_currency,
            }))

        # Line 2: Service charge — taxable (CGST + SGST)
        if sc_amount:
            cgst, sgst = self._get_or_create_gst_taxes()
            order_lines.append((0, 0, {
                'product_id': sc_product.id,
                'name': sc_desc,
                'product_uom_qty': 1,
                'price_unit': sc_amount,
                'tax_id': [(6, 0, [cgst.id, sgst.id])],
                'currency_id': company_currency,
            }))

        so = self.env['sale.order'].create({
            'partner_id': customer.id,
            'currency_id': company_currency,
            'origin': self.name,
            'note': f"Auto-generated from {booking_type} booking {self.name}",
            'order_line': order_lines,
        })
        self.sale_order_id = so.id
        return so

    def _create_draft_purchase_order(self):
        """Create a Draft Purchase Order mapped to the vendor."""
        self.ensure_one()
        vendor = self._get_vendor_partner()
        if not vendor:
            return False

        ticket_amount = self._get_ticket_amount()
        if not ticket_amount:
            return False

        booking_type = self._get_booking_type_label()
        passenger = self._get_passenger_info()
        pnr = self._get_pnr_info()

        line_desc = f"{booking_type} - {self.name}"
        if pnr:
            line_desc += f" | PNR: {pnr}"
        if passenger:
            line_desc += f" | {passenger}"

        company_currency = self.env.company.currency_id.id
        fare_product = self._get_fare_product()
        po = self.env['purchase.order'].create({
            'partner_id': vendor.id,
            'currency_id': company_currency,
            'origin': self.name,
            'notes': f"Auto-generated from {booking_type} booking {self.name}",
            'order_line': [(0, 0, {
                'product_id': fare_product.id,
                'name': line_desc,
                'product_qty': 1,
                'price_unit': ticket_amount,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'currency_id': company_currency,
                'date_planned': fields.Datetime.now(),
                'taxes_id': [(5, 0, 0)],  # No tax on purchase cost
            })],
        })
        self.purchase_order_id = po.id
        return po

    def _generate_sale_purchase_orders(self):
        """Called from action_confirm to generate both SO and PO."""
        for rec in self:
            if not rec.sale_order_id:
                so = rec._create_draft_sale_order()
                if so:
                    rec._attach_annexure_to_so(so)
            if not rec.purchase_order_id:
                rec._create_draft_purchase_order()

    def _attach_annexure_to_so(self, so):
        """Generate detailed Excel annexures (service charge + fare) and attach to SO."""
        self.ensure_one()
        try:
            import base64
            import io
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        except ImportError:
            return

        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin'),
        )
        header_font = Font(bold=True, color='FFFFFF', size=9)
        header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
        header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
        bold_font = Font(bold=True, size=10)

        booking_type = self._get_booking_type_label()
        customer = self._get_customer_partner()
        customer_name = customer.name if customer else ''

        # Passenger info
        pax = self._get_passenger_info()
        pax_list = self._get_passenger_list()
        num_pax = len(pax_list) if pax_list else 1
        emp_code = getattr(self, 'employee_code', '') or ''
        doc_no = getattr(self, 'document_number', '') or ''
        origin = self._get_route_info().split(' → ')[0] if ' → ' in self._get_route_info() else self._get_route_info()
        dest = self._get_route_info().split(' → ')[1] if ' → ' in self._get_route_info() else ''
        pnr = self._get_pnr_info()
        ticket = getattr(self, 'ticket_number', '') or ''
        flight_no = getattr(self, 'flight_number', '') or ''
        flight_ret = getattr(self, 'flight_number_return', '') or ''
        travel_class = ''
        if hasattr(self, 'travel_class') and self.travel_class:
            travel_class = dict(self._fields['travel_class'].selection).get(self.travel_class, '')
        airline = ''
        if hasattr(self, 'airline') and self.airline:
            field = self._fields.get('airline')
            if field and field.type == 'selection':
                airline = dict(field.selection).get(self.airline, self.airline)
            else:
                airline = self.airline
        trip_type = ''
        if hasattr(self, 'trip_type') and self.trip_type:
            trip_type = dict(self._fields['trip_type'].selection).get(self.trip_type, '')

        dates = self._get_travel_dates_info()
        travel_date = str(dates[0]['date']) if dates else ''
        return_date = str(dates[1]['date']) if len(dates) > 1 else ''

        total_fare = self._get_ticket_amount()
        sc = self._get_service_charge_amount()

        # --- Service Charge Annexure ---
        if sc > 0:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = 'Service Charge'
            ws.cell(row=1, column=1, value='THE EARTH').font = Font(bold=True, size=14)
            company = self.env.company
            ws.cell(row=2, column=1, value=f'GSTIN: {company.vat or ""}').font = Font(size=9)
            ws.cell(row=3, column=1, value=f'ANNEXURE - SERVICE CHARGE - {booking_type.upper()} BOOKING').font = Font(bold=True, size=11)
            ws.cell(row=4, column=1, value=f'To: {customer_name}').font = bold_font
            ws.cell(row=4, column=8, value=str(self.booking_date) if hasattr(self, 'booking_date') and self.booking_date else '').font = Font(size=9)

            row = 6
            headers = ['SR No.', 'Booking Date', 'No of', 'Passenger(s) Name', 'Emp. Code',
                        'Doc. No.', 'From Origin', 'To Destination', 'Travel Type',
                        'Travel Date', 'Return Date', 'PNR / Ticket', 'PNR No.',
                        'Flight No.', 'Class', 'Airline',
                        'Service Charge', 'CGST 9%', 'SGST 9%', 'IGST', 'Total ₹', 'Remark']
            for col, h in enumerate(headers, 1):
                cell = ws.cell(row=row, column=col, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align
                cell.border = thin_border

            row += 1
            cgst_amt = round(sc * 0.09, 2)
            sgst_amt = round(sc * 0.09, 2)
            line_total = round(sc + cgst_amt + sgst_amt, 2)
            vals = [1, str(self.booking_date) if hasattr(self, 'booking_date') and self.booking_date else '',
                    num_pax, pax, emp_code, doc_no, origin, dest, trip_type,
                    travel_date, return_date, ticket or pnr, pnr,
                    flight_no, travel_class, airline,
                    sc, cgst_amt, sgst_amt, 0, line_total, '']
            for col, v in enumerate(vals, 1):
                cell = ws.cell(row=row, column=col, value=v)
                cell.border = thin_border

            row += 1
            ws.cell(row=row, column=3, value='Grand Total').font = bold_font
            for col, val in [(17, sc), (18, cgst_amt), (19, sgst_amt), (20, 0), (21, line_total)]:
                cell = ws.cell(row=row, column=col, value=val)
                cell.font = bold_font
                cell.border = thin_border

            for c in ws.columns:
                ml = max(len(str(cell.value or '')) for cell in c)
                ws.column_dimensions[c[0].column_letter].width = min(ml + 2, 30)

            fp = io.BytesIO()
            wb.save(fp)
            fp.seek(0)
            self.env['ir.attachment'].create({
                'name': f"Annexure_ServiceCharge_{self.name}.xlsx",
                'type': 'binary',
                'datas': base64.b64encode(fp.read()),
                'res_model': 'sale.order',
                'res_id': so.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })
            fp.close()

        # --- Fare Charge Annexure ---
        if total_fare > 0:
            wb2 = openpyxl.Workbook()
            ws2 = wb2.active
            ws2.title = 'Fare Charge'
            ws2.cell(row=1, column=1, value='THE EARTH').font = Font(bold=True, size=14)
            ws2.cell(row=2, column=1, value=f'GSTIN: {self.env.company.vat or ""}').font = Font(size=9)
            ws2.cell(row=3, column=1, value=f'ANNEXURE - FARE CHARGE - {booking_type.upper()} BOOKING').font = Font(bold=True, size=11)
            ws2.cell(row=4, column=1, value=f'To: {customer_name}').font = bold_font

            row = 6
            headers2 = ['SR No.', 'Booking Date', 'No of Pax.', 'Passenger(s) Name', 'Emp. Code',
                         'Doc. No.', 'From Origin', 'To Destination', 'Travel Type',
                         'Travel Date', 'Return Date', 'PNR / Ticket', 'PNR No.',
                         'Flight No. Onward', 'Flight No. Return', 'Class', 'Airline',
                         'Total Fare', 'Cancel Cost', 'Refund Amount', 'Inv No.', 'Remark']
            for col, h in enumerate(headers2, 1):
                cell = ws2.cell(row=row, column=col, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align
                cell.border = thin_border

            row += 1
            vals2 = [1, str(self.booking_date) if hasattr(self, 'booking_date') and self.booking_date else '',
                     num_pax, pax, emp_code, doc_no, origin, dest, trip_type,
                     travel_date, return_date, ticket or pnr, pnr,
                     flight_no, flight_ret, travel_class, airline,
                     total_fare, 0, 0, so.name or '', '']
            for col, v in enumerate(vals2, 1):
                cell = ws2.cell(row=row, column=col, value=v)
                cell.border = thin_border

            row += 1
            ws2.cell(row=row, column=3, value='Grand Total').font = bold_font
            ws2.cell(row=row, column=18, value=total_fare).font = bold_font
            ws2.cell(row=row, column=18).border = thin_border

            for c in ws2.columns:
                ml = max(len(str(cell.value or '')) for cell in c)
                ws2.column_dimensions[c[0].column_letter].width = min(ml + 2, 30)

            fp2 = io.BytesIO()
            wb2.save(fp2)
            fp2.seek(0)
            self.env['ir.attachment'].create({
                'name': f"Annexure_FareCharge_{self.name}.xlsx",
                'type': 'binary',
                'datas': base64.b64encode(fp2.read()),
                'res_model': 'sale.order',
                'res_id': so.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })
            fp2.close()

    def action_view_sale_order(self):
        """Open the linked Sales Order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_purchase_order(self):
        """Open the linked Purchase Order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
