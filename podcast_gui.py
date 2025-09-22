#!/usr/bin/env python3
"""
GUI för komplett podcastgenerering av Människa Maskin Miljö
Alla steg från val av källor till färdig podcast i ett gränssnitt
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
import threading
from typing import Dict, List
import subprocess
from datetime import datetime
import pygame
from dotenv import load_dotenv

# Ladda environment variables
load_dotenv()

class PodcastGeneratorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Människa Maskin Miljö - Podcastgenerator")
        self.root.geometry("900x700")
        
        # Variabler för konfiguration
        self.sources = self.load_sources()
        self.generation_running = False
        self.current_output = ""
        
        # Initialisera inställningsvariabler
        self.target_audience_var = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.tone_var = tk.StringVar()
        self.music_volume_var = tk.StringVar()
        self.bridge_duration_var = tk.StringVar()
        
        # Initialisera pygame för audio
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except:
            self.audio_enabled = False
        
        self.setup_ui()
        self.refresh_sources()
        self.load_settings()
    
    def load_sources(self) -> Dict:
        """Ladda källor från sources.json"""
        try:
            with open("sources.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "news_sources": [],
                "tech_sources": [],
                "weather_sources": []
            }
    
    def save_sources(self):
        """Spara källor till sources.json"""
        try:
            with open("sources.json", 'w', encoding='utf-8') as f:
                json.dump(self.sources, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara källor: {e}")
            return False
    
    def load_settings(self):
        """Ladda sparade inställningar"""
        try:
            with open("podcast_settings.json", 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            self.target_audience_var.set(settings.get("target_audience", "Morgonlyssnare, teknikintresserade"))
            self.duration_var.set(settings.get("duration", "8-12 minuter"))
            self.tone_var.set(settings.get("tone", "Professionell men avslappnad"))
            self.music_volume_var.set(settings.get("music_volume", "25"))
            self.bridge_duration_var.set(settings.get("bridge_duration", "3-5"))
            
        except FileNotFoundError:
            # Sätt standardvärden
            self.target_audience_var.set("Morgonlyssnare, teknikintresserade")
            self.duration_var.set("8-12 minuter")
            self.tone_var.set("Professionell men avslappnad")
            self.music_volume_var.set("25")
            self.bridge_duration_var.set("3-5")
        except Exception as e:
            print(f"Kunde inte ladda inställningar: {e}")
            # Sätt standardvärden vid fel
    
    def setup_ui(self):
        """Skapa användargränssnitt"""
        # Skapa notebook för tabbar
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Podcastgenerering
        self.create_generation_tab(notebook)
        
        # Tab 2: Källhantering
        self.create_sources_tab(notebook)
        
        # Tab 3: Musikhantering
        self.create_music_tab(notebook)
        
        # Tab 4: Inställningar
        self.create_settings_tab(notebook)
    
    def create_generation_tab(self, parent):
        """Skapa fliken för podcastgenerering"""
        frame = ttk.Frame(parent, padding="10")
        parent.add(frame, text="🎙️ Generera Podcast")
        
        # Titel
        title_label = ttk.Label(frame, text="Människa Maskin Miljö - Podcastgenerator", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Genereringsalternativ
        options_frame = ttk.LabelFrame(frame, text="Genereringsalternativ", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Checkbox för komponenter
        self.gen_intro_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Intro och väckarklocka", 
                       variable=self.gen_intro_var).grid(row=0, column=0, sticky=tk.W)
        
        self.gen_news_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Nyheter (svenska/internationella)", 
                       variable=self.gen_news_var).grid(row=1, column=0, sticky=tk.W)
        
        self.gen_tech_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Teknik och AI-nyheter", 
                       variable=self.gen_tech_var).grid(row=2, column=0, sticky=tk.W)
        
        self.gen_weather_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Väder och avslutning", 
                       variable=self.gen_weather_var).grid(row=3, column=0, sticky=tk.W)
        
        self.gen_music_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Musikbryggor mellan segment", 
                       variable=self.gen_music_var).grid(row=4, column=0, sticky=tk.W)
        
        # Röstinställningar
        voice_frame = ttk.LabelFrame(frame, text="Röstinställningar", padding="10")
        voice_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(voice_frame, text="Sanna (huvudröst):").grid(row=0, column=0, sticky=tk.W)
        self.sanna_voice_var = tk.StringVar(value="21m00Tcm4TlvDq8ikWAM")
        ttk.Entry(voice_frame, textvariable=self.sanna_voice_var, width=30).grid(row=0, column=1, padx=5)
        
        ttk.Label(voice_frame, text="George (kompletterande):").grid(row=1, column=0, sticky=tk.W)
        self.george_voice_var = tk.StringVar(value="JBFqnCBsd6RMkjVDRZzb")
        ttk.Entry(voice_frame, textvariable=self.george_voice_var, width=30).grid(row=1, column=1, padx=5)
        
        # Kontrolknappar
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.generate_button = ttk.Button(control_frame, text="🚀 Generera Podcast", 
                                        command=self.start_generation, style="Accent.TButton")
        self.generate_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stoppa", 
                                    command=self.stop_generation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.play_button = ttk.Button(control_frame, text="▶️ Spela senaste", 
                                    command=self.play_latest)
        self.play_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.open_folder_button = ttk.Button(control_frame, text="📁 Öppna mapp", 
                                           command=self.open_output_folder)
        self.open_folder_button.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Redo att generera podcast")
        ttk.Label(frame, textvariable=self.progress_var).pack(pady=(10, 5))
        
        self.progress_bar = ttk.Progressbar(frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Output-textbox
        output_frame = ttk.LabelFrame(frame, text="Genereringslog", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def create_sources_tab(self, parent):
        """Skapa fliken för källhantering"""
        frame = ttk.Frame(parent, padding="10")
        parent.add(frame, text="📰 Källor")
        
        # Titel
        ttk.Label(frame, text="Hantera nyhetskällor", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Källor per kategori
        categories = [
            ("news_sources", "Nyheter"),
            ("tech_sources", "Teknik/AI"),
            ("weather_sources", "Väder")
        ]
        
        for source_key, title in categories:
            self.create_source_section(frame, source_key, title)
    
    def create_source_section(self, parent, source_key: str, title: str):
        """Skapa sektion för en källkategori"""
        section_frame = ttk.LabelFrame(parent, text=title, padding="10")
        section_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Lista med källor
        sources_frame = ttk.Frame(section_frame)
        sources_frame.pack(fill=tk.X)
        
        # Listbox för källor
        listbox = tk.Listbox(sources_frame, height=4)
        listbox.pack(fill=tk.X, side=tk.LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(sources_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Spara referenser
        setattr(self, f"{source_key}_listbox", listbox)
        
        # Knappar
        button_frame = ttk.Frame(section_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        def add_source():
            self.add_source_dialog(source_key, title)
        
        def edit_source():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                self.edit_source_dialog(source_key, title, index)
        
        def remove_source():
            selection = listbox.curselection()
            if selection:
                if messagebox.askyesno("Bekräfta", "Ta bort vald källa?"):
                    index = selection[0]
                    del self.sources[source_key][index]
                    self.save_sources()
                    self.refresh_sources()
        
        ttk.Button(button_frame, text="Lägg till", command=add_source).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Redigera", command=edit_source).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Ta bort", command=remove_source).pack(side=tk.LEFT)
    
    def create_music_tab(self, parent):
        """Skapa fliken för musikhantering"""
        frame = ttk.Frame(parent, padding="10")
        parent.add(frame, text="🎵 Musik")
        
        ttk.Label(frame, text="Musikhantering", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Info text
        info_text = """Här kan du hantera musik som används för:
• Intro och outro
• Bryggor mellan segment
• Bakgrundsmusik

För detaljerad musikhantering, använd music_manager_gui.py"""
        
        ttk.Label(frame, text=info_text, justify=tk.LEFT).pack(pady=(0, 20))
        
        # Knapp för att öppna musikhanterare
        music_buttons_frame = ttk.Frame(frame)
        music_buttons_frame.pack(pady=20)
        
        ttk.Button(music_buttons_frame, text="🎵 Öppna musikhanterare", 
                  command=self.open_music_manager).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(music_buttons_frame, text="✂️ Musikklipp-editor", 
                  command=self.open_clip_editor).pack(side=tk.LEFT)
        
        # Snabbtest av musik
        test_frame = ttk.LabelFrame(frame, text="Snabbtest", padding="10")
        test_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(test_frame, text="🎵 Testa intro-musik", 
                  command=lambda: self.test_music("intro")).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="🎵 Testa bryggmusik", 
                  command=lambda: self.test_music("transition")).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="⏹️ Stoppa musik", 
                  command=self.stop_music).pack(side=tk.LEFT, padx=5)
    
    def create_settings_tab(self, parent):
        """Skapa fliken för inställningar"""
        frame = ttk.Frame(parent, padding="10")
        parent.add(frame, text="⚙️ Inställningar")
        
        ttk.Label(frame, text="Podcastinställningar", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # API-status (läs-endast)
        api_frame = ttk.LabelFrame(frame, text="API-status", padding="10")
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Kontrollera API-status
        elevenlabs_status = "✅ Konfigurerad" if os.getenv("ELEVENLABS_API_KEY") else "❌ Saknas"
        openrouter_status = "✅ Konfigurerad" if os.getenv("OPENROUTER_API_KEY") else "❌ Saknas"
        cloudflare_status = "✅ Konfigurerad" if os.getenv("CLOUDFLARE_R2_TOKEN") else "❌ Saknas"
        
        ttk.Label(api_frame, text=f"ElevenLabs API: {elevenlabs_status}").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(api_frame, text=f"OpenRouter API: {openrouter_status}").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(api_frame, text=f"Cloudflare R2: {cloudflare_status}").grid(row=2, column=0, sticky=tk.W, pady=2)
        
        info_label = ttk.Label(api_frame, text="💡 API-nycklar konfigureras i .env-filen", 
                             font=("Arial", 9), foreground="gray")
        info_label.grid(row=3, column=0, sticky=tk.W, pady=(10, 0))
        
        # Podcastinställningar
        podcast_frame = ttk.LabelFrame(frame, text="Podcastinställningar", padding="10")
        podcast_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(podcast_frame, text="Målgrupp:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.target_audience_var = tk.StringVar(value="Morgonlyssnare, teknikintresserade")
        ttk.Entry(podcast_frame, textvariable=self.target_audience_var, width=40).grid(row=0, column=1, padx=5)
        
        ttk.Label(podcast_frame, text="Podcast-längd:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.duration_var = tk.StringVar(value="8-12 minuter")
        ttk.Entry(podcast_frame, textvariable=self.duration_var, width=40).grid(row=1, column=1, padx=5)
        
        ttk.Label(podcast_frame, text="Ton och stil:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.tone_var = tk.StringVar(value="Professionell men avslappnad")
        ttk.Entry(podcast_frame, textvariable=self.tone_var, width=40).grid(row=2, column=1, padx=5)
        
        # Ljudinställningar
        audio_frame = ttk.LabelFrame(frame, text="Ljudinställningar", padding="10")
        audio_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(audio_frame, text="Musikvolym (%):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.music_volume_var = tk.StringVar(value="25")
        music_scale = ttk.Scale(audio_frame, from_=0, to=50, orient=tk.HORIZONTAL, 
                               variable=self.music_volume_var, length=200)
        music_scale.grid(row=0, column=1, padx=5)
        ttk.Label(audio_frame, textvariable=self.music_volume_var).grid(row=0, column=2, padx=5)
        
        ttk.Label(audio_frame, text="Bryggmusik-längd (sek):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.bridge_duration_var = tk.StringVar(value="3-5")
        ttk.Entry(audio_frame, textvariable=self.bridge_duration_var, width=20).grid(row=1, column=1, padx=5, sticky=tk.W)
        
        # Verktygsknappar
        tools_frame = ttk.LabelFrame(frame, text="Verktyg", padding="10")
        tools_frame.pack(fill=tk.X, pady=(0, 10))
        
        tools_button_frame = ttk.Frame(tools_frame)
        tools_button_frame.pack(fill=tk.X)
        
        ttk.Button(tools_button_frame, text="📁 Öppna .env-fil", 
                  command=self.open_env_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tools_button_frame, text="🔄 Uppdatera API-status", 
                  command=self.refresh_api_status).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tools_button_frame, text="🧹 Rensa gamla podcasts", 
                  command=self.cleanup_old_podcasts).pack(side=tk.LEFT, padx=(0, 10))
        
        # Spara inställningar
        ttk.Button(frame, text="💾 Spara inställningar", 
                  command=self.save_settings).pack(pady=20)
    
    def refresh_sources(self):
        """Uppdatera källlistorna"""
        for source_key in ["news_sources", "tech_sources", "weather_sources"]:
            listbox = getattr(self, f"{source_key}_listbox", None)
            if listbox:
                listbox.delete(0, tk.END)
                for source in self.sources.get(source_key, []):
                    display_text = f"{source.get('name', 'Okänd')} - {source.get('url', '')}"
                    listbox.insert(tk.END, display_text)
    
    def add_source_dialog(self, source_key: str, title: str):
        """Dialog för att lägga till källa"""
        self.source_dialog(source_key, title)
    
    def edit_source_dialog(self, source_key: str, title: str, index: int):
        """Dialog för att redigera källa"""
        source = self.sources[source_key][index]
        self.source_dialog(source_key, title, source, index)
    
    def source_dialog(self, source_key: str, title: str, source=None, index=None):
        """Generisk dialog för källa"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Redigera' if source else 'Lägg till'} källa - {title}")
        dialog.geometry("500x300")
        dialog.grab_set()
        
        # Fält
        ttk.Label(dialog, text="Namn:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar(value=source.get("name", "") if source else "")
        ttk.Entry(dialog, textvariable=name_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="URL:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        url_var = tk.StringVar(value=source.get("url", "") if source else "")
        ttk.Entry(dialog, textvariable=url_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Beskrivning:").grid(row=2, column=0, sticky=(tk.W, tk.N), padx=5, pady=5)
        desc_text = tk.Text(dialog, width=50, height=5)
        desc_text.grid(row=2, column=1, padx=5, pady=5)
        if source:
            desc_text.insert("1.0", source.get("description", ""))
        
        # Knappar
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def save_source():
            if not name_var.get().strip() or not url_var.get().strip():
                messagebox.showerror("Fel", "Namn och URL måste anges")
                return
            
            source_data = {
                "name": name_var.get().strip(),
                "url": url_var.get().strip(),
                "description": desc_text.get("1.0", tk.END).strip()
            }
            
            if index is not None:
                self.sources[source_key][index] = source_data
            else:
                if source_key not in self.sources:
                    self.sources[source_key] = []
                self.sources[source_key].append(source_data)
            
            if self.save_sources():
                self.refresh_sources()
                dialog.destroy()
        
        ttk.Button(button_frame, text="Spara", command=save_source).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def start_generation(self):
        """Starta podcastgenerering"""
        if self.generation_running:
            return
        
        self.generation_running = True
        self.generate_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start()
        self.progress_var.set("Genererar podcast...")
        
        # Rensa output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # Starta generering i separat tråd
        thread = threading.Thread(target=self.run_generation)
        thread.daemon = True
        thread.start()
    
    def run_generation(self):
        """Kör podcastgenerering i bakgrund"""
        try:
            # Bygg kommando
            cmd = ["python", "run_podcast.py"]
            
            # Lägg till flaggor baserat på checkboxes
            if not self.gen_intro_var.get():
                cmd.append("--no-intro")
            if not self.gen_news_var.get():
                cmd.append("--no-news") 
            if not self.gen_tech_var.get():
                cmd.append("--no-tech")
            if not self.gen_weather_var.get():
                cmd.append("--no-weather")
            if not self.gen_music_var.get():
                cmd.append("--no-music")
            
            # Kör processen
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True,
                cwd=os.getcwd()
            )
            
            # Läs output i realtid
            for line in process.stdout:
                if not self.generation_running:
                    process.terminate()
                    break
                
                self.root.after(0, self.update_output, line.strip())
            
            process.wait()
            
            if self.generation_running:
                self.root.after(0, self.generation_complete, process.returncode == 0)
            
        except Exception as e:
            self.root.after(0, self.generation_error, str(e))
    
    def update_output(self, line: str):
        """Uppdatera output-text"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, line + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def generation_complete(self, success: bool):
        """Hantera när generering är klar"""
        self.generation_running = False
        self.generate_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        
        if success:
            self.progress_var.set("✅ Podcast genererad framgångsrikt!")
            messagebox.showinfo("Klart", "Podcast genererad! Klicka 'Spela senaste' för att lyssna.")
        else:
            self.progress_var.set("❌ Fel vid generering")
            messagebox.showerror("Fel", "Podcastgenerering misslyckades. Se log för detaljer.")
    
    def generation_error(self, error: str):
        """Hantera genereringsfel"""
        self.generation_running = False
        self.generate_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set(f"❌ Fel: {error}")
        messagebox.showerror("Fel", f"Podcastgenerering misslyckades: {error}")
    
    def stop_generation(self):
        """Stoppa pågående generering"""
        self.generation_running = False
        self.progress_var.set("Stoppar generering...")
    
    def play_latest(self):
        """Spela senaste genererade podcast"""
        if not self.audio_enabled:
            messagebox.showwarning("Audio", "Audio-uppspelning inte tillgänglig")
            return
        
        # Hitta senaste podcast i audio-mappen
        audio_dir = "audio"
        if not os.path.exists(audio_dir):
            messagebox.showwarning("Ingen podcast", "Ingen audio-mapp hittades")
            return
        
        # Hitta senaste intro_complete_*.mp3
        podcast_files = [f for f in os.listdir(audio_dir) if f.startswith("intro_complete_") and f.endswith(".mp3")]
        
        if not podcast_files:
            messagebox.showwarning("Ingen podcast", "Ingen podcast hittades")
            return
        
        # Sortera efter filnamn (datum/tid) och ta senaste
        podcast_files.sort(reverse=True)
        latest_file = os.path.join(audio_dir, podcast_files[0])
        
        try:
            pygame.mixer.music.load(latest_file)
            pygame.mixer.music.play()
            messagebox.showinfo("Spelar", f"Spelar: {podcast_files[0]}")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spela podcast: {e}")
    
    def open_output_folder(self):
        """Öppna output-mappen"""
        audio_dir = "audio"
        if os.path.exists(audio_dir):
            os.startfile(audio_dir)  # Windows
        else:
            messagebox.showwarning("Mapp", "Audio-mappen finns inte än")
    
    def open_music_manager(self):
        """Öppna musikhanterare"""
        try:
            subprocess.Popen(["python", "music_manager_gui.py"])
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte öppna musikhanterare: {e}")
    
    def open_clip_editor(self):
        """Öppna musikklipp-editor"""
        try:
            subprocess.Popen(["python", "music_clip_editor.py"])
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte öppna klipp-editor: {e}")
    
    def test_music(self, category: str):
        """Testa musik för kategori med rätt längd"""
        if not self.audio_enabled:
            messagebox.showwarning("Audio", "Audio-uppspelning inte tillgänglig")
            return
        
        try:
            from music_mixer import MusicMixer
            mixer = MusicMixer()
            music_file = mixer.get_music_for_emotion("friendly", category)
            
            if music_file and os.path.exists(music_file):
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.play()
                
                # Stoppa efter rätt tid beroende på kategori
                if category == "intro":
                    play_duration = 8  # 8 sekunder för intro
                    threading.Timer(play_duration, lambda: pygame.mixer.music.stop()).start()
                    messagebox.showinfo("Test", f"Spelar intro-musik (8 sek):\n{os.path.basename(music_file)}")
                elif category == "transition":
                    play_duration = 4  # 4 sekunder för brygga
                    threading.Timer(play_duration, lambda: pygame.mixer.music.stop()).start()
                    messagebox.showinfo("Test", f"Spelar bryggmusik (4 sek):\n{os.path.basename(music_file)}")
                else:
                    messagebox.showinfo("Test", f"Spelar {category}-musik:\n{os.path.basename(music_file)}")
            else:
                messagebox.showwarning("Test", f"Ingen {category}-musik hittades")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte testa musik: {e}")
    
    def stop_music(self):
        """Stoppa musik"""
        if self.audio_enabled:
            pygame.mixer.music.stop()
    
    def save_settings(self):
        """Spara inställningar"""
        # Här kan du spara inställningar till en config-fil
        settings = {
            "target_audience": self.target_audience_var.get(),
            "duration": self.duration_var.get(),
            "tone": self.tone_var.get(),
            "music_volume": self.music_volume_var.get(),
            "bridge_duration": self.bridge_duration_var.get()
        }
        
        try:
            with open("podcast_settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Sparad", "Inställningar sparade!")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara inställningar: {e}")
    
    def open_env_file(self):
        """Öppna .env-filen för redigering"""
        env_path = ".env"
        if os.path.exists(env_path):
            try:
                os.startfile(env_path)  # Windows
            except:
                messagebox.showwarning("Fel", "Kunde inte öppna .env-fil")
        else:
            # Skapa .env-fil med mall
            if messagebox.askyesno("Skapa .env", ".env-fil saknas. Vill du skapa en mall?"):
                env_template = """# API-nycklar för Människa Maskin Miljö podcast
# Få nycklar från respektive tjänst och fyll i här

# ElevenLabs (röstsyntes)
ELEVENLABS_API_KEY=din_elevenlabs_nyckel_här

# OpenRouter (AI-innehåll)
OPENROUTER_API_KEY=din_openrouter_nyckel_här

# Cloudflare R2 (filuppladdning)
CLOUDFLARE_R2_TOKEN=din_cloudflare_token_här
CLOUDFLARE_R2_ACCOUNT_ID=ditt_cloudflare_konto_id_här
CLOUDFLARE_R2_BUCKET_NAME=ditt_bucket_namn_här

# Valfria inställningar
# MUSIC_VOLUME=25
# BRIDGE_DURATION=3-5
"""
                try:
                    with open(env_path, 'w', encoding='utf-8') as f:
                        f.write(env_template)
                    os.startfile(env_path)
                    messagebox.showinfo("Skapad", ".env-fil skapad! Fyll i dina API-nycklar.")
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte skapa .env-fil: {e}")
    
    def refresh_api_status(self):
        """Uppdatera API-status"""
        # Starta om inställningsfliken för att visa uppdaterad status
        messagebox.showinfo("Uppdaterad", "Starta om applikationen för att se uppdaterad API-status")
    
    def cleanup_old_podcasts(self):
        """Rensa gamla podcast-filer"""
        audio_dir = "audio"
        if not os.path.exists(audio_dir):
            messagebox.showinfo("Rensning", "Ingen audio-mapp att rensa")
            return
        
        # Hitta gamla filer (mer än 7 dagar gamla)
        import time
        now = time.time()
        week_ago = now - (7 * 24 * 60 * 60)
        
        old_files = []
        for filename in os.listdir(audio_dir):
            if filename.startswith("intro_complete_") and filename.endswith(".mp3"):
                filepath = os.path.join(audio_dir, filename)
                if os.path.getmtime(filepath) < week_ago:
                    old_files.append(filename)
        
        if not old_files:
            messagebox.showinfo("Rensning", "Inga gamla filer att rensa")
            return
        
        if messagebox.askyesno("Rensa filer", 
                              f"Hitta {len(old_files)} gamla podcast-filer. Ta bort dem?"):
            deleted = 0
            for filename in old_files:
                try:
                    os.remove(os.path.join(audio_dir, filename))
                    deleted += 1
                except Exception as e:
                    print(f"Kunde inte ta bort {filename}: {e}")
            
            messagebox.showinfo("Rensad", f"Tog bort {deleted} gamla podcast-filer")
    
    def run(self):
        """Starta GUI"""
        self.root.mainloop()

def main():
    """Huvudfunktion"""
    app = PodcastGeneratorGUI()
    app.run()

if __name__ == "__main__":
    main()
