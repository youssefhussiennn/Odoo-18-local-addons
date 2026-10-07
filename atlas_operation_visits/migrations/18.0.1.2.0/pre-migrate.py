def migrate(cr, version):
    cr.execute("""
        UPDATE operation_visit
           SET state = 'scheduled'
         WHERE state IN ('draft', 'cancel')
    """)
