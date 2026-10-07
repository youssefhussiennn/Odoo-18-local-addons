from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Move the old single category/amount of each expense into a line."""
    cr.execute("""
        SELECT column_name FROM information_schema.columns
         WHERE table_name = 'operation_visit_expense'
           AND column_name IN ('category', 'amount', 'description')
    """)
    cols = {r[0] for r in cr.fetchall()}
    if not {'category', 'amount'} <= cols:
        return
    # Old columns are no longer fields; make sure they never block new inserts
    for col in cols:
        cr.execute(f'ALTER TABLE operation_visit_expense ALTER COLUMN {col} DROP NOT NULL')
    desc_col = 'description' if 'description' in cols else 'NULL'
    cr.execute(f"""
        SELECT e.id, e.category, e.amount, {desc_col}
          FROM operation_visit_expense e
         WHERE e.amount IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM operation_visit_expense_line l WHERE l.expense_id = e.id)
    """)
    rows = cr.fetchall()
    if not rows:
        return
    env = api.Environment(cr, SUPERUSER_ID, {'skip_approved_check': True})
    env['operation.visit.expense.line'].create([
        {
            'expense_id': exp_id,
            'category': category or 'other',
            'amount': amount if amount and amount > 0 else 0.01,
            'description': description or (False if category != 'other' else 'Migrated'),
        }
        for exp_id, category, amount, description in rows
    ])
