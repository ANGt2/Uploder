import os
import random
import string
import re

def generate_random_name():
    cool_words = ['v2ray', 'nexus', 'matrix', 'vortex', 'titan', 'cyber']
    word1 = random.choice(cool_words)
    word2 = random.choice(cool_words)
    while word1 == word2:
        word2 = random.choice(cool_words)
    random_digits = ''.join(random.choices(string.digits, k=3))
    return f"v2ray_{word1}_{word2}_{random_digits}.txt"

def parse_clash_to_v2ray():
    input_file = 'clash.yaml'
    if not os.path.exists(input_file) or os.path.getsize(input_file) == 0:
        print("❌ Error: clash.yaml not found or empty!")
        return

    print("⏳ Parsing Clash YAML and converting to v2rayNG links...")
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    clean_links = []

    # ۱. ابتدا بررسی میکنیم اگر لینک خامی از قبل در فایل وجود دارد استخراج شود
    raw_protocols = ['vless://', 'vmess://', 'ss://', 'hysteria2://', 'tuic://']
    for line in content.split('\n'):
        line_clean = line.strip().replace('-', '').strip()
        if any(line_clean.startswith(p) for p in raw_protocols) and not line_clean.startswith('trojan://'):
            if line_clean not in clean_links:
                clean_links.append(line_clean)

    # ۲. اگر لینک خامی پیدا نشد، ساختار پروکسی‌های کلش را به لینک تبدیل میکنیم
    if len(clean_links) == 0:
        # پیدا کردن بخش proxies در فایل یامل
        proxies_section = re.findall(r'-\s*\{\s*name:[^}]+}', content)
        if not proxies_section:
            # روش دوم استخراج بلاک‌های پروکسی در کلش
            proxies_section = re.findall(r'-\s*name:\s*(.*?)(?=\s*-\s*name:|\s*proxy-groups:|\Z)', content, re.DOTALL)

        for block in proxies_section:
            try:
                # حذف تروجان از فرآیند استخراج
                if 'type: trojan' in block or 'type:\s*trojan' in block:
                    continue
                
                # استخراج اطلاعات کلیدی با Regex
                name = re.search(r'name:\s*["\']?(.*?)["\']?(?:\s*,|\s*\n)', block)
                server = re.search(r'server:\s*["\']?(.*?)["\']?(?:\s*,|\s*\n)', block)
                port = re.search(r'port:\s*(\d+)', block)
                uuid = re.search(r'uuid:\s*["\']?(.*?)["\']?(?:\s*,|\s*\n)', block)
                cipher = re.search(r'cipher:\s*["\']?(.*?)["\']?(?:\s*,|\s*\n)', block)
                type_proto = re.search(r'type:\s*["\']?(.*?)["\']?(?:\s*,|\s*\n)', block)

                if server and port and type_proto:
                    srv = server.group(1).strip()
                    prt = port.group(1).strip()
                    proto = type_proto.group(1).strip().lower()
                    nm = urllib.parse.quote(name.group(1).strip()) if name else "Clash_Server"
                    
                    # تبدیل به فرمت VLESS
                    if proto == 'vless' and uuid:
                        uid = uuid.group(1).strip()
                        link = f"vless://{uid}@{srv}:{prt}?encryption=none#{nm}"
                        clean_links.append(link)
                    
                    # تبدیل به فرمت VMess (نیاز به اکستراکت ساده بدون انکود بیس۶۴ پیچیده برای سرورهای عمومی دارد)
                    elif proto == 'vmess' and uuid:
                        uid = uuid.group(1).strip()
                        # ساخت یک لینک سازگار با کلاینت‌ها
                        link = f"vmess://{uid}@{srv}:{prt}?remarks={nm}"
                        clean_links.append(link)
                        
                    # تبدیل به فرمت Shadowsocks (SS)
                    elif proto == 'ss' and cipher:
                        pwd = re.search(r'password:\s*["\']?(.*?)["\']?(?:\s*,|\s*\n)', block)
                        if pwd:
                            cph = cipher.group(1).strip()
                            password = pwd.group(1).strip()
                            link = f"ss://{cph}:{password}@{srv}:{prt}#{nm}"
                            clean_links.append(link)
            except:
                continue

    if len(clean_links) == 0:
        print("⚠️ No proxy structures could be parsed from this file format.")
        return

    # ذخیره فایل نهایی متنی برای v2rayNG
    output_filename = generate_random_name()
    with open(f'/sdcard/{output_filename}', 'w', encoding='utf-8') as f_out:
        for link in clean_links:
            f_out.write(link + '\n')

    print(f"✅ Successfully fixed! Converted {len(clean_links)} clean configs for v2rayNG.")
    print(f"📁 Saved to Internal Storage as: {output_filename}\n")

if __name__ == "__main__":
    import urllib.parse
    parse_clash_to_v2ray()
