import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import threading
import os
import sys

# --- Constants & Config ---
APP_TITLE = "Arch Auto-Updater"
WINDOW_SIZE = "950x600"
COLOR_BG = "#121212"
COLOR_FG = "#E0E0E0"
COLOR_ACCENT = "#1793D1"
COLOR_SUCCESS = "#4CAF50"
COLOR_ERROR = "#F44336"
COLOR_TERMINAL_BG = "#1E1E1E"
COLOR_TERMINAL_FG = "#00FF41"

class ArchUpdaterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)

        if not self.is_arch_linux():
            messagebox.showerror("OS Error", "This application is designed specifically for Arch Linux.")
            self.destroy()
            return

        self.setup_ui()
        self.detect_aur_helper()

    def is_arch_linux(self):
        return os.path.exists("/etc/arch-release")

    def detect_aur_helper(self):
        self.aur_helper = None
        for helper in ["yay", "paru"]:
            if subprocess.run(["which", helper], capture_output=True).returncode == 0:
                self.aur_helper = helper
                break
        
        status = f"Using: pacman" + (f" + {self.aur_helper}" if self.aur_helper else "")
        self.lbl_helper_status.config(text=status)

    def setup_ui(self):
        # Header
        self.header_frame = tk.Frame(self, bg=COLOR_BG, height=80)
        self.header_frame.pack(fill="x", pady=(20, 10))

        self.lbl_title = tk.Label(
            self.header_frame, text="ARCH SYSTEM UPDATER", 
            font=("Segoe UI", 28, "bold"), bg=COLOR_BG, fg=COLOR_ACCENT
        )
        self.lbl_title.pack()

        self.lbl_helper_status = tk.Label(
            self.header_frame, text="Detecting system state...", 
            font=("Segoe UI", 10), bg=COLOR_BG, fg="#888888"
        )
        self.lbl_helper_status.pack()

        # Layout container
        self.main_container = tk.Frame(self, bg=COLOR_BG)
        self.main_container.pack(fill="both", expand=True, padx=40, pady=10)

        # Left: Commands & Status
        self.left_side = tk.Frame(self.main_container, bg=COLOR_BG)
        self.left_side.pack(side="left", fill="both", expand=True)

        self.lbl_status = tk.Label(
            self.left_side, text="System Ready", font=("Segoe UI", 14), bg=COLOR_BG, fg=COLOR_FG
        )
        self.lbl_status.pack(anchor="w", pady=(20, 5))

        self.progress_canvas = tk.Canvas(self.left_side, height=12, bg="#333333", highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=10)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 12, fill=COLOR_ACCENT, width=0)

        self.btn_update = tk.Button(
            self.left_side, text="UPDATE SYSTEM", command=self.start_update_thread,
            bg=COLOR_ACCENT, fg="white", font=("Segoe UI", 12, "bold"),
            relief="flat", cursor="hand2", padx=30, pady=10
        )
        self.btn_update.pack(pady=30)

        # License Button
        self.btn_license = tk.Button(
            self.left_side, text="VIEW LICENSE", command=self.show_license,
            bg=COLOR_BG, fg="#888888", font=("Segoe UI", 9),
            relief="flat", cursor="hand2", activebackground=COLOR_BG, activeforeground=COLOR_ACCENT
        )
        self.btn_license.pack(side="bottom", anchor="w", pady=10)

        # Right: Logs
        self.right_side = tk.Frame(self.main_container, bg=COLOR_BG)
        self.right_side.pack(side="right", fill="both", expand=True, padx=(20, 0))

        self.log_area = scrolledtext.ScrolledText(
            self.right_side, bg=COLOR_TERMINAL_BG, fg=COLOR_TERMINAL_FG,
            font=("Consolas", 10), borderwidth=0, highlightthickness=1,
            highlightbackground="#444444"
        )
        self.log_area.pack(fill="both", expand=True)
        self.log_area.config(state="disabled")

        self.footer = tk.Label(
            self, text="Built for Arch Linux • Premium & Secure", font=("Segoe UI", 8), bg=COLOR_BG, fg="#555555"
        )
        self.footer.pack(side="bottom", pady=10)

    def show_license(self):
        try:
            with open("LICENSE", "r") as f:
                content = f.read()
            
            # Simple custom dialog for license
            win = tk.Toplevel(self)
            win.title("Project License")
            win.geometry("600x500")
            win.configure(bg=COLOR_BG)
            
            t = scrolledtext.ScrolledText(win, bg=COLOR_TERMINAL_BG, fg=COLOR_FG, font=("Consolas", 10))
            t.pack(fill="both", expand=True, padx=20, pady=20)
            t.insert("end", content)
            t.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not read LICENSE: {e}")

    def log(self, message):
        self.log_area.config(state="normal")
        self.log_area.insert("end", f"{message}\n")
        self.log_area.see("end")
        self.log_area.config(state="disabled")

    def update_progress(self, percent):
        canvas_width = self.progress_canvas.winfo_width()
        self.progress_canvas.coords(self.progress_bar, 0, 0, (percent / 100) * canvas_width, 12)

    def start_update_thread(self):
        self.btn_update.config(state="disabled", text="UPDATING...")
        self.lbl_status.config(text="Initializing...", fg=COLOR_FG)
        thread = threading.Thread(target=self.run_updates, daemon=True)
        thread.start()

    def run_updates(self):
        # 1. Sync
        self.update_progress(20)
        self.lbl_status.config(text="Checking for updates...")
        self.log(">>> [1/3] Refreshing package databases...")
        
        success = self.execute_cmd(["pkexec", "pacman", "-Sy"])
        if not success:
            self.handle_failure("Failed to sync databases. Check internet or authentication.")
            return

        # 2. Upgrade
        self.update_progress(40)
        self.lbl_status.config(text="Preparing system upgrade...")
        self.log("\n>>> [2/3] Resolving package upgrades...")
        
        # We try to detect conflicts and handle them
        success = self.execute_cmd(["pkexec", "pacman", "-Su", "--noconfirm"])
        
        if not success:
            # We might have a conflict that --noconfirm couldn't handle
            self.log("\n[!] Standard upgrade failed. Checking for conflicts...")
            # Detect conflicts by running again WITHOUT noconfirm but for preparation only
            # Re-running with interactive mode for the user via terminal could be better
            # But for now, we'll suggest manual intervention or parsing errors
            self.handle_failure("Conflict or error detected during upgrade. Check the log.")
            return

        # 3. AUR
        self.update_progress(70)
        if self.aur_helper:
            self.lbl_status.config(text=f"Updating AUR ({self.aur_helper})...")
            self.log(f"\n>>> [3/3] Scanning {self.aur_helper}...")
            # AUR helpers handle their own sudo
            self.execute_cmd([self.aur_helper, "-Sua", "--noconfirm"])
        else:
            self.log("\n>>> [3/3] No AUR helper. Skipping AUR updates.")

        self.update_progress(100)
        self.lbl_status.config(text="Deployment Complete!", fg=COLOR_SUCCESS)
        self.log("\n[DONE] Your system is fully updated.")
        self.after(0, self.finish_ui)

    def execute_cmd(self, cmd_list):
        try:
            # Note: subprocess.PIPE can sometimes hang if buffers are full and we don't read fast enough
            # but bufsize=1 and text mode should be okay for pacman's throughput.
            process = subprocess.Popen(
                cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, bufsize=1, universal_newlines=True, stdin=subprocess.PIPE
            )
            
            error_detected = False
            for line in process.stdout:
                line_striped = line.strip()
                self.log(f"  {line_striped}")
                
                # Conflict detection
                if "conflict" in line_striped.lower() or "unresolvable" in line_striped.lower():
                    error_detected = True
                    # If we detect a conflict, we might need to ask the user
                    # In this lightweight app, we'll log it clearly and let the user see it
                
                # Dependency replace? (Pacman usually asks this)
                # With --noconfirm, pacman automatically replaces if it's the expected behavior.
            
            process.wait()
            return process.returncode == 0 and not error_detected
        except Exception as e:
            self.log(f"Subprocess Error: {e}")
            return False

    def handle_failure(self, msg):
        self.log(f"\n[FATAL] {msg}")
        self.lbl_status.config(text="Update Blocked", fg=COLOR_ERROR)
        self.btn_update.config(state="normal", text="VIEW ERRORS")
        # Suggest manual terminal run if conflict
        self.log("\n[TIP] If you see 'conflicting dependencies', try running 'sudo pacman -Su' in a terminal.")

    def finish_ui(self):
        self.btn_update.config(state="normal", text="SYSTEM UPDATED")
        self.after(5000, lambda: self.btn_update.config(text="RE-SCAN"))

if __name__ == "__main__":
    app = ArchUpdaterApp()
    app.mainloop()
