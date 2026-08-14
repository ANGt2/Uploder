from datetime import datetime


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return datetime.now().strftime("%Y-%m-%d")


def normalize_phone(phone: str):
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("+98"):
        return "0" + phone[3:]
    if phone.startswith("98"):
        return "0" + phone[2:]
    return phone


def is_iranian_phone(phone: str):
    phone = normalize_phone(phone)
    return phone.startswith("09") and len(phone) == 11 and phone.isdigit()


def kyc_fa(status):
    return {
        "not_started": "احراز نشده",
        "pending": "در انتظار بررسی",
        "verified": "تأیید شده",
        "rejected": "رد شده",
    }.get(status or "not_started", "احراز نشده")


def level_fa(level):
    return {
        "normal": "معمولی",
        "advanced": "پیشرفته",
        "pro": "حرفه‌ای",
    }.get(level or "normal", "معمولی")


def order_status_fa(status):
    return {
        "waiting_receipt": "در انتظار رسید",
        "waiting_admin": "در انتظار بررسی ادمین",
        "approved": "تأیید شده",
        "rejected": "رد شده",
        "delivered": "تحویل شده",
    }.get(status, status)
