# LECO Electricity Bill (Sri Lanka) - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/default)
[![GitHub release](https://img.shields.io/github/v/release/muradjabir/ha-leco-electricity-bill?style=for-the-badge)](https://github.com/muradjabir/ha-leco-electricity-bill/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

Track your **Lanka Electricity Company (LECO)** electricity bill balance, connection status, and account details directly in Home Assistant.

This custom component pulls bill and connection details daily from the official [LECO InstantPay](https://ipg.leco.lk) portal with zero credentials required—only your 10-digit LECO electricity account number.

---

## Features

- **Automatic Daily Updates:** Fetches current outstanding balance and connection status once every 24 hours.
- **Config Flow Setup:** Easy UI configuration directly in Home Assistant (Settings -> Devices & Services -> Add Integration).
- **Multiple Accounts:** Track multiple LECO electricity connections in the same Home Assistant instance.
- **Entities Provided per Account:**
  - `sensor.electricity_bill_balance`: Current bill balance in `LKR` (`monetary` device class).
  - `sensor.connection_status`: Live connection/account status reported by LECO (`ACCOUNT ACTIVATED`, `NORMAL`, etc.).
- **Rich Attributes:**
  - `account_number`: Your 10-digit LECO account number
  - `customer_name`: Name registered with LECO
  - `address`: Service address
  - `meter_number`: Meter ID
  - `tariff`: Tariff category (e.g., `DOMESTIC`)
  - `branch` / `csc`: LECO Branch and Customer Service Center
  - `service_type`: Service connection type (e.g., `PERMANENT CONNECTION`)
  - `account_status` / `connection_status`: Portal status fields
  - `last_synced`: Timestamp of last sync

---

## Installation

### Method 1: Via HACS (1-Click Install)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=muradjabir&repository=ha-leco-electricity-bill&category=integration)

Click the button above to directly open and install the repository in HACS, or follow the manual steps:

1. In Home Assistant, open **HACS** > **Integrations**.
2. Click the **three dots** in the top right corner and select **Custom repositories**.
3. Paste the repository URL:
   ```text
   https://github.com/muradjabir/ha-leco-electricity-bill
   ```
4. Select Category: **Integration** and click **Add**.
5. Search for **LECO Electricity Bill (Sri Lanka)** and click **Download**.
6. Restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release `.zip` or clone this repository.
2. Copy the `custom_components/leco_bill` directory into your Home Assistant `<config_dir>/custom_components/` folder.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **LECO Electricity Bill (Sri Lanka)**.
4. Enter your 10-digit LECO Account Number (e.g. `0211140204`) and submit.
5. Two sensors (`Electricity Bill Balance` and `Connection Status`) will be created under your LECO device.

---

## Example Automation: Bill Change Notification

Get a push notification whenever your monthly electricity bill is updated:

```yaml
alias: "LECO Electricity Bill Notification"
description: "Notify when LECO electricity bill balance changes"
trigger:
  - platform: state
    entity_id: sensor.leco_account_0211140204_electricity_bill_balance
condition:
  - condition: template
    value_template: >-
      {{ trigger.from_state is not none and
         trigger.to_state is not none and
         trigger.from_state.state not in ['unavailable', 'unknown'] and
         trigger.to_state.state not in ['unavailable', 'unknown'] and
         trigger.from_state.state != trigger.to_state.state }}
action:
  - service: notify.notify
    data:
      title: "LECO Electricity Bill Updated"
      message: >-
        Your LECO bill balance changed from {{ trigger.from_state.state }} LKR to {{ trigger.to_state.state }} LKR.
mode: single
```

---

## Disclaimer

This integration is an independent open-source project and is not officially affiliated with, endorsed by, or sponsored by Lanka Electricity Company (Pvt) Ltd (LECO).

---

## License

[MIT License](LICENSE)
