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

    def test_calculate_band_1_subsidized_tier_1(self) -> None:
        """Test Band 1 (0-30 kWh) on 30-day base."""
        res = calculate_leco_bill(25, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "band_1_subsidized")
        self.assertEqual(res["energy_charge"], 125.00)
        self.assertEqual(res["fixed_charge"], 80.00)
        self.assertEqual(res["sscl_charge"], 5.26)
        self.assertEqual(res["total_bill"], 210.26)

    def test_calculate_band_1_subsidized_tier_2(self) -> None:
        """Test Band 1 (31-60 kWh) on 30-day base."""
        res = calculate_leco_bill(45, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "band_1_subsidized")
        self.assertEqual(res["energy_charge"], 285.00)
        self.assertEqual(res["fixed_charge"], 210.00)
        self.assertEqual(res["sscl_charge"], 12.69)
        self.assertEqual(res["total_bill"], 507.69)

    def test_calculate_example_a_100_units(self) -> None:
        """Test Example A (100 units in Band 2)."""
        res = calculate_leco_bill(100, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "band_2_normal")
        self.assertEqual(res["energy_charge"], 1720.00)
        self.assertEqual(res["fixed_charge"], 1000.00)
        self.assertEqual(res["sscl_charge"], 69.74)
        self.assertEqual(res["total_bill"], 2789.74)

    def test_calculate_example_b_200_units(self) -> None:
        """Test Example B (200 units in Band 3)."""
        res = calculate_leco_bill(200, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "band_3_heavy")
        self.assertEqual(res["energy_charge"], 7850.00)
        self.assertEqual(res["fixed_charge"], 2500.00)
        self.assertEqual(res["sscl_charge"], 265.38)
        self.assertEqual(res["total_bill"], 10615.38)

    def test_calculate_325_units(self) -> None:
        """Test 325 units under May 11, 2026 tariff schedule (~23,435.90 LKR)."""
        res = calculate_leco_bill(325, days_in_cycle=30, prorate=False)
        self.assertEqual(res["tier_applied"], "band_3_heavy")
        self.assertEqual(res["energy_charge"], 20350.00)
        self.assertEqual(res["fixed_charge"], 2500.00)
        self.assertEqual(res["sscl_charge"], 585.90)
        self.assertEqual(res["total_bill"], 23435.90)

    def test_calculate_zero_kwh(self) -> None:
        """Test zero kWh consumption."""
        res = calculate_leco_bill(0, days_in_cycle=30, prorate=False)
        self.assertEqual(res["energy_charge"], 0.00)
        self.assertEqual(res["fixed_charge"], 80.00)
        self.assertEqual(res["total_bill"], 82.05)

    def test_calculate_predicted_consumption(self) -> None:
        """Test average daily consumption and predicted cycle kWh."""
        res = calculate_predicted_consumption(150.0, days_in_cycle=30, days_elapsed_seconds=1296000.0)
        self.assertEqual(res["average_daily_kwh"], 10.0)
        self.assertEqual(res["predicted_kwh"], 300.0)


if __name__ == "__main__":
    unittest.main()
