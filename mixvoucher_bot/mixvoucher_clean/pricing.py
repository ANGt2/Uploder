import json
import logging
import urllib.request

from config import NOBITEX_USDT_URL, DEFAULT_FALLBACK_RATE
from database import get_setting

logger = logging.getLogger(__name__)


def get_profit_percent():
    try:
        return float(get_setting("profit_percent", "8"))
    except Exception:
        return 8


def get_fallback_rate():
    try:
        return int(float(get_setting("fallback_rate", str(DEFAULT_FALLBACK_RATE))))
    except Exception:
        return DEFAULT_FALLBACK_RATE


def get_usdt_rate():
    try:
        req = urllib.request.Request(
            NOBITEX_USDT_URL,
            headers={"User-Agent": "MixVoucherBot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "ok":
            raise ValueError("Nobitex status is not ok")

        return int(float(data.get("lastTradePrice", 0)) / 10)
    except Exception as e:
        logger.warning("Nobitex failed: %s", e)
        return get_fallback_rate()


def get_uvoucher_rate():
    usdt = get_usdt_rate()
    return int(usdt * (1 + get_profit_percent() / 100))
