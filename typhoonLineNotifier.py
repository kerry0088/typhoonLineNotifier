import subprocess
import sys
import time
import random
import configparser
required_packages = ['requests', 'bs4', 'configparser']

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"{package} 未安装，正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
import requests
from bs4 import BeautifulSoup
# 基本資訊
config = configparser.ConfigParser()
with open('data.ini', 'r', encoding='utf-8') as config_file:
    config.read_file(config_file)
line_token = config.get('settings', 'line_token')
city = config.get('settings', 'city')
print(f"讀取到設定檔,line_notify之token為{line_token}\n指定城市為{city}")
# 目標網址
url = "https://www.dgpa.gov.tw/typh/daily/nds.html"

# 自訂 header
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Linux; Android 10; SM-G950F Build/QP1A.190711.020) Chrome/72.0.3626.121 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 9; Pixel 3 Build/PQ1A.190205.002) Chrome/70.0.3538.110 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
]

# LINE Notify 權杖

# 發送 LINE Notify 訊息的函數
def send_line_notify(message):
    line_url = 'https://notify-api.line.me/api/notify'
    headers = {
        'Authorization': f'Bearer {line_token}'
    }
    data = {
        'message': message
    }
    response = requests.post(line_url, headers=headers, data=data)
    if response.status_code == 200:
        print("已發送 LINE Notify 訊息")
    else:
        print(f"發送失敗，狀態碼: {response.status_code}")


def fetch_taichung_data():
    try:
        headers = {
            'User-Agent': random.choice(user_agents)
        }        
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'  # 確保使用正確的編碼
        soup = BeautifulSoup(response.text, 'html.parser')

        # 假設台中市的資料位於特定的表格中
        table = soup.find('table')  # 找到第一個表格
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 0 and city in cells[0].text:
                taichung_data = cells[1].text.strip()
                print(f"{city}: {taichung_data}")

                # 檢查是否包含 "明天"
                if "明天" in taichung_data:
                    send_line_notify(f"\n{city}: {taichung_data}\n https://www.dgpa.gov.tw/typh/daily/nds.html ")
                    sys.exit(0)
                break

    except Exception as e:
        print(f"出錯了: {e}")


while True:
    wait_time = random.randint(1, 7)
    fetch_taichung_data()
    print(f"等待{wait_time}秒")
    time.sleep(wait_time)
