{'name':'estate',
'depends':['base', 'account'] , 
'data':['security/ir.model.access.csv' , 'views/estate_views.xml', 'views/estate_type_view.xml', 'views/estate_log_views.xml'],
# 'assets': {
#     'web.assets_backend': [
#         'estate/static/src/css/custom_style.css',
#         'estate/static/src/js/disable_sort.js',
#     ],
# },
'application' :True,
}