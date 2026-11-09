"""Coordinator for fetching LECO electricity bill data."""
from __future__ import annotations

from datetime import datetime, timedelta
import http.cookiejar
import json
import logging
import urllib.request

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)

URL_BASE = "https://ipg.leco.lk"
URL_DETAILS = "https://ipg.leco.lk/Token/GetDetails"


class InvalidAccountError(ValueError):
    """Raised when the LECO portal reports an invalid account number."""


def fetch_leco_bill_sync(account_no: str) -> dict:
    """Fetch electricity bill details synchronously from the LECO InstantPay portal."""
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar)
    )
    opener.addheaders = [
        (
            "User-Agent",
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        ),
        ("Accept", "application/json, text/javascript, */*; q=0.01"),
        ("X-Requested-With", "XMLHttpRequest"),
        ("Origin", URL_BASE),
        ("Referer", f"{URL_BASE}/"),
    ]

    # 1. Establish session cookies
    with opener.open(URL_BASE, timeout=20) as resp1:
        resp1.read()

    # 2. Query account details (ARN = Electricity Bill)
    payload_bytes = json.dumps({"type": "ARN", "payno": account_no}).encode("utf-8")
    req = urllib.request.Request(
        URL_DETAILS,
        data=payload_bytes,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with opener.open(req, timeout=25) as resp2:
        raw_body = resp2.read().decode("utf-8")

    payload = json.loads(raw_body)
    if not isinstance(payload, dict):
        raise ValueError("Unexpected non-JSON-object response from LECO portal")

    if payload.get("message"):
        raise InvalidAccountError(str(payload["message"]))

    desc = payload.get("data", {}).get("responseStatusDesc")
    if not isinstance(desc, dict):
        raise ValueError(
            f"Missing 'responseStatusDesc' in LECO portal response for account {account_no}"
        )

    raw_balance = desc.get("ACC_BALANCE")
    if raw_balance is None or str(raw_balance).strip() == "":
        raise ValueError(
            f"Missing 'ACC_BALANCE' field in LECO portal response for account {account_no}"
        )

    try:
        balance = float(str(raw_balance).replace(",", "").strip())
    except ValueError as err:
        raise ValueError(
            f"Invalid 'ACC_BALANCE' value {raw_balance!r} for account {account_no}"
        ) from err

    connection_status = (desc.get("CONNECTION_STATUS") or "").strip() or None
    account_status = (desc.get("ACCOUNT_STATUS") or "").strip() or None
    if not connection_status and not account_status:
        raise ValueError(
            f"Missing status fields in LECO portal response for account {account_no}"
        )

    return {
        "account_number": (desc.get("ACCOUNT_NO") or account_no).strip(),
        "balance": balance,
        "customer_name": (desc.get("NAME") or "").strip() or None,
        "address": (desc.get("ADDRESS") or "").strip() or None,
        "meter_no": (desc.get("METER_ID") or "").strip() or None,
        "tariff": (desc.get("TARIFF_DESCRIPTION") or "").strip() or None,
        "branch": (desc.get("BRANCH") or "").strip() or None,
        "csc": (desc.get("CSC") or "").strip() or None,
        "service_type": (desc.get("SERVICE_TYPE") or "").strip() or None,
        "account_status": account_status,
        "connection_status": connection_status,
        "last_synced": datetime.now().isoformat(),
    }


class LECOBillCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching LECO bill data from the portal."""

    def __init__(
        self,
        hass: HomeAssistant,
        account_number: str,
        scan_interval_hours: int = DEFAULT_SCAN_INTERVAL_HOURS,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"LECO Bill ({account_number})",
            update_interval=timedelta(hours=scan_interval_hours),
        )
        self.account_number = account_number

    async def _async_update_data(self) -> dict:
        """Fetch data from LECO portal in executor."""
        try:
            return await self.hass.async_add_executor_job(
                fetch_leco_bill_sync, self.account_number
            )
        except ValueError as err:
            raise UpdateFailed(f"LECO portal response error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with LECO portal: {err}") from err
