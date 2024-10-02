import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, StringVar
import configparser
import requests
from bs4 import BeautifulSoup
import random
import threading
import os
import webbrowser

# 安裝必要套件
for package in ['requests', 'bs4', 'configparser']:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

class TyphoonMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("颱風監視小幫手")
        self.root.geometry("400x400")
        
        self.setup_ui()
        self.fetching_data = False
        self.line_token, self.city = self.read_config()

    def setup_ui(self):
        self.output_text = tk.Text(self.root, height=15, width=50)
        self.output_text.pack(pady=10)

        wait_frame = tk.Frame(self.root)
        wait_frame.pack(pady=5)
        
        self.min_wait_var = StringVar()
        self.max_wait_var = StringVar()
        
        tk.Label(wait_frame, text="最小等待秒數:").pack(side=tk.LEFT, padx=5)
        tk.Entry(wait_frame, textvariable=self.min_wait_var, width=5).pack(side=tk.LEFT, padx=5)
        tk.Label(wait_frame, text="最大等待秒數:").pack(side=tk.LEFT, padx=5)
        tk.Entry(wait_frame, textvariable=self.max_wait_var, width=5).pack(side=tk.LEFT, padx=5)

        tk.Button(self.root, text="查看獲取 TOKEN 的步驟", command=self.show_instructions).pack(pady=10)
        tk.Button(self.root, text="測試發送 LINE Notify", command=self.test_send_notify).pack(pady=10)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="開始抓取資料", command=self.start_fetching_data).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="停止抓取資料", command=self.stop_fetching_data).pack(side=tk.LEFT, padx=5)

    @staticmethod
    def get_random_user_agent():
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/92.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/92.0.4515.107 Safari/537.36",
        ]
        return {'User-Agent': random.choice(user_agents)}

    def log_message(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)

    def read_config(self):
        config = configparser.ConfigParser()
        config_file_path = 'data.ini'

        if not os.path.exists(config_file_path):
            self.log_message("配置文件不存在！正在創建...")
            return self.create_config_file()

        try:
            config.read(config_file_path, encoding='utf-8')
            return config.get('settings', 'line_token'), config.get('settings', 'city')
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取配置文件時出現錯誤：{e}")
            return None, None

    def create_config_file(self):
        line_token = self.show_instructions()
        if line_token:
            city = self.select_city()
            if city:
                config = configparser.ConfigParser()
                config['settings'] = {'line_token': line_token, 'city': city}
                with open('data.ini', 'w', encoding='utf-8') as config_file:
                    config.write(config_file)
                self.log_message("配置文件已創建成功！")
                return line_token, city
            else:
                messagebox.showerror("錯誤", "必須選擇城市！")
        else:
            messagebox.showerror("錯誤", "必須填寫 LINE Notify Token！")
        return None, None

    def select_city(self):
        city_list = self.fetch_cities()
        if not city_list:
            messagebox.showerror("錯誤", "無法獲取城市資料！")
            return None

        city_window = tk.Toplevel(self.root)
        city_window.title("選擇城市")
        city_window.geometry("300x150")

        selected_city = StringVar(city_window)
        selected_city.set(city_list[0])

        tk.OptionMenu(city_window, selected_city, *city_list).pack(pady=20)
        tk.Button(city_window, text="確認", command=city_window.destroy).pack(pady=10)

        city_window.wait_window()
        return selected_city.get()

    def fetch_cities(self):
        url = "https://www.dgpa.gov.tw/typh/daily/nds.html"
        
        try:
            response = requests.get(url, headers=self.get_random_user_agent())
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            return [row.find_all('td')[0].text.strip() for row in soup.find('table').find_all('tr')[:-1] if row.find_all('td')]
        except Exception as e:
            self.log_message(f"出錯了: {e}")
            return []

    def send_line_notify(self, message):
        response = requests.post(
            'https://notify-api.line.me/api/notify',
            headers={'Authorization': f'Bearer {self.line_token}'},
            data={'message': message}
        )
        self.log_message("已發送 LINE Notify 訊息" if response.status_code == 200 else f"發送失敗，狀態碼: {response.status_code}")

    def fetch_city_data(self):
        url = "https://www.dgpa.gov.tw/typh/daily/nds.html"

        try:
            response = requests.get(url, headers=self.get_random_user_agent())
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for row in soup.find('table').find_all('tr')[:-1]:
                cells = row.find_all('td')
                if len(cells) > 0 and self.city in cells[0].text:
                    city_data = cells[1].text.strip()
                    self.log_message(f"{self.city}: {city_data}")
                    if "明天" in city_data:
                        self.send_line_notify(f"\n{self.city}: {city_data}\n https://www.dgpa.gov.tw/typh/daily/nds.html ")
                    return city_data
        except Exception as e:
            self.log_message(f"出錯了: {e}")
        return ""

    def start_fetching_data(self):
        if not os.path.exists('data.ini'):
            self.log_message("配置文件不存在，請先設置 LINE Notify Token 和城市。")
            self.line_token, self.city = self.create_config_file()
            if not self.line_token or not self.city:
                return

        if not self.fetching_data:
            self.fetching_data = True
            threading.Thread(target=self.fetch_data_periodically, daemon=True).start()

    def fetch_data_periodically(self):
        if self.fetching_data:
            try:
                min_wait = max(1, int(self.min_wait_var.get() or 1))
                max_wait = max(min_wait, int(self.max_wait_var.get() or 7))
                wait_time = random.randint(min_wait, max_wait)
                self.fetch_city_data()
                self.log_message(f"等待 {wait_time} 秒")
                self.root.after(wait_time * 1000, self.fetch_data_periodically)
            except ValueError:
                self.log_message("請輸入有效的整數秒數！")
                self.fetching_data = False

    def stop_fetching_data(self):
        self.fetching_data = False
        self.log_message("停止抓取資料")

    def test_send_notify(self):
        if not os.path.exists('data.ini'):
            self.log_message("配置文件不存在，請先設置 LINE Notify Token 和城市。")
            self.line_token, self.city = self.create_config_file()
            if not self.line_token or not self.city:
                return

        if self.line_token and self.city:
            city_data = self.fetch_city_data()
            self.send_line_notify(f"測試訊息：當前城市是 {self.city}。\n最新數據：{city_data}")
            self.log_message("測試訊息已發送！")
        else:
            self.log_message("錯誤:無法獲取 LINE Notify Token 或城市名稱。")

    def show_instructions(self):
        instructions_window = tk.Toplevel(self.root)
        instructions_window.title("獲取 LINE Notify Token")
        instructions_window.geometry("400x400")

        tk.Label(instructions_window, text="1. 訪問 LINE Notify 官方網站", anchor="w").pack(pady=10, padx=10, anchor="w")
        link_label = tk.Label(instructions_window, text="https://notify-bot.line.me/", fg="blue", cursor="hand2")
        link_label.pack(pady=5)
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://notify-bot.line.me/"))

        instructions_steps = (
            "2. 點擊右上角的 '登入' 按鈕，使用你的 LINE 帳號登入。\n\n"
            "3. 登入後，選擇 '個人頁面'。\n\n"
            "4. 在頁面最下面中，點擊 '發行權杖'。\n\n"
            "5. 輸入你希望的權杖名稱，並選擇要發送通知的聊天室（個人或群組）。\n\n"
            "6. 點擊 '發行'，複製生成的 Token。\n\n"
            "7. 將 Token 貼上進下方的輸入框中。"
        )
        tk.Label(instructions_window, text=instructions_steps, justify="left").pack(pady=10, padx=10)

        token_var = StringVar()
        token_entry = tk.Entry(instructions_window, textvariable=token_var, width=40)
        token_entry.pack(pady=10)

        def submit_token():
            instructions_window.destroy()

        tk.Button(instructions_window, text="提交", command=submit_token).pack(pady=10)

        instructions_window.wait_window()
        return token_var.get()

if __name__ == "__main__":
    root = tk.Tk()
    app = TyphoonMonitor(root)
    root.mainloop()
