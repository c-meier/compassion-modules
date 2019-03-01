# -*- coding: utf-8 -*-45.00
# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CrmClaim(models.Model):
    _inherit = "crm.claim"
    _description = "Request"

    date = fields.Datetime(string='Date', readonly=True, index=False)
    name = fields.Char(string='Subject')
    code = fields.Char(string='Number')
    claim_type = fields.Many2one(string='Type')
    user_id = fields.Many2one(string='Assign to')

    @api.multi
    def action_reply(self):
        """
        This function opens a window to compose an email, with the default
        template message loaded by default"""
        self.ensure_one()

        template_id = self.claim_type.template_id.id
        ctx = {
            'default_model': 'crm.claim',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': ctx,
        }

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------
    @api.model
    def message_new(self, msg, custom_values=None):
        """ Use the html of the mail's body instead of html converted in text
        """
        if custom_values is None:
            custom_values = {}
        custom_values.update({'description': msg.get('body')})
        return super(CrmClaim, self).message_new(msg, custom_values)

    @api.multi
    def message_update(self, msg_dict, update_vals=None):
        """Change the stage to "Waiting on support" when the customer write a
           new mail on the thread
        """
        result = super(CrmClaim, self).message_update(msg_dict, update_vals)
        for request in self:
            request.stage_id = self.env[
                'ir.model.data'].get_object_reference(
                'crm_request', 'stage_wait_support')[1]
        return result

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, **kwargs):
        """Change the stage to "Waiting on customer" when the employee answer
           to the supporter
        """
        result = super(CrmClaim, self).message_post(**kwargs)

        if 'mail_server_id' in kwargs:
            for request in self:
                ir_data = self.env['ir.model.data']
                request.stage_id = ir_data.get_object_reference(
                    'crm_request', 'stage_wait_customer')[1]

        return result
