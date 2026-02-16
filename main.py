import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import subprocess
import threading
import os
import sys
import base64

# Simple config
APP_TITLE = "ArchAutoUpdater"
IMG_FILE = "image.png"
PASS_FILE = ".sudo_pass"

class UpdaterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("800x500")
        self.resizable(False, False)
        
        # Make it look slightly less ancient
        self.configure(bg="#2b2b2b")

        # Layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.ensure_password()

    def setup_ui(self):
        # Styles
        fg_color = "#ffffff"
        bg_color = "#2b2b2b"
        btn_bg = "#1f6aa5"
        
        # --- LEFT PANEL (Controls) ---
        self.left_panel = tk.Frame(self, bg=bg_color)
        self.left_panel.grid(row=0, column=0, sticky="nswe", padx=20, pady=20)
        
        # Title
        self.lbl_title = tk.Label(self.left_panel, text="Arch Updater", font=("Arial", 24, "bold"), bg=bg_color, fg=fg_color)
        self.lbl_title.pack(pady=(40, 20))

        # Status
        self.lbl_status = tk.Label(self.left_panel, text="Ready to go...", font=("Arial", 12), bg=bg_color, fg="#aaaaaa")
        self.lbl_status.pack(pady=10)

        # Progress (Determinate because standard tk indeterminate is ugly/hard)
        # We'll just use status text mainly, maybe a simple canvas bar if we wanted fancy
        
        # Button
        self.btn_update = tk.Button(self.left_panel, text="Check & Update", command=self.do_update, 
                                    bg=btn_bg, fg=fg_color, font=("Arial", 12), relief="flat", padx=20, pady=10)
        self.btn_update.pack(pady=20)

        # Console Log
        self.console = scrolledtext.ScrolledText(self.left_panel, height=10, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.console.pack(pady=10, fill="both", expand=True)
        self.console.config(state="disabled")

        # --- RIGHT PANEL (Image) ---
        self.right_panel = tk.Frame(self, bg=bg_color)
        self.right_panel.grid(row=0, column=1, sticky="nswe")
        
        try:
            # Load PNG natively
            # Image is pre-resized to fit height=500, so valid directly
            self.orig_img = tk.PhotoImage(file=IMG_FILE)
            self.lbl_img = tk.Label(self.right_panel, image=self.orig_img, bg=bg_color)
            self.lbl_img.pack(expand=True)
            
        except Exception as e:
            print(f"Failed to load image: {e}")
            self.lbl_img = tk.Label(self.right_panel, text="[Image Missing]", bg=bg_color, fg=fg_color)
            self.lbl_img.pack(expand=True)

    def log_msg(self, text):
        self.console.config(state="normal")
        self.console.insert("end", text + "\n")
        self.console.see("end")
        self.console.config(state="disabled")

    # --- Password Stuff (File based now, no keyring lib) ---
    def get_pwd(self):
        if os.path.exists(PASS_FILE):
            try:
                with open(PASS_FILE, "r") as f:
                    # Simple base64 decode to not store plain text directly readable by eyes
                    # (still not secure, but requested feature)
                    encoded = f.read().strip()
                    return base64.b64decode(encoded).decode("utf-8")
            except:
                return None
        return None

    def save_pwd(self, pwd):
        try:
            with open(PASS_FILE, "w") as f:
                encoded = base64.b64encode(pwd.encode("utf-8")).decode("utf-8")
                f.write(encoded)
        except Exception as e:
            self.log_msg(f"Save password failed: {e}")

    def ensure_password(self):
        if not self.get_pwd():
            # Standard dialog
            input_val = simpledialog.askstring("Auth Required", "Enter sudo password for pacman:", show='*')
            if input_val:
                self.save_pwd(input_val)
            else:
                self.log_msg("Warn: No password provided.")

    # --- Update Logic ---
    def do_update(self):
        self.btn_update.config(state="disabled")
        t = threading.Thread(target=self._run_pacman, daemon=True)
        t.start()

    def _run_pacman(self):
        pwd = self.get_pwd()
        
        if not pwd:
            self.log_msg("Error: Missing sudo password. Restart app.")
            self.after(0, self.cleanup)
            return

        success = False
        try:
            self.log_msg("Syncing DBs (pacman -Sy)...")
            
            cmd1 = ["sudo", "-S", "pacman", "-Sy"]
            p1 = subprocess.Popen(cmd1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out1, err1 = p1.communicate(input=f"{pwd}\n")
            
            if p1.returncode != 0:
                self.log_msg(f"Sync failed: {err1}")
                self.after(0, self.cleanup)
                return
            
            self.log_msg("DB Synced.")
            self.log_msg("Upgrading system (pacman -Su)...")

            cmd2 = ["sudo", "-S", "pacman", "-Su", "--noconfirm"]
            p2 = subprocess.Popen(cmd2, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            p2.stdin.write(f"{pwd}\n")
            p2.stdin.flush()
            
            while True:
                line = p2.stdout.readline()
                if not line and p2.poll() is not None:
                    break
                if line:
                    safe_line = line.strip()
                    self.after(0, lambda l=safe_line: self.log_msg(l))

            p2.wait()
            
            if p2.returncode == 0:
                 self.log_msg("Done! System is up to date.")
                 success = True
            else:
                 err2 = p2.stderr.read()
                 if "nothing to do" in err2 or (out1 and "nothing to do" in out1):
                     self.log_msg("Nothing to update.")
                     success = True
                 else:
                     self.log_msg(f"Process failed: {err2}")

        except Exception as ex:
            self.log_msg(f"Exception: {ex}")
        
        self.after(0, lambda: self.cleanup(auto_close=success))

    def cleanup(self, auto_close=False):
        self.btn_update.config(state="normal")
        self.lbl_status.config(text="Finite.")
        
        if auto_close:
            timeout = 20
            self.log_msg(f"Auto-closing in {timeout}s...")
            self.btn_update.config(state="disabled")
            self.countdown(timeout)
            
    def countdown(self, seconds):
        if seconds <= 0:
            self.destroy()
        else:
            self.btn_update.config(text=f"Closing in {seconds}s")
            self.after(1000, lambda: self.countdown(seconds - 1))

if __name__ == "__main__":
    app = UpdaterApp()
    app.mainloop()
