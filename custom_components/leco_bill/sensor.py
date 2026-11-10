"""Sensor platform for LECO Electricity Bill integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ACCOUNT_NUMBER
from .coordinator import LECOBillCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the LECO sensors from config entry."""
    coordinator: LECOBillCoordinator = hass.data[DOMAIN][entry.entry_id]
    account_no = entry.data[CONF_ACCOUNT_NUMBER]

    async_add_entities(
        [
            LECOBillSensor(coordinator, account_no, entry.entry_id),
            LECOConnectionStatusSensor(coordinator, account_no, entry.entry_id),
        ]
    )


class LECOBillSensor(CoordinatorEntity[LECOBillCoordinator], SensorEntity):
    """Representation of LECO Electricity Bill Balance Sensor."""

    _attr_has_entity_name = True
    _attr_translation_key = "bill_balance"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "LKR"
    _attr_icon = "mdi:lightning-bolt-circle"
    _unrecorded_attributes = frozenset(
        {
            "customer_name",
            "address",
            "meter_number",
        }
    )

    def __init__(
        self,
        coordinator: LECOBillCoordinator,
        account_number: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._account_number = account_number
        self._attr_unique_id = f"leco_bill_{account_number}"
        self._attr_name = "Electricity Bill Balance"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_number)},
            name=f"LECO Account {account_number}",
            manufacturer="Lanka Electricity Company (Pvt) Ltd",
            model="InstantPay Bill Account",
            entry_type=None,
        )

    @property
    def native_value(self) -> float | None:
        """Return the current balance."""
        if self.coordinator.data:
            return self.coordinator.data.get("balance")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity attributes."""
        if not self.coordinator.data:
            return {}
        return {
            "account_number": self._account_number,
            "customer_name": self.coordinator.data.get("customer_name"),
            "address": self.coordinator.data.get("address"),
            "meter_number": self.coordinator.data.get("meter_no"),
            "tariff": self.coordinator.data.get("tariff"),
            "branch": self.coordinator.data.get("branch"),
            "csc": self.coordinator.data.get("csc"),
            "service_type": self.coordinator.data.get("service_type"),
            "account_status": self.coordinator.data.get("account_status"),
            "connection_status": self.coordinator.data.get("connection_status"),
            "last_synced": self.coordinator.data.get("last_synced"),
        }


class LECOConnectionStatusSensor(CoordinatorEntity[LECOBillCoordinator], SensorEntity):
    """Representation of LECO Electricity Connection Status Sensor."""

    _attr_has_entity_name = True
    _attr_translation_key = "connection_status"

    def __init__(
        self,
        coordinator: LECOBillCoordinator,
        account_number: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._account_number = account_number
        self._attr_unique_id = f"leco_status_{account_number}"
        self._attr_name = "Connection Status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_number)},
            name=f"LECO Account {account_number}",
            manufacturer="Lanka Electricity Company (Pvt) Ltd",
            model="InstantPay Bill Account",
            entry_type=None,
        )

    @property
    def native_value(self) -> str | None:
        """Return the current connection status from the LECO portal."""
        if not self.coordinator.data:
            return None
        acc_status = self.coordinator.data.get("account_status")
        if acc_status and acc_status.strip().lower() not in ("normal", ""):
            return acc_status.strip()
        return self.coordinator.data.get("connection_status") or acc_status

    @property
    def icon(self) -> str:
        """Return dynamic icon based on exact status value."""
        val = (self.native_value or "").strip().lower()
        if val in ("account activated", "active", "normal"):
            return "mdi:power-plug"
        if val in ("account deactivated", "inactive", "disconnected", "suspended"):
            return "mdi:power-plug-off"
        return "mdi:power-plug-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity attributes."""
        if not self.coordinator.data:
            return {}
        return {
            "account_number": self._account_number,
            "connection_status": self.coordinator.data.get("connection_status"),
            "account_status": self.coordinator.data.get("account_status"),
            "tariff": self.coordinator.data.get("tariff"),
            "branch": self.coordinator.data.get("branch"),
            "csc": self.coordinator.data.get("csc"),
            "service_type": self.coordinator.data.get("service_type"),
            "last_synced": self.coordinator.data.get("last_synced"),
        }
