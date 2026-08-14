import os
import re
import json
import time
import base64
import random
import threading
import tempfile
import subprocess

import telebot
from telebot import types
from urllib.parse import urlparse, unquote


TOKEN = "7868033717:AAGEHmJW3fRIA9PgPjvYTYoLvBy1chBK_Fo"


bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

CONFIG_RE = re.compile(r'(vless|vmess|trojan|ss)://[^\s]+', re.IGNORECASE)

cancel_flags = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("🚫 لغو عملیات"))
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    cancel_flags[message.chat.id] = False
    bot.reply_to(
        message,
        "✅ ربات آماده تست نهایی است.\n\n"
        "کانفیگ‌ها را (تکی/گروهی) بفرست یا فایل متنی بده.\n"
        "برای توقف، «🚫 لغو عملیات» را بزن.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: (m.text or "") == "🚫 لغو عملیات")
def cancel_now(message):
    cancel_flags[message.chat.id] = True
    bot.reply_to(message, "🛑 درخواست لغو ثبت شد. بررسی متوقف می‌شود.", reply_markup=main_menu())

def rand_port():
    return random.randint(12000, 22000)

def kill_process(p: subprocess.Popen):
    try:
        p.terminate()
        try:
            p.wait(timeout=1.5)
        except:
            p.kill()
    except:
        pass

def start_xray_process(cfg_path: str) -> subprocess.Popen:
    candidates = [
        ["xray", "run", "-c", cfg_path],
        ["xray", "run", "-config", cfg_path],
        ["xray", "run", f"-c={cfg_path}"],
        ["xray", "run", f"-config={cfg_path}"],
    ]

    last = None
    for cmd in candidates:
        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(0.35)

            if p.poll() is not None:
                err = ""
                try:
                    err = (p.stderr.read() or "").strip()
                except:
                    pass
                last = f"exited: {cmd} | err: {err[:400]}"
                continue

            return p

        except Exception as e:
            last = f"exception: {cmd} | {e}"

    raise RuntimeError(f"Could not start xray. last={last}")

# ---------- Parsers (برای گرفتن host/port و ساخت outbound) ----------

def vmess_decode(link: str) -> dict:
    b64 = link.split("vmess://", 1)[1].strip()
    pad = len(b64) % 4
    if pad:
        b64 += "=" * (4 - pad)
    return json.loads(base64.b64decode(b64).decode("utf-8", errors="ignore"))

def vmess_to_outbound(link: str) -> tuple[dict, str, str, int]:
    data = vmess_decode(link)
    name = data.get("ps") or "بدون نام"
    host = data.get("add")
    port = int(data.get("port", 443))
    uuid = data.get("id")
    net = (data.get("net") or "tcp").lower()
    tls_on = (data.get("tls") or "").lower() in ("tls", "1", "true")

    outbound = {
        "tag": "proxy",
        "protocol": "vmess",
        "settings": {
            "vnext": [{
                "address": host,
                "port": port,
                "users": [{
                    "id": uuid,
                    "alterId": 0,
                    "security": data.get("scy", "auto")
                }]
            }]
        },
        "streamSettings": {
            "network": net,
            "security": "tls" if tls_on else "none",
        }
    }
    if tls_on:
        outbound["streamSettings"]["tlsSettings"] = {"serverName": host}

    return outbound, name, host, port

def vless_to_outbound(link: str) -> tuple[dict, str, str, int]:
    u = urlparse(link)
    name = unquote(u.fragment) if u.fragment else "بدون نام"
    uuid = u.username
    host = u.hostname
    port = u.port or 443

    q = {}
    if u.query:
        for kv in u.query.split("&"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                q[k] = v
            else:
                q[kv] = ""

    security = (q.get("security") or "none").lower()
    net = (q.get("type") or q.get("network") or "tcp").lower()

    outbound = {
        "tag": "proxy",
        "protocol": "vless",
        "settings": {
            "vnext": [{
                "address": host,
                "port": port,
                "users": [{
                    "id": uuid,
                    "encryption": q.get("encryption", "none")
                }]
            }]
        },
        "streamSettings": {
            "network": net,
            "security": "tls" if security == "tls" else "none",
        }
    }

    if net == "ws":
        outbound["streamSettings"]["wsSettings"] = {
            "path": q.get("path", "/"),
            "headers": {"Host": q.get("host", host)}
        }

    return outbound, name, host, port

def trojan_to_outbound(link: str) -> tuple[dict, str, str, int]:
    u = urlparse(link)
    name = unquote(u.fragment) if u.fragment else "بدون نام"
    passwd = u.username
    host = u.hostname
    port = u.port or 443

    outbound = {
        "tag": "proxy",
        "protocol": "trojan",
        "settings": {
            "servers": [{
                "address": host,
                "port": port,
                "password": passwd
            }]
        },
        "streamSettings": {"security": "tls"}
    }
    return outbound, name, host, port

def ss_to_outbound(link: str) -> tuple[dict, str, str, int]:
    u = urlparse(link)
    name = unquote(u.fragment) if u.fragment else "بدون نام"

    if not u.netloc:
        raise ValueError("Unsupported SS format")

    if "@" not in u.netloc:
        raise ValueError("Unsupported SS format")

    userinfo, hostport = u.netloc.split("@", 1)
    pad = len(userinfo) % 4
    if pad:
        userinfo += "=" * (4 - pad)

    method_pass = base64.b64decode(userinfo).decode("utf-8", errors="ignore")
    method, password = method_pass.split(":", 1)

    host, port = hostport.split(":", 1)
    port = int(port)

    outbound = {
        "tag": "proxy",
        "protocol": "shadowsocks",
        "settings": {
            "servers": [{
                "address": host,
                "port": port,
                "method": method,
                "password": password
            }]
        }
    }
    return outbound, name, host, port

def link_to_outbound_and_target(link: str) -> tuple[dict, str, str, int, str]:
    low = link.lower()
    proto = link.split("://", 1)[0].upper()

    if low.startswith("vmess://"):
        outbound, name, host, port = vmess_to_outbound(link)
        return outbound, name, host, port, proto
    if low.startswith("vless://"):
        outbound, name, host, port = vless_to_outbound(link)
        return outbound, name, host, port, proto
    if low.startswith("trojan://"):
        outbound, name, host, port = trojan_to_outbound(link)
        return outbound, name, host, port, proto
    if low.startswith("ss://"):
        outbound, name, host, port = ss_to_outbound(link)
        return outbound, name, host, port, proto

    raise ValueError("Unsupported protocol")

# ---------- Tests ----------

def build_xray_config(outbound: dict, socks_port: int) -> dict:
    return {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {
                "tag": "socks-in",
                "listen": "127.0.0.1",
                "port": socks_port,
                "protocol": "socks",
                "settings": {"udp": True}
            }
        ],
        "outbounds": [
            outbound,
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"}
        ],
        "routing": {
            "domainStrategy": "AsIs",
            "rules": [
                {"type": "field", "inboundTag": ["socks-in"], "outboundTag": "proxy"}
            ]
        }
    }

def direct_tcp_test(host: str, port: int, timeout_s: int = 3) -> tuple[bool, int | None]:
    """تست مستقیم: آیا از شبکه فعلی دستگاه می‌شود به سرور کانفیگ وصل شد؟"""
    try:
        t0 = time.time()
        r = subprocess.run(["nc", "-zw", str(timeout_s), host, str(port)], capture_output=True)
        ms = int((time.time() - t0) * 1000)
        return (r.returncode == 0), ms
    except:
        return False, None

def tunnel_test_with_xray(outbound: dict, cancel_event: threading.Event) -> tuple[bool, int | None, int, str | None, int | None]:
    """تست داخل تونل: Xray + SOCKS + curl generate_204"""
    socks_port = rand_port()
    cfg = build_xray_config(outbound, socks_port)

    with tempfile.TemporaryDirectory() as td:
        cfg_path = os.path.join(td, "config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)

        p = None
        startup_ms = None
        try:
            if cancel_event.is_set():
                return False, None, 0, "Cancelled", None

            t_start = time.time()
            p = start_xray_process(cfg_path)

            ready = False
            for _ in range(40):
                if cancel_event.is_set():
                    return False, None, 0, "Cancelled", None

                if p.poll() is not None:
                    err = ""
                    try:
                        err = (p.stderr.read() or "").strip()
                    except:
                        pass
                    return False, None, 0, f"xray exited early: {err[:250]}", None

                chk = subprocess.run(["nc", "-z", "127.0.0.1", str(socks_port)], capture_output=True)
                if chk.returncode == 0:
                    ready = True
                    break
                time.sleep(0.1)

            if not ready:
                return False, None, 0, "SOCKS not listening", None

            startup_ms = int((time.time() - t_start) * 1000)

            t0 = time.time()
            curl = subprocess.run(
                [
                    "curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                    "--connect-timeout", "8", "--max-time", "15",
                    "--proxy", f"socks5h://127.0.0.1:{socks_port}",
                    "https://www.google.com/generate_204"
                ],
                capture_output=True,
                text=True
            )
            latency_ms = int((time.time() - t0) * 1000)

            code_txt = (curl.stdout or "").strip()
            http_code = int(code_txt) if code_txt.isdigit() else 0

            if http_code == 204:
                return True, latency_ms, http_code, None, startup_ms

            err = (curl.stderr or "").strip() or "No 204"
            return False, latency_ms, http_code, err[:250], startup_ms

        except Exception as e:
            return False, None, 0, str(e), startup_ms
        finally:
            if p is not None:
                kill_process(p)

def final_verdict(direct_ok: bool, tunnel_ok: bool) -> str:
    if not direct_ok and not tunnel_ok:
        return "❌ **خراب / قطع کامل**"
    if not direct_ok and tunnel_ok:
        return "⚠️ **فقط با عبور از فیلترینگ / وابسته به VPN**"
    if direct_ok and tunnel_ok:
        return "✅ **سالم واقعی**"
    return "⚠️ **عجیب: مستقیم وصل است ولی داخل تونل قطع**"

def format_report(i: int, name: str, proto: str, host: str, port: int,
                  direct_ok: bool, direct_ms: int | None,
                  tunnel_ok: bool, latency_ms: int | None, http_code: int,
                  err: str | None, startup_ms: int | None) -> str:

    d_state = "✅ وصل" if direct_ok else "❌ قطع"
    d_ms = f"{direct_ms}ms" if direct_ms is not None else "—"

    t_state = "✅ وصل" if tunnel_ok else "❌ قطع"
    lat = f"{latency_ms}ms" if latency_ms is not None else "—"
    st = f"{startup_ms}ms" if isinstance(startup_ms, int) else "—"

    verdict = final_verdict(direct_ok, tunnel_ok)

    msg = (
        f"📍 **مورد {i}**\n"
        f"🏷 نام: {name}\n"
        f"🛠 پروتکل: **{proto}**\n"
        f"🧭 هدف سرور: `{host}:{port}`\n\n"
        f"🔌 تست مستقیم (شبکه فعلی دستگاه): **{d_state}**  |  ⏱ {d_ms}\n"
        f"🌐 تست داخل تونل (Xray): **{t_state}**\n"
        f"🚀 Startup: {st}\n"
        f"⏱ تاخیر واقعی HTTP: {lat}\n"
        f"🔢 HTTP: {http_code}\n\n"
        f"📌 نتیجه نهایی: {verdict}\n"
    )
    if err:
        msg += f"⚠️ خطا: {err}\n"
    msg += "─────────────"
    return msg

def worker(chat_id: int, links: list[str]):
    cancel_flags[chat_id] = False
    cancel_event = threading.Event()

    bot.send_message(chat_id, f"🚀 شروع تست نهایی {len(links)} مورد...", reply_markup=main_menu())

    for i, link in enumerate(links, 1):
        if cancel_flags.get(chat_id):
            cancel_event.set()
            bot.send_message(chat_id, "🛑 عملیات توسط شما لغو شد.", reply_markup=main_menu())
            return

        try:
            outbound, name, host, port, proto = link_to_outbound_and_target(link)
        except Exception as e:
            bot.send_message(chat_id, f"📍 **مورد {i}**\n⚠️ خطا در پارس: {e}\n─────────────", reply_markup=main_menu())
            continue

        direct_ok, direct_ms = direct_tcp_test(host, port, timeout_s=3)

        tunnel_ok, latency_ms, http_code, err, startup_ms = tunnel_test_with_xray(outbound, cancel_event)

        bot.send_message(
            chat_id,
            format_report(i, name, proto, host, port, direct_ok, direct_ms, tunnel_ok, latency_ms, http_code, err, startup_ms),
            reply_markup=main_menu()
        )
        time.sleep(0.2)

@bot.message_handler(content_types=["text"])
def handle_text(message):
    if (message.text or "").startswith("/"):
        return
    links = [m.group(0) for m in CONFIG_RE.finditer(message.text or "")]
    if not links:
        bot.reply_to(message, "❌ کانفیگی پیدا نشد.", reply_markup=main_menu())
        return
    t = threading.Thread(target=worker, args=(message.chat.id, links), daemon=True)
    t.start()

@bot.message_handler(content_types=["document"])
def handle_doc(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        data = bot.download_file(file_info.file_path)
        content = data.decode("utf-8", errors="ignore")
        links = [m.group(0) for m in CONFIG_RE.finditer(content)]
        if not links:
            bot.reply_to(message, "❌ داخل فایل کانفیگی پیدا نشد.", reply_markup=main_menu())
            return
        t = threading.Thread(target=worker, args=(message.chat.id, links), daemon=True)
        t.start()
    except:
        bot.reply_to(message, "❌ خطا در خواندن فایل. بهتره .txt باشه.", reply_markup=main_menu())

print("Bot is running...")
bot.infinity_polling()
