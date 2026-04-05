{
    'name': 'Project Task State Field',
    'version': '1.0',
    'summary': 'Inherits project.task to add Submitted and Ongoing states',
    'author': 'Youssef Hussien',
    'category': 'Project',
    'license': 'LGPL-3',
    'depends': ['project'],
    'assets': {
        'web.assets_backend': [
            "/project_task_state/static/src/js/project_task_state_patch.js",
        ],
    },
    # "data": [
    #     "views/project_task_view.xml",
    # ],
    'installable': True,
    'application': False,
}
