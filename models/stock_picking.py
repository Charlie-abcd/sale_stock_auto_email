# -*- coding: utf-8 -*-

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        """Send the delivery email only when the transfer is actually done.

        ``button_validate`` often returns a wizard (backorder / immediate
        transfer) before the picking reaches state ``done``. Hooking
        ``_action_done`` guarantees the email is sent exactly once, after a
        successful validation — including wizard-based flows.
        """
        res = super()._action_done()
        self._send_auto_delivery_email()
        return res

    def _get_auto_email_partner(self):
        """Resolve a partner that has an email (delivery address often has none)."""
        self.ensure_one()
        if self.partner_id.email:
            return self.partner_id
        sale_partner = self.sale_id.partner_id if self.sale_id else self.env["res.partner"]
        if sale_partner.email:
            return sale_partner
        commercial = self.partner_id.commercial_partner_id
        if commercial.email:
            return commercial
        return self.partner_id

    def _send_auto_delivery_email(self):
        """Post in chatter + send email (same pattern as stock native confirmation)."""
        template = self.env.ref(
            "sale_stock_auto_email.mail_template_picking_done",
            raise_if_not_found=False,
        )
        if not template:
            return

        outgoing_done = self.filtered(
            lambda p: p.state == "done" and p.picking_type_code == "outgoing"
        )
        for picking in outgoing_done:
            partner = picking._get_auto_email_partner()
            if not partner.email:
                continue

            picking.with_context(force_send=True).message_post_with_source(
                template,
                email_layout_xmlid="mail.mail_notification_light",
                subtype_xmlid="mail.mt_comment",
                partner_ids=partner.ids,
            )
