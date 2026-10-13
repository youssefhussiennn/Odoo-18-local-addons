# European Group Control Tower (Odoo 18)

Odoo 18 port of the *European Group | Control Tower* React app (Purchase Orders -> Shipments -> Tracking ->
Payments -> Documents -> Customs -> Warehouse -> Reports). The UI is the original React 18 app, unchanged in
look and behaviour, embedded in Odoo as a client action.

## Install
1. Copy the `european_group_control_tower` folder into an Odoo 18 addons path.
2. Apps -> Update Apps List -> install **European Group Control Tower**.
3. Give users the group *Control Tower / User* (or *Manager*) under Settings -> Users.
   Administrators are Managers automatically.
4. Open the **Control Tower** app. Managers can load the original Excel data from Settings (Load original Excel data).

No build step is needed to deploy (including Odoo.sh): the compiled bundle is committed in `static/dist/`.

## What changed compared with the Netlify/React version
| Before | Now |
| --- | --- |
| localStorage (per browser) | Odoo models `egct.po`, `egct.po.line`, `egct.shipment`, `egct.payment`, `egct.document`, `egct.supplier`, `egct.activity` (shared, backed up with the DB) |
| Email OTP gate (Netlify Functions + Resend) | Odoo login + access groups (User / Manager) |
| Replace / clear all data open to everyone | Managers only |
| Print = whole page | Print goes through a hidden iframe (tables and PO detail) |
| Merge logic in the browser | Merge / replace / ACID rules on the server (`models/egct_api.py`) |

Unchanged: dashboard, all 10 pages, alerts engine, date and payment maths (still derived in the browser from the
same dataset), Excel/CSV import with column mapping, XLSX/CSV export, document matrix, tracking inline edit.

Native Odoo list/form views of every model are available under Control Tower -> Data (Managers) for bulk edits.

## Architecture
* `models/` data models + `egct.api` (dataset serialisation and all write operations, runs with the caller's rights).
* `controllers/main.py` JSON-RPC routes (`/egct/...`, `auth='user'`, no sudo).
* `static/src/js/control_tower_action.js` OWL client action: lazy-loads the bundle and mounts it.
* `frontend/` React source. The app renders in a Shadow DOM, so its CSS and Odoo's Bootstrap never interfere.

## Rebuilding the front end
```bash
cd frontend
npm install
npm run build      # writes ../static/dist/egct.iife.js
npm run dev        # Vite dev server (needs an Odoo session for data; use Odoo for real testing)
```
`frontend/scripts/build-seed.py` regenerates `src/data/seed.json` from the two Excel files in `frontend/data/`.

## Tests
```bash
odoo-bin -d test_db -i european_group_control_tower --test-enable --test-tags /european_group_control_tower --stop-after-init
```
