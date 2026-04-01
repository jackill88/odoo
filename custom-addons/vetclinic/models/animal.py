from odoo import models, fields, api


class AnimalCategory(models.Model):
    _name = 'animal.category'
    _description = 'Animal Category'

    name = fields.Char(required=True)
    description = fields.Text()


class AnimalType(models.Model):
    _name = 'animal.type'
    _description = 'Animal Type'

    name = fields.Char(required=True)
    description = fields.Text()
    animal_category_id = fields.Many2one(
        'animal.category',
        required=True
    )


class Animal(models.Model):
    _name = 'animal'
    _description = 'Animal'

    name = fields.Char(required=True)
    animal_type_id = fields.Many2one(
        'animal.type',
        required=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        ondelete='cascade'
    )
    birth_date = fields.Date()
    age = fields.Integer(
        compute='_compute_age',
        store=True
    )

    @api.depends('birth_date')
    def _compute_age(self):
        today = fields.Date.today()
        for record in self:
            if record.birth_date:
                record.age = (
                    today.year - record.birth_date.year
                    - ((today.month, today.day) <
                       (record.birth_date.month, record.birth_date.day))
                )
            else:
                record.age = 0