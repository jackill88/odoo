from odoo import models, fields


class AnimalExamination(models.Model):
    _name = 'animal.examination'
    _description = 'Animal Examination'

    date = fields.Date()
    animal_id = fields.Many2one(
        'animal',
        required=True,
        ondelete='cascade'
    )
    examination_file_ids = fields.One2many(
        'animal.examination.file',
        'animal_examination_id',
        string='Files'
    )


class AnimalExaminationFile(models.Model):
    _name = 'animal.examination.file'
    _description = 'Animal Examination File'

    file = fields.Binary()
    animal_examination_id = fields.Many2one(
        'animal.examination',
        ondelete='cascade'
    )