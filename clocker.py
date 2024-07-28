import tkinter as tk
from tkinter import messagebox
import json
import datetime
import time
current_time = int(time.time())
print(current_time)

class ClockerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clocker")
        self.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        self.time_label = tk.Label(self, text="", font=("Helvetica", 48))
        self.time_label.pack(pady=20)

        self.date_label = tk.Label(self, text="", font=("Helvetica", 32))
        self.date_label.pack(pady=10)

        self.weather_label = tk.Label(self, text="", font=("Helvetica", 24))
        self.weather_label.pack(pady=10)

        self.refresh_button = tk.Button(self, text="Refresh", command=self.refresh_data)
        self.refresh_button.pack(pady=10)

        self.refresh_data()

    def refresh_data(self):
        self.update_time()
        self.update_weather()

    def update_time(self):
        now = datetime.datetime.now()
        self.time_label.config(text=now.strftime("%H:%M"))
        self.date_label.config(text=now.strftime("%Y-%m-%d %A"))

    def update_weather(self):
        try:
            with open('weather.json', 'r') as file:
                weather_data = json.load(file)
                if int(time.time()) - weather_data['update'] > 2 * 3600:
                    raise ValueError("Weather data is outdated")
                weather_text = f"Weather: {weather_data['today_weather']}, {weather_data['current_temp']}°C"
                self.weather_label.config(text=weather_text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = ClockerApp()
    app.mainloop()
