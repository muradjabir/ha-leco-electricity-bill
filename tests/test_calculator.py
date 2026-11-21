"""Unit tests for LECO bill, cycle, and prediction calculator."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

# Allow running tests in lightweight environments without Home Assistant installed
if "homeassistant" not in sys.modules:
    for mod in (
        "homeassistant",
        "homeassistant.components",
        "homeassistant.components.sensor",
        "homeassistant.components.number",
        "homeassistant.config_entries",
        "homeassistant.const",
        "homeassistant.core",
        "homeassistant.data_entry_flow",
        "homeassistant.exceptions",
        "homeassistant.helpers",
        "homeassistant.helpers.entity",
        "homeassistant.helpers.entity_platform",
        "homeassistant.helpers.event",
        "homeassistant.helpers.restore_state",
        "homeassistant.helpers.selector",
        "homeassistant.helpers.update_coordinator",
    ):
        sys.modules.setdefault(mod, MagicMock())

from datetime import date
import unittest

from custom_components.leco_bill.calculator import (
    calculate_leco_bill,
    calculate_predicted_consumption,
    get_billing_cycle,
)


class TestLECOCalculator(unittest.TestCase):
    """Test suite for billing cycle and LECO bill calculations."""

    def test_billing_cycle_same_month_after_billing_day(self) -> None:
        """Test cycle when current date is after billing day in the same month."""
        ref = date(2026, 11, 21)
        cycle = get_billing_cycle(ref, billing_day=15)
        self.assertEqual(cycle["cycle_start"], date(2026, 11, 15))
        self.assertEqual(cycle["cycle_end"], date(2026, 12, 15))
        self.assertEqual(cycle["days_in_cycle"], 30)
        self.assertEqual(cycle["days_elapsed"], 6)
        self.assertEqual(cycle["days_remaining"], 24)

    def test_billing_cycle_same_month_before_billing_day(self) -> None:
        """Test cycle when current date is before billing day in the same month."""
        ref = date(2026, 11, 10)
        cycle = get_billing_cycle(ref, billing_day=15)
        self.assertEqual(cycle["cycle_start"], date(2026, 10, 15))
        self.assertEqual(cycle["cycle_end"], date(2026, 11, 15))
        self.assertEqual(cycle["days_in_cycle"], 31)
        self.assertEqual(cycle["days_elapsed"], 26)
        self.assertEqual(cycle["days_remaining"], 5)

    def test_billing_cycle_exact_billing_day(self) -> None:
        """Test cycle on the exact billing day."""
        ref = date(2026, 11, 15)
        cycle = get_billing_cycle(ref, billing_day=15)
        self.assertEqual(cycle["cycle_start"], date(2026, 11, 15))
        self.assertEqual(cycle["cycle_end"], date(2026, 12, 15))
        self.assertEqual(cycle["days_elapsed"], 0)
        self.assertEqual(cycle["days_remaining"], 30)

    def test_calculate_low_user_tier_1(self) -> None:
        """Test low user tier 1 (<= 30 kWh) on 30-day base."""
        res = calculate_leco_bill(25, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "low_user")
        self.assertEqual(res["energy_charge"], 150.00)
        self.assertEqual(res["fixed_charge"], 100.00)
        self.assertEqual(res["sscl_charge"], 6.25)
        self.assertEqual(res["total_bill"], 256.25)

    def test_calculate_low_user_tier_2(self) -> None:
        """Test low user tier 2 (31 - 60 kWh) on 30-day base."""
        res = calculate_leco_bill(45, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "low_user")
        self.assertEqual(res["energy_charge"], 315.00)
        self.assertEqual(res["fixed_charge"], 250.00)
        self.assertEqual(res["sscl_charge"], 14.12)
        self.assertEqual(res["total_bill"], 579.12)

    def test_calculate_normal_user_80_kwh(self) -> None:
        """Test normal user tier (61 - 90 kWh) on 30-day base."""
        res = calculate_leco_bill(80, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "normal_user")
        self.assertEqual(res["energy_charge"], 1260.00)
        self.assertEqual(res["fixed_charge"], 400.00)
        self.assertEqual(res["sscl_charge"], 41.50)
        self.assertEqual(res["total_bill"], 1701.50)

    def test_calculate_normal_user_150_kwh(self) -> None:
        """Test normal user tier (121 - 180 kWh) on 30-day base."""
        res = calculate_leco_bill(150, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "normal_user")
        self.assertEqual(res["energy_charge"], 3600.00)
        self.assertEqual(res["fixed_charge"], 1500.00)
        self.assertEqual(res["sscl_charge"], 127.50)
        self.assertEqual(res["total_bill"], 5227.50)

    def test_calculate_normal_user_over_180_kwh(self) -> None:
        """Test normal user tier (> 180 kWh) on 30-day base."""
        res = calculate_leco_bill(200, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "normal_user")
        # 60*15 + 30*18 + 30*30 + 60*42 + 20*65 = 900+540+900+2520+1300 = 6160
        self.assertEqual(res["energy_charge"], 6160.00)
        self.assertEqual(res["fixed_charge"], 2000.00)
        self.assertEqual(res["sscl_charge"], 204.00)
        self.assertEqual(res["total_bill"], 8364.00)

    def test_calculate_zero_kwh(self) -> None:
        """Test zero kWh consumption."""
        res = calculate_leco_bill(0, days_in_cycle=30, prorate=False)
        self.assertEqual(res["energy_charge"], 0.00)
        self.assertEqual(res["fixed_charge"], 100.00)
        self.assertEqual(res["total_bill"], 102.50)

    def test_calculate_predicted_consumption(self) -> None:
        """Test average daily consumption and predicted cycle kWh."""
        # 15 days elapsed (1,296,000s), 150 kWh consumed in 30-day cycle
        res = calculate_predicted_consumption(150.0, days_in_cycle=30, days_elapsed_seconds=1296000.0)
        self.assertEqual(res["average_daily_kwh"], 10.0)
        self.assertEqual(res["predicted_kwh"], 300.0)

        bill = calculate_leco_bill(res["predicted_kwh"], days_in_cycle=30)
        self.assertEqual(bill["tier_applied"], "normal_user")
        self.assertGreater(bill["total_bill"], 10000.0)

    def test_calculate_predicted_consumption_minimum_duration(self) -> None:
        """Test clamping to prevent division by zero on fresh cycle start."""
        res = calculate_predicted_consumption(5.0, days_in_cycle=30, days_elapsed_seconds=0.0)
        self.assertGreater(res["average_daily_kwh"], 0.0)
        self.assertGreater(res["predicted_kwh"], 0.0)


if __name__ == "__main__":
    unittest.main()
