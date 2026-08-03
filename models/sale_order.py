# -*- coding: utf-8 -*-

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super().action_confirm()
        self.filtered(lambda o: o.state in ("sale", "done"))._send_auto_confirmation_email()
        return res

    def _get_auto_email_partner(self):
        """Prefer a partner that has an email (invoice contact as fallback)."""
        self.ensure_one()
        if self.partner_id.email:
            return self.partner_id
        if self.partner_invoice_id.email:
            return self.partner_invoice_id
        commercial = self.partner_id.commercial_partner_id
        if commercial.email:
            return commercial
        return self.partner_id

    def _send_auto_confirmation_email(self):
        """Post in chatter + send email (same pattern as sale native confirmation)."""
        template = self.env.ref(
            "sale_stock_auto_email.mail_template_sale_order_confirmed",
            raise_if_not_found=False,
        )
        if not template:
            return

        for order in self:
            partner = order._get_auto_email_partner()
            if not partner.email:
                continue

            order.with_context(force_send=True).message_post_with_source(
                template,
                email_layout_xmlid="mail.mail_notification_layout_with_responsible_signature",
                subtype_xmlid="mail.mt_comment",
                partner_ids=partner.ids,
            )
