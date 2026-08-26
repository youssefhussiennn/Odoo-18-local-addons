"""
Renames the visible column headers on the Aged Receivable / Aged Payable
reports to match the new bucket boundaries.

This works by finding the two reports by name and renaming their dated
columns *in sequence order*, rather than relying on a guessed XML id -
so it's safe regardless of the exact ids used in your installed version.
It only touches columns whose current label looks like a day-range
(e.g. "1 - 30", "31 - 60"), so the "Not Due" and "Total" columns are
left alone.

New labels, applied in order: 1 - 30, 31 - 90, 91 - 150, 151 - 365, Older
"""
import re

NEW_LABELS = ['1 - 30', '31 - 90', '91 - 150', '151 - 365', 'Older']


def post_init_hook(env):
    reports = env['account.report'].search([
        ('name', 'in', ['Aged Receivable', 'Aged Payable']),
    ])
    if not reports:
        # Report names can be translated / renamed on some installs.
        raise ValueError(
            "Could not find 'Aged Receivable' / 'Aged Payable' reports by "
            "name. Open Settings > Technical > Reporting > Reports, find "
            "the two reports manually, note their exact `name` field, and "
            "update the search domain above."
        )

    for report in reports:
        # Columns whose label is a day-range look like "31 - 60" or "1-30".
        dated_columns = report.column_ids.filtered(
            lambda c: re.match(r'^\d+\s*-\s*\d+$', (c.name or '').strip())
        ).sorted('sequence')

        if len(dated_columns) != len(NEW_LABELS) - 1:  # NEW_LABELS includes "Older"
            raise ValueError(
                f"Report '{report.name}' has {len(dated_columns)} day-range "
                f"columns, expected {len(NEW_LABELS) - 1}. Column layout "
                "doesn't match what this module expects - check "
                "account.report.column records for this report manually "
                "before renaming, or send me the list and I'll adjust."
            )

        for column, label in zip(dated_columns, NEW_LABELS):
            column.name = label

        # Rename the "Older"/oldest column too, if it exists and isn't
        # already labelled correctly.
        older_column = report.column_ids.filtered(
            lambda c: (c.name or '').strip().lower() in ('older', 'total older')
        )
        older_column.name = 'Older'
