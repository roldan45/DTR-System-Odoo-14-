# -*- coding: utf-8 -*-
{
    'name': "HR & Payroll",

    'summary': """
        HR & Payroll""",

    'description': """
        HR & Payroll System
    """,

    'author': "Me",
    'website': "https://mec.com.ph",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Services',
    'version': '1.0.0',
    'sequence': -700,

    'depends': [
        'base',
        'mail',
        'resource',
        'web',
    ],

    'data': [
        'data/ir_cron.xml',
        
        #security
        'security/security.xml',
        'security/ir.model.access.csv',
        
        #wizard
        'wizard/import_bio.xml',
        'wizard/create_position_wizard.xml',
        'wizard/set_leave_days.xml',
        'wizard/print_late_summary.xml',
        'wizard/fixer.xml',
        
        #report
        'report/attendance_department_report.xml',
        'report/late_summary_report.xml',
        'report/payroll_dtr_report.xml',
        'report/report_view.xml',
        
        'report/report.xml',
        
        #views
        'views/assets.xml',
        'views/base_employee.xml',
        'views/masterdata.xml',
        'views/biometric_log.xml',
        'views/department_attendance.xml',
        'views/employee_attendance.xml',
        'views/employee_attendance_data.xml',
        'views/payroll_dtr.xml',
        'views/payslip.xml',
        'views/attendance.xml',
        'views/late_data.xml',
        'views/dtr_timeoff.xml',
        'views/dtr_timeoff_data.xml',
        'views/events.xml',
        # 'views/web_templates.xml',
        
        'views/menu_items.xml',
    ],
    
    'qweb': [
        'static/src/xml/progress_bar.xml',
        # 'static/src/xml/timepicker.xml',
    ],

    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True, 
}
