import os
import requests
import sys
from bs4 import BeautifulSoup

# --- [بخش جدید] برای حل مشکل SSL سایت پست ---
# این کد به کتابخانه اتصال ما می‌گوید که از یک پروتکل امنیتی قدیمی‌تر هم پشتیبانی کند
import urllib3
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'
# --- [پایان بخش جدید] ---


# --- خواندن اطلاعات از Secrets گیت‌هاب ---
BOT_TOKEN = os.getenv('BALE_BOT_TOKEN')
CHAT_ID = os.getenv('BALE_CHAT_ID')
TRACKING_CODE = os.getenv('TRACKING_CODE')

# آدرس‌های مورد نیاز
POST_TRACKING_URL = f"https://tracking.post.ir/?id={TRACKING_CODE}"
BALE_API_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"

def get_tracking_status():
    """از سایت tracking.post.ir برای گرفتن آخرین وضعیت مرسوله استفاده می‌کند"""
    try:
        # حالا این درخواست با تنظیمات امنیتی جدید ارسال می‌شود
        response = requests.get(POST_TRACKING_URL)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', class_='table-striped')
        if not table:
            print("جدول اطلاعات مرسوله در صفحه یافت نشد. احتمالا کد رهگیری اشتباه است.")
            return None
            
        last_row = table.find_all('tr')[-1]
        columns = last_row.find_all('td')
        
        if len(columns) >= 4:
            date = columns[3].text.strip()
            time = columns[2].text.strip()
            status = columns[0].text.strip()
            location = columns[1].text.strip()
            final_status = f"{status} | مکان: {location} | زمان: {date} {time}"
            return final_status
        else:
            print("ساختار جدول وضعیت‌ها تغییر کرده است.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"خطا در اتصال به سایت پست: {e}")
        return None
    except Exception as e:
        print(f"خطا در پردازش اطلاعات صفحه: {e}")
        return None

def send_bale_message(message):
    """یک پیام به ربات بله ارسال می‌کند"""
    payload = {'chat_id': CHAT_ID, 'text': message}
    try:
        response = requests.post(BALE_API_URL, data=payload)
        response.raise_for_status()
        print("پیام «بله» با موفقیت ارسال شد.")
    except requests.exceptions.RequestException as e:
        print(f"خطا در ارسال پیام به «بله»: {e}")

def main():
    """تابع اصلی برنامه"""
    last_status = ""
    status_file = "last_status.txt"

    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            last_status = f.read().strip()
    except FileNotFoundError:
        print("فایل وضعیت قبلی یافت نشد. یک فایل جدید ایجاد می‌شود.")

    current_status = get_tracking_status()

    if not current_status:
        print("نمی‌توان وضعیت فعلی را دریافت کرد. برنامه متوقف می‌شود.")
        sys.exit(1)

    print(f"وضعیت قبلی: {last_status}")
    print(f"وضعیت فعلی: {current_status}")

    if current_status != last_status:
        print("وضعیت تغییر کرده است! در حال ارسال نوتیفیکیشن...")
        message = (
            f"📦 تغییر وضعیت مرسوله!\n\n"
            f"کد رهگیری: {TRACKING_CODE}\n\n"
            f"📌 وضعیت جدید: {current_status}"
        )
        send_bale_message(message)
        
        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(current_status)
    else:
        print("هیچ تغییری در وضعیت مرسوله وجود ندارد.")

if __name__ == "__main__":
    main()
