# SMSMisr Connector v2

This is a ready-to-install Odoo module that integrates with SMSMisr.

## Features
- Singleton configuration model `smsmisr.config` (username/password/sender/api_url)
- Connection status indicator and Test Connection button
- Message model `smsmisr.message` with list & form, queue & send now buttons
- SMS sending service (`smsmisr.service`) with send_queued helper
- Delivery Report endpoint: /smsmisr/dlr
- Cron job (disabled by default) to process queued messages

## Installation
1. Copy the `smsmisr_connector_v2` folder into your `addons` directory.
2. Restart Odoo and update apps list.
3. Install the module.
4. Under **Settings → Technical → SMS Misr** you'll find **Configuration** and **Messages** menus.

## Notes
- Ensure `requests` Python package is installed in Odoo environment:
  ```bash
  pip install requests
  ```
- Adjust api_url and payload parameters to match the SMSMisr account details they provide.
- The DLR endpoint mapping is generic — confirm provider DLR parameters and adapt controller if necessary.
