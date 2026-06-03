import tkinter as tk
from datetime import datetime
import subprocess
import atexit

DATA_FILE = "gps_log.txt"

# --- MILITARY COLOR PALETTE ---
BG_COLOR = "#0a0a0a"
FG_NORMAL = "#00ff00"
FG_WARNING = "#ffff00"
FG_CRITICAL = "#ff0000"
FG_ALERT = "#ff00ff"
FG_BLUE = "#00ffff"

class NavalIDSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Naval GNSS Intrusion Detection System (IDS)")
        self.root.geometry("800x400")
        self.root.configure(bg=BG_COLOR)
        
        self.base_lat = None
        self.base_lon = None
        
        # Variable to track the current alarm state
        self.current_audio_state = "NORMAL"
        self.audio_process = None
        self.build_ui()
        self.update_system()
        
        # This protocol ensures the audio stops when closing the window via the UI
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def build_ui(self):
        header = tk.Label(self.root, text="NAVAL COMMAND & CONTROL - GNSS MONITOR", 
                          font=("Courier", 20, "bold"), bg=BG_COLOR, fg=FG_BLUE)
        header.pack(pady=20)
        
        self.status_banner = tk.Label(self.root, text="INITIALIZING...", 
                                      font=("Courier", 24, "bold"), bg="#333333", fg="white", width=40, pady=10)
        self.status_banner.pack(pady=20)
        
        data_frame = tk.Frame(self.root, bg=BG_COLOR)
        data_frame.pack(pady=10)
        
        self.cn0_label = tk.Label(data_frame, text="C/N0: -- dB-Hz", font=("Courier", 16), bg=BG_COLOR, fg=FG_NORMAL)
        self.cn0_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")
        
        self.sog_label = tk.Label(data_frame, text="SOG: -- Kt", font=("Courier", 16), bg=BG_COLOR, fg=FG_NORMAL)
        self.sog_label.grid(row=0, column=1, padx=20, pady=5, sticky="w")
        
        self.pos_label = tk.Label(data_frame, text="Pos: --, --", font=("Courier", 16), bg=BG_COLOR, fg=FG_NORMAL)
        self.pos_label.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        self.time_label = tk.Label(data_frame, text="Time (UTC): --", font=("Courier", 16), bg=BG_COLOR, fg=FG_NORMAL)
        self.time_label.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")

    def trigger_audio_alarm(self, attack_category):
        # Check if the state has changed to prevent redundant process execution
        if self.current_audio_state != attack_category:
            self.current_audio_state = attack_category
            
            # If an audio process is already running, terminate it gracefully
            if self.audio_process is not None:
                self.audio_process.terminate()
                self.audio_process = None
                
            # Start the alarm in an infinite loop using a shell subprocess
            if attack_category == "JAMMING":
                self.audio_process = subprocess.Popen(["sh", "-c", "while true; do aplay -q jamming_alarm.wav; done"])
            elif attack_category == "SPOOFING":
                self.audio_process = subprocess.Popen(["sh", "-c", "while true; do aplay -q spoofing_alarm.wav; done"])

    def read_gps_data(self):
        cn0, sog, lat, lon = 0, 0, 0.0, 0.0
        timestamp_str = "1970-01-01 00:00:00"
        try:
            with open(DATA_FILE, "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if "CN0=" in line: cn0 = int(line.split("=")[1])
                    elif "SOG=" in line: sog = int(line.split("=")[1])
                    elif "Lat=" in line: lat = float(line.split("=")[1])
                    elif "Lon=" in line: lon = float(line.split("=")[1])
                    elif "Time=" in line: timestamp_str = line.split("=")[1]
        except:
            pass 
        return cn0, sog, lat, lon, timestamp_str

    def update_system(self):
        cn0, sog, lat, lon, timestamp_str = self.read_gps_data()
        system_time = datetime.utcnow()
        
        if self.base_lat is None and lat != 0.0:
            self.base_lat = lat
            self.base_lon = lon
        
        try:
            gps_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            time_diff_seconds = abs((system_time - gps_time).total_seconds())
        except ValueError:
            time_diff_seconds = 999999

        self.cn0_label.config(text=f"C/N0: {cn0} dB-Hz")
        self.sog_label.config(text=f"SOG: {sog} Kt")
        self.pos_label.config(text=f"Pos: {lat:.4f}, {lon:.4f}")
        self.time_label.config(text=f"Time (UTC): {timestamp_str}")

        # --- INDEPENDENT THREAT EVALUATION ---
        jamming_attack = (cn0 == 0)
        degraded_signal = (0 < cn0 < 35)
        
        # DEMO TOLERANCE: 172800 seconds = 48 hours (to accommodate playback of pre-recorded baseband files)
        time_spoofed = (time_diff_seconds > 172800) 
        
        kinematic_spoofed = (sog > 50)
        
        location_spoofed = False
        if self.base_lat is not None and (abs(lat - self.base_lat) > 0.05 or abs(lon - self.base_lon) > 0.05):
            location_spoofed = True

        # --- BANNER AND AUDIO DECISION LOGIC ---
        if jamming_attack:
            status_text = "[ CRITICAL ] RF JAMMING DETECTED!"
            status_bg = "#880000"
            status_fg = "white"
            self.trigger_audio_alarm("JAMMING")
            
        elif degraded_signal:
            status_text = "[ WARNING ] DEGRADED GNSS SIGNAL"
            status_bg = "#666600"
            status_fg = FG_WARNING
            self.trigger_audio_alarm("NORMAL")
            
        elif time_spoofed and location_spoofed:
            status_text = "[ CRITICAL ] HYBRID SPOOFING (TIME+POS)!"
            status_bg = "#4b0082" 
            status_fg = "white"
            self.trigger_audio_alarm("SPOOFING")
            
        elif time_spoofed:
            status_text = "[ ALERT ] TIME SPOOFING DETECTED!"
            status_bg = "#000088"
            status_fg = FG_BLUE
            self.trigger_audio_alarm("SPOOFING")
            
        elif location_spoofed:
            status_text = "[ ALERT ] POSITION SPOOFING DETECTED!"
            status_bg = "#ff4400" 
            status_fg = "white"
            self.trigger_audio_alarm("SPOOFING")
            
        elif kinematic_spoofed:
            status_text = f"[ ALERT ] KINEMATIC SPOOFING ({sog} Kt)!"
            status_bg = "#880088"
            status_fg = FG_ALERT
            self.trigger_audio_alarm("SPOOFING")
            
        else:
            status_text = "[ SYSTEM NORMAL ]"
            status_bg = "#004400" 
            status_fg = FG_NORMAL
            self.trigger_audio_alarm("NORMAL")

        self.status_banner.config(text=status_text, bg=status_bg, fg=status_fg)
        self.root.after(1000, self.update_system)

    def on_closing(self):
        # This function triggers upon the window close event
        if self.audio_process is not None:
            self.audio_process.terminate()
        # Forcefully kill any orphaned 'aplay' background processes
        subprocess.call(["pkill", "-f", "aplay"])
        self.root.destroy()

    def stop_audio_at_exit(self):
        # Fallback exit handler to ensure audio terminates upon Python exit
        if hasattr(self, 'audio_process') and self.audio_process is not None:
            self.audio_process.terminate()
        subprocess.call(["pkill", "-f", "aplay"])

if __name__ == "__main__":
    current_exact_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    initial_data = f"CN0=45\nSOG=15\nLat=44.1598\nLon=28.6348\nTime={current_exact_time}"
    with open(DATA_FILE, "w") as f:
        f.write(initial_data)

    root = tk.Tk()
    app = NavalIDSApp(root)
    atexit.register(app.stop_audio_at_exit)
    root.mainloop()
