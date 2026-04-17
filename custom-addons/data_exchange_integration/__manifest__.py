{
    "name": "Data Exchange Integration",
    'category': 'Products/Data Exchange',
    "version": "1.0",
    "depends": [ "base", "product"],
    "data": [
        "data/cron.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/data_import_job_views.xml",
        "views/sftp_config_views.xml",
        "views/s3_config_views.xml",
        "views/menu.xml",
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
    'author': 'Yaroslav Tkachenko'
}