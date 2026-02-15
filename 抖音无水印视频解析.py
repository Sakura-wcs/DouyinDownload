import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
from playwright.sync_api import sync_playwright
import requests
import re
import os
from PIL import Image, ImageDraw

# ================= 配置区 =================
COLOR_BG = "#121212"        # 极简深黑背景
COLOR_CARD = "#1E1E1E"      # 卡片背景色
COLOR_PRIMARY = "#FE2C55"   # 抖音红 (主按钮)
COLOR_ACCENT = "#25F4EE"    # 抖音蓝 (进度条/高亮)
COLOR_TEXT = "#FFFFFF"      # 白字
COLOR_TEXT_GRAY = "#AAAAAA" # 灰字

class DouyinModernUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # === 1. 窗口基础设置 ===
        self.title(" 抖音无水印解析神器 v2.3")
        self.geometry("800x600")
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.video_url = ""
        self.default_filename = "douyin_video"

        self.icon_image = self.create_app_icon()
        self.setup_ui()

    def create_app_icon(self):
        """自动绘制图标"""
        try:
            size = (64, 64)
            img = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([(0, 0), size], radius=15, fill=COLOR_PRIMARY)
            triangle_coords = [(22, 16), (22, 48), (50, 32)]
            draw.polygon(triangle_coords, fill="white")
            return ctk.CTkImage(img, size=(32, 32))
        except:
            return None

    def setup_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ------------------ 顶部 Header ------------------
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text=" 抖音视频解析下载器", 
            image=self.icon_image,
            compound="left",
            font=("Microsoft YaHei", 24, "bold"),
            text_color=COLOR_TEXT
        )
        title_label.pack(side="left")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="by Zero817",
            font=("Arial", 12),
            text_color=COLOR_TEXT_GRAY
        )
        subtitle_label.pack(side="left", padx=15, pady=(8,0))

        # ------------------ 核心操作区 ------------------
        card_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=15)
        card_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(3, weight=1) 

        # 1. 输入区域
        input_label = ctk.CTkLabel(card_frame, text="粘贴分享链接:", font=("Microsoft YaHei", 14), text_color=COLOR_ACCENT)
        input_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))

        input_row = ctk.CTkFrame(card_frame, fg_color="transparent")
        input_row.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))

        self.url_entry = ctk.CTkEntry(
            input_row, 
            placeholder_text="在此处粘贴抖音分享口令...",
            height=45,
            border_width=0,
            fg_color="#2B2B2B",
            text_color="white",
            font=("Microsoft YaHei", 14)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_paste = ctk.CTkButton(
            input_row,
            text="📋 粘贴",
            width=80,
            height=45,
            fg_color="#444444",
            hover_color="#555555",
            font=("Microsoft YaHei", 13),
            command=self.paste_from_clipboard
        )
        self.btn_paste.pack(side="left")

        # 2. 操作按钮栏 (解析 / 复制 / 下载)
        btn_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="new", padx=20)

        # 解析按钮 (独占一行或左侧)
        self.btn_parse = ctk.CTkButton(
            btn_frame, 
            text="🚀 开始解析", 
            font=("Microsoft YaHei", 15, "bold"),
            height=45,
            fg_color=COLOR_PRIMARY,
            hover_color="#D61F40",
            corner_radius=8,
            command=self.start_parse_thread
        )
        self.btn_parse.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # === 两个结果操作按钮 (默认禁用) ===
        self.btn_copy = ctk.CTkButton(
            btn_frame, 
            text="🔗 复制直链", 
            font=("Microsoft YaHei", 14),
            height=45,
            fg_color="#333333",
            state="disabled",
            corner_radius=8,
            command=self.copy_url_to_clipboard
        )
        self.btn_copy.pack(side="left", fill="x", expand=True, padx=(5, 5))

        self.btn_download = ctk.CTkButton(
            btn_frame, 
            text="💾 下载视频", 
            font=("Microsoft YaHei", 15, "bold"),
            height=45,
            fg_color="#333333",
            state="disabled",
            corner_radius=8,
            command=self.save_video_dialog
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(5, 0))


        # 3. 日志区
        log_label = ctk.CTkLabel(card_frame, text="运行日志:", font=("Consolas", 12), text_color=COLOR_TEXT_GRAY)
        log_label.grid(row=3, column=0, sticky="nw", padx=20, pady=(20, 5))

        self.txt_log = ctk.CTkTextbox(
            card_frame, 
            font=("Consolas", 12), 
            text_color="#00FF00",
            fg_color="#000000",
            corner_radius=8,
            border_width=1,
            border_color="#333333"
        )
        self.txt_log.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # 4. 状态栏
        self.status_bar = ctk.CTkLabel(self, text="就绪", text_color="gray", anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=25, pady=(0, 10))

    # ================= 交互逻辑 =================
    
    def paste_from_clipboard(self):
        try:
            content = self.clipboard_get()
            if content:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, content)
                filename = self.extract_filename(content)
                self.log(f"📋 已粘贴。识别到内容: {filename}")
            else:
                self.log("⚠️ 剪贴板为空")
        except Exception as e:
            self.log(f"⚠️ 无法读取剪贴板: {e}")

    def copy_url_to_clipboard(self):
        if self.video_url:
            self.clipboard_clear()
            self.clipboard_append(self.video_url)
            self.log("✅ 直链已复制到剪贴板！")
            messagebox.showinfo("成功", "无水印直链已复制！")

    # ================= 逻辑代码 =================

    def log(self, msg):
        def _update():
            self.txt_log.insert(tk.END, f"> {msg}\n")
            self.txt_log.see(tk.END)
            self.status_bar.configure(text=msg)
        self.after(0, _update)

    def extract_filename(self, full_text):
        try:
            text_before_url = re.split(r'https?://', full_text)[0]
            clean_title = re.sub(r'^[\d\.]+\s+复制打开抖音，看看', '', text_before_url).strip()
            clean_title = clean_title.replace("复制打开抖音，看看", "").strip()
            if '#' in clean_title:
                clean_title = clean_title.split('#')[0].strip()
            if not clean_title:
                return "douyin_video"
            return re.sub(r'[\\/*?:"<>|]', '_', clean_title)[:100]
        except:
            return "douyin_video"

    def start_parse_thread(self):
        text = self.url_entry.get().strip()
        if not text: 
            self.log("❌ 错误：请先输入分享链接")
            return
        
        self.default_filename = self.extract_filename(text)
        self.log(f"📋 确认文件名: {self.default_filename}")
        
        self.btn_parse.configure(state="disabled", text="⏳ 解析中...")
        self.btn_copy.configure(state="disabled")     # 重置复制按钮
        self.btn_download.configure(state="disabled") # 重置下载按钮
        
        self.txt_log.delete(1.0, tk.END)
        self.log("正在启动解析引擎...")
        
        t = threading.Thread(target=self.run_playwright, args=(text,))
        t.start()

    def get_real_address(self, play_url):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"}
            res = requests.get(play_url, headers=headers, allow_redirects=False)
            if res.status_code == 302:
                return res.headers['Location']
            return play_url
        except Exception as e:
            return None

    def run_playwright(self, share_text):
        playwright = None
        browser = None
        try:
            import re
            url_match = re.search(r'https?://v\.douyin\.com/[a-zA-Z0-9]+/', share_text)
            start_url = url_match.group(0) if url_match else share_text

            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(
                headless=True,  
                args=['--disable-blink-features=AutomationControlled', '--autoplay-policy=no-user-gesture-required']
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                viewport={'width': 390, 'height': 844},
                is_mobile=True, has_touch=True
            )
            page = context.new_page()

            found_data = {"url": None} 
            def handle_response(response):
                if "aweme/v1/play" in response.url:
                    no_wm_url = response.url.replace("playwm", "play")
                    if found_data["url"] is None:
                        found_data["url"] = no_wm_url
            page.on("response", handle_response)

            self.log(f"🌍 访问页面: {start_url}...")
            try: page.goto(start_url, wait_until='domcontentloaded', timeout=20000)
            except: pass 
            try:
                page.wait_for_timeout(1000)
                page.mouse.click(200, 400)
            except: pass

            for i in range(15):
                if found_data["url"]: break
                page.wait_for_timeout(1000)

            if found_data["url"]:
                final_url = self.get_real_address(found_data["url"])
                if final_url:
                    self.video_url = final_url
                    self.log("✅ 解析成功！")
                    self.enable_action_buttons()
                else:
                    self.log("❌ 获取真实地址失败")
            else:
                self.log("❌ 解析超时，未捕获到视频流")

        except Exception as e:
            self.log(f"❌ 出错: {str(e)}")
        finally:
            if browser: browser.close()
            if playwright: playwright.stop()
            self.after(0, lambda: self.btn_parse.configure(state="normal", text="🚀 开始解析"))

    def enable_action_buttons(self):
        def _enable():
            self.btn_copy.configure(state="normal", fg_color="#444444", text_color="white")
            self.btn_download.configure(state="normal", fg_color=COLOR_ACCENT, text_color="black")
        self.after(0, _enable)

    def save_video_dialog(self):
        if not self.video_url: return
        file_path = filedialog.asksaveasfilename(
            initialfile=self.default_filename,
            defaultextension=".mp4",
            filetypes=[("MP4 视频文件", "*.mp4")],
            title="保存视频到..."
        )
        if file_path:
            t = threading.Thread(target=self.download_file, args=(file_path,))
            t.start()

    def download_file(self, file_path):
        self.log(f"📥 开始下载: {os.path.basename(file_path)}")
        self.after(0, lambda: self.btn_download.configure(state="disabled", text="下载中..."))
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            with requests.get(self.video_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
            self.log("✨ 下载完成！")
            messagebox.showinfo("成功", "视频已保存到本地")
        except Exception as e:
            self.log(f"❌ 下载失败: {str(e)}")
        finally:
            self.after(0, lambda: self.btn_download.configure(state="normal", text="💾 下载视频"))

if __name__ == "__main__":
    app = DouyinModernUI()
    app.mainloop()
