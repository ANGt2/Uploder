import os
import sys
import random
import string

GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'
YELLOW = '\033[93m'
CYAN = '\033[96m'

def generate_random_name():
    cool_words = ['alpha', 'nexus', 'shadow', 'cyber', 'matrix', 'phoenix', 'vortex', 'titan']
    word1 = random.choice(cool_words)
    word2 = random.choice(cool_words)
    while word1 == word2:
        word2 = random.choice(cool_words)
    random_digits = ''.join(random.choices(string.digits, k=3))
    return f"configs_{word1}_{word2}_{random_digits}.txt"

def extract_fast():
    print(f"{CYAN}🤖 Welcome to V2ray Config Cleaner!{RESET}")
    
    # 📥 گرفتن اسم فایل به صورت تعاملی از کاربر
    try:
        input_filename = input(f"{YELLOW}📝 Enter the input filename (e.g., Sub1.txt): {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{RED}🛑 Process cancelled by user.{RESET}")
        return

    # اگر کاربر چیزی تایپ نکرد، به طور پیش‌فرض Sub1.txt را در نظر بگیرد
    if not input_filename:
        input_filename = "Sub1.txt"
        print(f"{CYAN}💡 No name entered. Using default: Sub1.txt{RESET}")

    input_file = f'/sdcard/Download/{input_filename}'
    output_file = 'v2ray_links.txt'
    
    # بررسی وجود فایل در پوشه دانلود گوشی
    if not os.path.exists(input_file) or os.path.getsize(input_file) == 0:
        print(f"{RED}❌ Error: '{input_filename}' not found in Download folder!{RESET}")
        return

    protocols = ['vless://', 'vmess://', 'ss://', 'hysteria2://', 'tuic://']
    extracted_links = []

    print(f"{CYAN}⏳ Processing '{input_filename}' and filtering protocols...{RESET}")
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                clean_line = line.strip()
                if any(clean_line.startswith(proto) for proto in protocols):
                    if not clean_line.startswith('trojan://'):
                        extracted_links.append(clean_line)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}🛑 Process stopped by user.{RESET}")
        return

    total = len(extracted_links)
    print(f"{GREEN}✅ Successfully extracted {total} configs (No Trojan).{RESET}")

    if total == 0:
        print(f"{RED}⚠️ No valid configs found in this file.{RESET}")
        return

    with open(output_file, 'w', encoding='utf-8') as f_out:
        for link in extracted_links:
            f_out.write(link + '\n')
    
    unique_filename = generate_random_name()
    os.system(f'cp {output_file} /sdcard/{unique_filename}')
    print(f"{GREEN}📁 Clean configs saved to Internal Storage as: {unique_filename}{RESET}\n")

if __name__ == "__main__":
    extract_fast()
