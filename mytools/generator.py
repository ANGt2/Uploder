import random

# پیش شماره‌های معتبر ایران (چهار رقم اول شامل 09)
# اینبار خود 09 رو هم بخشی از پیش شماره می‌کنیم تا خطا برطرف بشه
MOBILE_PREFIXES = [
    '0910', '0911', '0912', '0913', '0914', '0915', '0916', '0917', '0918', '0919',  # همراه اول
    '0990', '0991', '0992', '0993', '0994', '0995', '0996', '0997', '0998', '0999',  # ایرانسل
    '0920', '0921', '0922', '0923'  # رایتل
]

BANKS = {
    '603799': 'ملی', '589210': 'سپه', '627648': 'توسعه صادرات',
    '622106': 'پارسیان', '502229': 'پاسارگاد', '610433': 'ملت',
    '627353': 'تجارت', '621986': 'سامان', '636949': 'حکمت ایرانیان'
}

CITIES = {
    'تهران': ['تهران', 'ری', 'شمیرانات'],
    'اصفهان': ['اصفهان', 'کاشان', 'خمینی شهر'],
    'خراسان رضوی': ['مشهد', 'نیشابور', 'سبزوار'],
    'فارس': ['شیراز', 'مرودشت', 'کازرون']
}

def random_mobile():
    """تولید شماره موبایل ۱۱ رقمی با پیش شماره معتبر"""
    prefix = random.choice(MOBILE_PREFIXES)  # این خودش 4 رقم اول رو میده (مثل 0912)
    suffix = ''.join(str(random.randint(0, 9)) for _ in range(7))  # 7 رقم باقی‌مونده
    return prefix + suffix  # 4 + 7 = 11 رقم

def random_card_number():
    bin_num = random.choice(list(BANKS.keys()))
    remaining = ''.join(str(random.randint(0, 9)) for _ in range(10))
    return bin_num + remaining, BANKS[bin_num]

def calculate_checksum(national_code):
    if not national_code.isdigit() or len(national_code) != 9:
        return None
    s = 0
    for i in range(9):
        s += int(national_code[i]) * (10 - i)
    remainder = s % 11
    return str(remainder) if remainder < 2 else str(11 - remainder)

def random_national_code():
    first_nine = ''.join(str(random.randint(0, 9)) for _ in range(9))
    control_digit = calculate_checksum(first_nine)
    province = random.choice(list(CITIES.keys()))
    city = random.choice(CITIES[province])
    return first_nine + control_digit, city, province

if __name__ == "__main__":
    print("\n" + "="*50)
    print("تولید کننده اطلاعات ساختگی")
    print("="*50 + "\n")
    
    for i in range(1, 6):
        print(f"✅ نمونه شماره {i}:")
        print(f"   📱 موبایل: {random_mobile()}")
        card, bank = random_card_number()
        print(f"   💳 کارت: {card} (بانک {bank})")
        national_id, city, province = random_national_code()
        print(f"   🆔 کد ملی: {national_id} - اهل {city}، {province}")
        print("-" * 40)
