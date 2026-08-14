from mega import Mega

try:
    print("در حال اتصال به مگا...")
    mega = Mega()
    m = mega.login('nzriamirmhmd54@gmail.com', 'Amiramn0141+')
    
    print("✅ ورود موفقیت‌آمیز بود!")
    print("اکانت مگا با موفقیت متصل شد.")

except Exception as e:
    print(f"❌ خطا در اتصال به مگا: {e}")
