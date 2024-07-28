import pyaudio
import speech_recognition as sr
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import threading
import os

class SmartBracelet:
    def __init__(self):
        # Ana pencereyi oluştur ve başlık ve boyutunu ayarla
        self.root = tk.Tk()
        self.root.title("Akıllı Bileklik")
        self.root.geometry("600x400")
        self.root.configure(bg='#fbfcfd')

        self.microphone_on = False  # Mikrofonun açık olup olmadığını kontrol eder
        self.vibration_on = False   # Titreşimin açık olup olmadığını kontrol eder
        self.animating = False      # Animasyonun oynatılıp oynatılmadığını kontrol eder

        self.create_widgets()
        self.update_time()

    def create_widgets(self):
        # Zaman etiketi
        self.time_label = ttk.Label(self.root, text="", font=("Poppins", 48), background='#fbfcfd', foreground='#05556F')
        self.time_label.pack(pady=10)

        # Mikrofon açma/kapama düğmesi
        self.toggle_button = tk.Button(self.root, text="Mikrofonu Aç", command=self.toggle_microphone, bg='#93a7a6', fg='#fbfcfd', font=("Helvetica", 12))
        self.toggle_button.pack(pady=10)

        # Bilgi etiketi
        self.info_label = ttk.Label(self.root, text="Ses algılanmadı.", font=("Helvetica", 12), background='#fbfcfd', foreground='#05556F')
        self.info_label.pack(pady=10)

        # Animasyon için canvas
        self.canvas = tk.Canvas(self.root, width=400, height=300, bg='#fbfcfd', highlightthickness=0)
        self.canvas.pack(pady=10)

        # Metin çıktısı etiketi
        self.text_output = ttk.Label(self.root, text="", font=("Helvetica", 12), wraplength=400, background='#fbfcfd', foreground='#05556F')
        self.text_output.pack(pady=10)

    def update_time(self):
        # Mikrofon kapalıysa zamanı günceller
        if not self.microphone_on:
            current_time = time.strftime("%H:%M:%S")
            self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)  # 1 saniyede bir günceller

    def toggle_microphone(self):
        # Mikrofonun açık/kapalı durumunu değiştirir
        self.microphone_on = not self.microphone_on
        if self.microphone_on:
            self.toggle_button.config(text="Mikrofonu Kapat")
            self.start_listening()
        else:
            self.toggle_button.config(text="Mikrofonu Aç")
            self.info_label.config(text="Ses algılanmadı.")
            self.stop_animation()

    def start_listening(self):
        # Ses dinleme işlevi
        def listen():
            recognizer = sr.Recognizer()
            mic = sr.Microphone()

            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                self.info_label.config(text="Dinliyor...")
                audio = recognizer.listen(source)

                try:
                    text = recognizer.recognize_google(audio, language="tr-TR")
                    self.info_label.config(text=f"Algılanan ses: {text}")
                    self.text_output.config(text=text)
                    self.start_animation(text)
                    self.root.after(3000, self.stop_animation)  # 3 saniye sonra animasyonu durdur
                except sr.UnknownValueError:
                    self.info_label.config(text="Ses anlaşılamadı.")
                except sr.RequestError as e:
                    self.info_label.config(text=f"Google API hatası: {e}")

        # Dinleme işlemini ayrı bir iş parçacığında başlatır
        if self.microphone_on:
            listening_thread = threading.Thread(target=listen)
            listening_thread.start()

    def start_animation(self, text):
        # Animasyonu başlatır
        self.animating = True
        self.animate(text, 0)

    def stop_animation(self):
        # Animasyonu durdurur
        self.animating = False
        self.canvas.delete("all")

    def animate(self, text, frame):
        # Animasyon çerçevelerini oynatır
        if not self.animating:
            return

        frame_path = f"images/{text}{frame + 1}.gif"
        if os.path.exists(frame_path):
            image = Image.open(frame_path)
            photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas.image = photo

            next_frame = frame + 1
            self.root.after(100, self.animate, text, next_frame)  # 100 ms sonra bir sonraki çerçeve

if __name__ == "__main__":
    smart_bracelet = SmartBracelet()
    smart_bracelet.root.mainloop()
