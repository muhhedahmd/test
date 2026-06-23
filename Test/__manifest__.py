{
    'name': 'Test',
    'license': 'LGPL-3',
    'author': 'Abdalrhman Salah',
    'category': '',
    'version': '19.0.1.0.0',
    'depends': ['base', 'account'],
    'data': [
        "security/ir.model.access.csv",  # لازم الصلاحيات تقرأ الأول هنا
        "views/accounting_view.xml",
    ],
    'application': True,
}