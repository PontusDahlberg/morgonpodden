#!/usr/bin/env python3
"""
Grafisk musikredigerare för att skapa bryggor, intron och outros
Med timeline och drag-reglage för att välja korta utdrag ur längre låtar
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import json
import os
from pydub import AudioSegment
from pydub.playback import play
import threading
import time
import uuid

class MusicClipEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎵 Musikklipp-editor - Skapa bryggmusik")
        self.root.geometry("1000x900")  # Öka till 900px så alla kontroller syns bekvämt
        
        # Audio-variabler
        self.current_audio = None
        self.audio_file_path = None
        self.audio_data = None
        self.sample_rate = 44100
        self.duration = 0
        
        # Urvals-variabler
        self.selection_start = 0
        self.selection_end = 5  # 5 sekunder default
        self.playing = False
        
        # Waveform-plot
        self.figure = Figure(figsize=(12, 4), dpi=80)
        self.ax = self.figure.add_subplot(111)
        
        # Initialisera pygame med bättre inställningar
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(8)
            self.audio_enabled = True
            print("✅ Audio initialiserat")
        except Exception as e:
            self.audio_enabled = False
            print(f"⚠️ Audio playback not available: {e}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Skapa användargränssnitt"""
        # Huvudframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titel
        title_label = ttk.Label(main_frame, text="🎵 Musikklipp-editor", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Filval
        file_frame = ttk.LabelFrame(main_frame, text="Välj musikfil", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_label = ttk.Label(file_frame, text="Ingen fil vald")
        self.file_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(file_frame, text="📁 Välj fil", command=self.load_audio_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="▶️ Spela hela", command=self.play_full_audio).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="🎵 Öppna i spelare", command=self.open_in_player).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="⏹️ Stopp", command=self.stop_audio).pack(side=tk.LEFT)
        
        # Waveform och timeline (begränsad höjd så resten syns)
        waveform_frame = ttk.LabelFrame(main_frame, text="Audio-timeline", padding="10")
        waveform_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Canvas för matplotlib (fast höjd)
        self.canvas = FigureCanvasTkAgg(self.figure, waveform_frame)
        self.canvas.get_tk_widget().pack(fill=tk.X, pady=(0, 10))
        
        # Urvalskontroller
        selection_frame = ttk.LabelFrame(main_frame, text="Urval för klipp", padding="10")
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Start-tid
        ttk.Label(selection_frame, text="Start (sekunder):").grid(row=0, column=0, padx=(0, 5))
        self.start_var = tk.DoubleVar(value=0.0)
        self.start_scale = ttk.Scale(selection_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                   variable=self.start_var, command=self.on_start_change, length=200)
        self.start_scale.grid(row=0, column=1, padx=5)
        self.start_label = ttk.Label(selection_frame, text="0.0s")
        self.start_label.grid(row=0, column=2, padx=5)
        
        # Slut-tid
        ttk.Label(selection_frame, text="Slut (sekunder):").grid(row=1, column=0, padx=(0, 5))
        self.end_var = tk.DoubleVar(value=5.0)
        self.end_scale = ttk.Scale(selection_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                 variable=self.end_var, command=self.on_end_change, length=200)
        self.end_scale.grid(row=1, column=1, padx=5)
        self.end_label = ttk.Label(selection_frame, text="5.0s")
        self.end_label.grid(row=1, column=2, padx=5)
        
        # Längd
        ttk.Label(selection_frame, text="Längd:").grid(row=2, column=0, padx=(0, 5))
        self.length_label = ttk.Label(selection_frame, text="5.0s", font=("Arial", 10, "bold"))
        self.length_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Snabbval för vanliga längder
        quick_frame = ttk.Frame(selection_frame)
        quick_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Label(quick_frame, text="Snabbval:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(quick_frame, text="3s intro", command=lambda: self.set_length(3)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="4s brygga", command=lambda: self.set_length(4)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="5s brygga", command=lambda: self.set_length(5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="8s intro", command=lambda: self.set_length(8)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="10s outro", command=lambda: self.set_length(10)).pack(side=tk.LEFT, padx=2)
        
        # Uppspelningskontroller
        playback_frame = ttk.LabelFrame(main_frame, text="Testa urval", padding="10")
        playback_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(playback_frame, text="▶️ Spela urval", command=self.play_selection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(playback_frame, text="🔁 Loopa urval", command=self.loop_selection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(playback_frame, text="⏹️ Stopp", command=self.stop_audio).pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress för uppspelning
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(playback_frame, variable=self.progress_var, length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=(10, 0))
        
        # Spara-sektion
        save_frame = ttk.LabelFrame(main_frame, text="Spara klipp", padding="10")
        save_frame.pack(fill=tk.X)
        
        # Metadata för klipp
        ttk.Label(save_frame, text="Titel:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.title_var = tk.StringVar()
        ttk.Entry(save_frame, textvariable=self.title_var, width=30).grid(row=0, column=1, padx=5)
        
        ttk.Label(save_frame, text="Typ:").grid(row=0, column=2, padx=(10, 5))
        self.type_var = tk.StringVar(value="transition")
        type_combo = ttk.Combobox(save_frame, textvariable=self.type_var, width=15,
                                values=["intro", "transition", "outro", "news", "tech", "weather"])
        type_combo.grid(row=0, column=3, padx=5)
        
        ttk.Label(save_frame, text="Stämning:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.mood_var = tk.StringVar(value="upbeat")
        mood_combo = ttk.Combobox(save_frame, textvariable=self.mood_var, width=15,
                                values=["upbeat", "calm", "serious", "playful", "dramatic", "mysterious"])
        mood_combo.grid(row=1, column=1, padx=5)
        
        ttk.Label(save_frame, text="Beskrivning:").grid(row=1, column=2, padx=(10, 5))
        self.desc_var = tk.StringVar()
        ttk.Entry(save_frame, textvariable=self.desc_var, width=30).grid(row=1, column=3, padx=5)
        
        # Spara-knappar
        button_frame = ttk.Frame(save_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        
        ttk.Button(button_frame, text="💾 Spara klipp", command=self.save_clip).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="📝 Lägg till i bibliotek", command=self.add_to_library).pack(side=tk.LEFT)
    
    def load_audio_file(self):
        """Ladda audio-fil"""
        file_path = filedialog.askopenfilename(
            title="Välj musikfil",
            filetypes=[("Audio files", "*.mp3 *.wav *.ogg *.m4a"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Ladda med pydub
            self.current_audio = AudioSegment.from_file(file_path)
            self.audio_file_path = file_path
            self.duration = len(self.current_audio) / 1000.0  # sekunder
            
            # Uppdatera UI
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"📄 {filename} ({self.duration:.1f}s)")
            
            # Sätt sliders
            self.start_scale.configure(to=self.duration)
            self.end_scale.configure(to=self.duration)
            
            # Sätt auto-titel
            name_without_ext = os.path.splitext(filename)[0]
            self.title_var.set(f"{name_without_ext}_clip")
            
            # Rita waveform
            self.plot_waveform()
            self.update_selection_display()
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte ladda audiofil: {e}")
    
    def plot_waveform(self):
        """Rita waveform av audio"""
        if not self.current_audio:
            return
        
        try:
            # Konvertera till numpy array (sampla ned för snabbare rendering)
            samples = self.current_audio.get_array_of_samples()
            if self.current_audio.channels == 2:
                samples = np.array(samples).reshape((-1, 2))
                samples = samples.mean(axis=1)  # Mono
            else:
                samples = np.array(samples)
            
            # Sampla ned för visualisering
            step = max(1, len(samples) // 2000)  # Max 2000 punkter
            samples = samples[::step]
            
            # Tidsskala
            time_axis = np.linspace(0, self.duration, len(samples))
            
            # Rensa och plotta
            self.ax.clear()
            self.ax.plot(time_axis, samples, color='blue', linewidth=0.5)
            self.ax.set_xlabel('Tid (sekunder)')
            self.ax.set_ylabel('Amplitud')
            self.ax.set_title('Audio Waveform')
            self.ax.grid(True, alpha=0.3)
            
            # Sätt rätt x-axel gränser
            self.ax.set_xlim(0, self.duration)
            
        except Exception as e:
            print(f"Kunde inte rita waveform: {e}")
    
    def update_selection_display(self):
        """Uppdatera visuellt urval"""
        if not self.current_audio:
            return
        
        start = self.start_var.get()
        end = self.end_var.get()
        
        # Rensa plottet och rita om allt
        self.plot_waveform()
        
        # Rita urval som skuggat område
        self.ax.axvspan(start, end, alpha=0.3, color='red', label='Urval')
        
        # Uppdatera labels
        self.start_label.config(text=f"{start:.1f}s")
        self.end_label.config(text=f"{end:.1f}s")
        self.length_label.config(text=f"{end-start:.1f}s")
        
        self.canvas.draw()
    
    def on_selection_change(self, event=None):
        """Callback när urval ändras"""
        start = self.start_var.get()
        end = self.end_var.get()
        
        # Se till att start < end
        if start >= end:
            if start >= end:
                self.end_var.set(start + 1)
        
        self.update_selection_display()
    
    def on_start_change(self, event=None):
        """Callback när start-tid ändras"""
        start = self.start_var.get()
        end = self.end_var.get()
        
        # Se till att start < end
        if start >= end:
            self.end_var.set(start + 1)
        
        self.update_selection_display()
        print(f"Start ändrad till: {start:.1f}s")
    
    def on_end_change(self, event=None):
        """Callback när slut-tid ändras"""
        start = self.start_var.get()
        end = self.end_var.get()
        
        # Se till att start < end
        if end <= start:
            self.start_var.set(max(0, end - 1))
        
        self.update_selection_display()
        print(f"Slut ändrad till: {end:.1f}s")
    
    def set_length(self, length_seconds):
        """Sätt urval till specifik längd"""
        start = self.start_var.get()
        new_end = start + length_seconds
        
        if new_end > self.duration:
            # Flytta start bakåt istället
            new_start = max(0, self.duration - length_seconds)
            self.start_var.set(new_start)
            self.end_var.set(new_start + length_seconds)
        else:
            self.end_var.set(new_end)
        
        # Tvinga uppdatering av display
        self.update_selection_display()
        print(f"Satt längd till {length_seconds}s: {self.start_var.get():.1f}-{self.end_var.get():.1f}")
    
    def play_full_audio(self):
        """Spela hela audio-filen"""
        if not self.current_audio:
            messagebox.showwarning("Audio", "Ingen fil laddad")
            return
        
        if not self.audio_enabled:
            messagebox.showwarning("Audio", "Audio inte tillgängligt - försök med Windows Media Player")
            # Alternativ: öppna i systemets standard player
            try:
                os.startfile(self.audio_file_path)
            except:
                pass
            return
        
        try:
            # Stoppa eventuell pågående audio
            pygame.mixer.music.stop()
            
            # Ladda och spela
            pygame.mixer.music.load(self.audio_file_path)
            pygame.mixer.music.play()
            
            messagebox.showinfo("Spelar", f"Spelar: {os.path.basename(self.audio_file_path)}")
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spela audio: {e}\n\nFörsök öppna filen direkt.")
            # Fallback: öppna i systemets player
            try:
                os.startfile(self.audio_file_path)
            except:
                pass
    
    def play_selection(self):
        """Spela valt urval"""
        print("🎵 PLAY_SELECTION ANROPAD")
        
        if not self.current_audio:
            print("❌ Ingen fil laddad")
            messagebox.showwarning("Audio", "Ingen fil laddad")
            return
        
        start = self.start_var.get()
        end = self.end_var.get()
        print(f"🎯 Urval: {start:.1f}s - {end:.1f}s (längd: {end-start:.1f}s)")
        
        try:
            start_ms = int(start * 1000)
            end_ms = int(end * 1000)
            print(f"📏 Millisekunder: {start_ms}ms - {end_ms}ms")
            
            # Extrahera urval
            selection = self.current_audio[start_ms:end_ms]
            selection_length = len(selection) / 1000.0
            print(f"✂️ Urval extraherat: {selection_length:.1f}s")
            
            # Spara till temp-fil
            temp_file = os.path.join(os.getcwd(), "temp_selection.mp3")
            print(f"💾 Sparar till: {temp_file}")
            
            selection.export(temp_file, format="mp3", bitrate="128k")
            print(f"✅ Temp-fil skapad: {os.path.exists(temp_file)}")
            
            # Visa bekräftelse innan uppspelning
            messagebox.showinfo("Spelar urval", 
                f"Spelar {selection_length:.1f}s från {start:.1f}s till {end:.1f}s")
            
            # Prova pygame först
            try:
                print("🎮 Försöker pygame...")
                pygame.mixer.music.stop()
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                print("✅ Pygame uppspelning startad")
                
            except Exception as pygame_error:
                print(f"❌ Pygame fel: {pygame_error}")
                print("🔄 Försöker systemspelare...")
                os.startfile(temp_file)
                print("✅ Systemspelare öppnad")
            
        except Exception as e:
            print(f"💥 STOR FEL: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Fel", f"Kunde inte spela urval: {e}")
    
    def loop_selection(self):
        """Loopa valt urval"""
        if not self.current_audio:
            messagebox.showwarning("Audio", "Ingen fil laddad")
            return
        
        try:
            start_ms = int(self.start_var.get() * 1000)
            end_ms = int(self.end_var.get() * 1000)
            
            # Extrahera urval
            selection = self.current_audio[start_ms:end_ms]
            
            if not self.audio_enabled:
                messagebox.showinfo("Loop", "Audio-loop inte tillgängligt. Använd 'Spela urval' flera gånger.")
                return
            
            # Skapa loop genom att upprepa urval
            loop_audio = selection * 3  # 3 upprepningar
            
            # Spara till temp-fil
            temp_file = "temp_loop.mp3"
            loop_audio.export(temp_file, format="mp3")
            
            # Spela med pygame
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            duration = (self.end_var.get() - self.start_var.get()) * 3
            messagebox.showinfo("Loopar", f"Spelar urval 3 gånger ({duration:.1f} sekunder)")
            
            # Städa upp
            def cleanup():
                time.sleep(duration + 2)
                try:
                    os.remove(temp_file)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte loopa urval: {e}")
    
    def stop_audio(self):
        """Stoppa audio"""
        try:
            if self.audio_enabled:
                pygame.mixer.music.stop()
            
            # Försök även städa upp temp-filer
            for temp_file in ["temp_selection.mp3", "temp_loop.mp3"]:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
        except Exception as e:
            print(f"Fel vid stopp: {e}")
    
    def open_in_player(self):
        """Öppna aktuell fil i systemets spelare"""
        if not self.audio_file_path:
            messagebox.showwarning("Öppna", "Ingen fil laddad")
            return
        
        try:
            os.startfile(self.audio_file_path)
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte öppna fil: {e}")
    
    def save_clip(self):
        """Spara valt klipp som fil"""
        if not self.current_audio:
            messagebox.showwarning("Spara", "Ingen fil laddad")
            return
        
        if not self.title_var.get().strip():
            messagebox.showerror("Fel", "Titel måste anges")
            return
        
        try:
            start_ms = int(self.start_var.get() * 1000)
            end_ms = int(self.end_var.get() * 1000)
            
            # Extrahera urval
            selection = self.current_audio[start_ms:end_ms]
            
            # Skapa filnamn
            safe_title = "".join(c for c in self.title_var.get() if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.mp3"
            
            # Se till att audio-mappen finns
            audio_dir = "audio"
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
            
            filepath = os.path.join(audio_dir, filename)
            
            # Spara klipp
            selection.export(filepath, format="mp3")
            
            messagebox.showinfo("Sparat", f"Klipp sparat som:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara klipp: {e}")
    
    def add_to_library(self):
        """Lägg till klipp i musikbiblioteket"""
        if not self.current_audio:
            messagebox.showwarning("Bibliotek", "Ingen fil laddad")
            return
        
        if not self.title_var.get().strip():
            messagebox.showerror("Fel", "Titel måste anges")
            return
        
        try:
            # Spara klipp först
            self.save_clip()
            
            # Ladda musikbibliotek
            try:
                with open("music_library.json", 'r', encoding='utf-8') as f:
                    library = json.load(f)
            except FileNotFoundError:
                library = {"tracks": {}, "categories": {}, "moods": {}}
            
            # Skapa track-info
            safe_title = "".join(c for c in self.title_var.get() if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.mp3"
            filepath = os.path.join("audio", filename)
            
            track_id = str(uuid.uuid4())[:8]
            
            track_info = {
                "id": track_id,
                "title": self.title_var.get().strip(),
                "artist": "Klippt från " + os.path.basename(self.audio_file_path),
                "filename": filename,
                "path": filepath,
                "categories": [self.type_var.get()],
                "moods": [self.mood_var.get()],
                "description": self.desc_var.get().strip() or f"Klipp från {self.start_var.get():.1f}s-{self.end_var.get():.1f}s",
                "duration": self.end_var.get() - self.start_var.get(),
                "created_from": self.audio_file_path,
                "clip_start": self.start_var.get(),
                "clip_end": self.end_var.get()
            }
            
            # Lägg till i bibliotek
            library["tracks"][track_id] = track_info
            
            # Spara bibliotek
            with open("music_library.json", 'w', encoding='utf-8') as f:
                json.dump(library, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Tillagt", f"Klipp tillagt i musikbibliotek!\nKan nu användas som {self.type_var.get()}-musik")
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte lägga till i bibliotek: {e}")
    
    def run(self):
        """Starta applikationen"""
        self.root.mainloop()

def main():
    """Huvudfunktion"""
    app = MusicClipEditor()
    app.run()

if __name__ == "__main__":
    main()
