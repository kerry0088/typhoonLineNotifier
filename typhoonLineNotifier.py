import subprocess
import sys
import time
import random
import configparser
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import messagebox, simpledialog, StringVar, OptionMenu
import os
import webbrowser
import threading

# 必要的套件
required_packages = ['requests', 'bs4', 'configparser']

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"{package} 未安裝，正在安裝...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# 創建 Tkinter 窗口
root = tk.Tk()
root.title("颱風監視小幫手")
root.geometry("400x400")  # 調整高度

# 在主窗口中添加 Text 小部件來顯示資訊
output_text = tk.Text(root, height=15, width=50)
output_text.pack(pady=10)

# 定義一個新的函數來在 Text 小部件中插入資訊
def log_message(message):
    output_text.insert(tk.END, message + "\n")
    output_text.see(tk.END)  # 自動滾動到最後一行

# 讀取配置文件的函數
def read_config():
    config = configparser.ConfigParser()
    config_file_path = 'data.ini'

    if not os.path.exists(config_file_path):
        log_message("配置文件 data.ini 不存在！正在創建配置文件...")
        root.after(0, create_config_file)  # 在主線程中創建配置文件
        return None, None  # 返回空值

    try:
        config.read(config_file_path, encoding='utf-8')  # 指定編碼
    except Exception as e:
        messagebox.showerror("錯誤", f"讀取配置文件時出現錯誤：{e}")
        sys.exit(1)

    if not config.has_section('settings') or not config.has_option('settings', 'line_token') or not config.has_option('settings', 'city'):
        messagebox.showerror("錯誤", "配置文件缺少必要的信息！請確保包含 LINE Notify Token 和城市名。")
        sys.exit(1)  # 終止程序

    line_token = config.get('settings', 'line_token')
    city = config.get('settings', 'city')
    return line_token, city

# 創建配置文件的函數
def create_config_file():
    line_token = simpledialog.askstring("輸入 LINE Notify Token", "請輸入您的 LINE Notify Token：")
    
    if line_token:
        city = select_city()
        if city:
            config = configparser.ConfigParser()
            config.add_section('settings')
            config.set('settings', 'line_token', line_token)
            config.set('settings', 'city', city)

            with open('data.ini', 'w', encoding='utf-8') as config_file:
                config.write(config_file)
            
            log_message("配置文件已創建成功！")
        else:
            messagebox.showerror("錯誤", "必須選擇城市！")
    else:
        messagebox.showerror("錯誤", "必須填寫 LINE Notify Token！")

# 選擇城市的函數
def select_city():
    city_list = fetch_cities()
    if not city_list:
        messagebox.showerror("錯誤", "無法獲取城市資料！")
        return None

    # 建立選擇城市的窗口
    city_window = tk.Toplevel(root)
    city_window.title("選擇城市")
    city_window.geometry("300x150")

    selected_city = StringVar(city_window)
    selected_city.set(city_list[0])  # 預設選擇第一個城市

    dropdown = OptionMenu(city_window, selected_city, *city_list)
    dropdown.pack(pady=20)

    confirm_button = tk.Button(city_window, text="確認", command=city_window.destroy)
    confirm_button.pack(pady=10)

    city_window.wait_window()  # 等待窗口關閉
    return selected_city.get()

# 獲取城市列表的函數
def fetch_cities():
    url = "https://www.dgpa.gov.tw/typh/daily/nds.html"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/92.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/92.0.4515.107 Safari/537.36",
    ]
    
    try:
        headers = {'User-Agent': random.choice(user_agents)}
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'  # 確保使用正確的編碼
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table')  # 找到第一個表格
        rows = table.find_all('tr')
        cities = []

        for row in rows[:-1]:  # 忽略最後一行註解
            cells = row.find_all('td')
            if cells:
                city_name = cells[0].text.strip()
                cities.append(city_name)

        return cities

    except Exception as e:
        log_message(f"出錯了: {e}")
        return []

# 發送 LINE Notify 訊息的函數
def send_line_notify(message, line_token):
    line_url = 'https://notify-api.line.me/api/notify'
    headers = {
        'Authorization': f'Bearer {line_token}'
    }
    data = {
        'message': message
    }
    response = requests.post(line_url, headers=headers, data=data)
    if response.status_code == 200:
        log_message("已發送 LINE Notify 訊息")
    else:
        log_message(f"發送失敗，狀態碼: {response.status_code}")

# 抓取城市數據的函數
def fetch_city_data(line_token, city):
    url = "https://www.dgpa.gov.tw/typh/daily/nds.html"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/92.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/92.0.4515.107 Safari/537.36",
    ]

    try:
        headers = {'User-Agent': random.choice(user_agents)}        
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'  # 確保使用正確的編碼
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table')  # 找到第一個表格
        rows = table.find_all('tr')
        city_data = ""

        for row in rows[:-1]:  # 忽略最後一行註解
            cells = row.find_all('td')
            if len(cells) > 0 and city in cells[0].text:
                city_data = cells[1].text.strip()
                log_message(f"{city}: {city_data}")

                if "明天" in city_data:
                    send_line_notify(f"\n{city}: {city_data}\n https://www.dgpa.gov.tw/typh/daily/nds.html ", line_token)
                    break
        
        return city_data  # 返回城市數據

    except Exception as e:
        log_message(f"出錯了: {e}")
        return ""

# 全局變量來控制數據抓取
fetching_data = False

# 從指定的線程運行數據抓取
def start_fetching_data_thread():
    global fetching_data
    line_token, city = read_config()
    if city is None:  # 如果沒有配置文件，則返回
        fetching_data = False
        return
    
    fetching_data = True
    fetch_city_data_periodically(line_token, city)

def fetch_city_data_periodically(line_token, city):
    if fetching_data:  # 檢查是否仍在抓取
        wait_time = random.randint(1, 7)
        fetch_city_data(line_token, city)
        log_message(f"等待 {wait_time} 秒")
        root.after(wait_time * 1000, fetch_city_data_periodically, line_token, city)  # 等待後重新調用

# 開始抓取數據的按鈕回調
def start_fetching_data():
    threading.Thread(target=start_fetching_data_thread, daemon=True).start()

# 停止抓取數據的按鈕回調
def stop_fetching_data():
    global fetching_data
    fetching_data = False
    log_message("停止抓取資料")

# 測試發送 LINE Notify 訊息的按鈕回調
def test_send_notify():
    line_token, city = read_config()
    if line_token and city:
        city_data = fetch_city_data(line_token, city)  # 獲取當前城市的數據
        message = f"測試訊息：當前城市是 {city}。\n最新數據：{city_data}"
        send_line_notify(message, line_token)
        log_message("測試訊息已發送！")
    else:
        log_message("錯誤:無法獲取 LINE Notify Token 或城市名稱。")

# 創建顯示網址的函數
def show_instructions():
    instructions_window = tk.Toplevel(root)
    instructions_window.title("獲取 LINE Notify Token")
    instructions_window.geometry("400x300")

    # 說明文字
    instructions_label = tk.Label(instructions_window, text="1. 訪問 LINE Notify 官方網站", anchor="w")
    instructions_label.pack(pady=10, padx=10, anchor="w")  # 左對齊

    # 超連結
    link_label = tk.Label(instructions_window, text="https://notify-bot.line.me/", fg="blue", cursor="hand2")
    link_label.pack(pady=5)
    link_label.bind("<Button-1>", lambda e: webbrowser.open("https://notify-bot.line.me/"))

    instructions_steps = (
        "2. 點擊右上角的 '登入' 按鈕，使用你的 LINE 帳號登入。\n\n"
        "3. 登入後，選擇 '個人頁面'。\n\n"
        "4. 在頁面最下面中，點擊 '發行權杖'。\n\n"
        "5. 輸入你希望的權杖名稱，並選擇要發送通知的聊天室（個人或群組）。\n\n"
        "6. 點擊 '發行'，複製生成的 Token。\n\n"
        "7. 將 Token 貼上進程式中以進行後續操作。"
    )

    steps_label = tk.Label(instructions_window, text=instructions_steps, justify="left")
    steps_label.pack(pady=10, padx=10)

    close_button = tk.Button(instructions_window, text="關閉", command=instructions_window.destroy)
    close_button.pack(pady=10)

# 創建查看獲取 TOKEN 的按鈕
btn_instructions = tk.Button(root, text="查看獲取 TOKEN 的步驟", command=show_instructions)
btn_instructions.pack(pady=10)

# 創建開始抓取資料的按鈕
btn_start = tk.Button(root, text="開始抓取資料", command=start_fetching_data)
btn_start.pack(pady=10)

# 創建停止抓取資料的按鈕
btn_stop = tk.Button(root, text="停止抓取資料", command=stop_fetching_data)
btn_stop.pack(pady=10)

# 創建測試發送的按鈕
btn_test_send = tk.Button(root, text="測試發送 LINE Notify", command=test_send_notify)
btn_test_send.pack(pady=10)

# 運行 Tkinter 主循環
root.mainloop()
