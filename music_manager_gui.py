#!/usr/bin/env python3
"""
GUI för musikhantering i Människa Maskin Miljö podcast
Låter användaren lägga till, redigera och testa bryggmusik
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import pygame
from typing import Dict, List
import uuid
from datetime import datetime
from pathlib import Path

class MusicManagerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Människa Maskin Miljö - Musikhantering")
        self.root.geometry("800x600")
        
        # Initialisera pygame för audio-uppspelning
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except:
            self.audio_enabled = False
            print("⚠️ Audio playback not available")
        
        self.music_library_path = "music_library.json"
        self.music_library = self.load_music_library()
        
        self.setup_ui()
        self.refresh_music_list()
    
    def load_music_library(self) -> Dict:
        """Ladda musik-bibliotek"""
        try:
            with open(self.music_library_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "tracks": {},
                "categories": {
                    "intro": "Intro och öppning",
                    "news": "Nyheter och seriöst innehåll", 
                    "tech": "Teknik och innovation",
                    "transition": "Övergångar mellan ämnen",
                    "weather": "Väder och avslutning",
                    "outro": "Avslutning och outro"
                },
                "moods": {
                    "serious": "Seriös och professionell",
                    "upbeat": "Energisk och positiv",
                    "calm": "Lugn och avslappnande",
                    "mysterious": "Mystisk och spännande",
                    "dramatic": "Dramatisk och intensiv",
                    "playful": "Lekfull och glad"
                }
            }
    
    def save_music_library(self):
        """Spara musik-bibliotek"""
        try:
            with open(self.music_library_path, 'w', encoding='utf-8') as f:
                json.dump(self.music_library, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara: {e}")
            return False
    
    def setup_ui(self):
        """Skapa användargränssnitt"""
        # Huvudframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titel
        title_label = ttk.Label(main_frame, text="🎵 Musikbibliotek - Bryggmusik", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Musiklista
        list_frame = ttk.LabelFrame(main_frame, text="Tillgänglig musik", padding="10")
        list_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Treeview för musiklista
        columns = ("Titel", "Artist", "Kategorier", "Stämningar", "Beskrivning")
        self.music_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.music_tree.heading(col, text=col)
            self.music_tree.column(col, width=150)
        
        self.music_tree.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar för lista
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.music_tree.yview)
        scrollbar.grid(row=0, column=4, sticky=(tk.N, tk.S))
        self.music_tree.configure(yscrollcommand=scrollbar.set)
        
        # Knappar för musiklista
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        ttk.Button(button_frame, text="▶️ Spela", command=self.play_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="⏹️ Stopp", command=self.stop_music).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="➕ Lägg till", command=self.add_music).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="✏️ Redigera", command=self.edit_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="🗑️ Ta bort", command=self.delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        
        # Testsektion
        test_frame = ttk.LabelFrame(main_frame, text="Testa bryggmusik", padding="10")
        test_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(test_frame, text="Emotion:").grid(row=0, column=0, padx=(0, 5))
        self.emotion_var = tk.StringVar(value="exciting")
        emotion_combo = ttk.Combobox(test_frame, textvariable=self.emotion_var, 
                                   values=["exciting", "serious", "friendly", "professional"])
        emotion_combo.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(test_frame, text="🎵 Testa brygga", command=self.test_bridge).grid(row=0, column=2, padx=(10, 0))
        
        # Statistik
        stats_frame = ttk.LabelFrame(main_frame, text="Statistik", padding="10")
        stats_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.stats_label = ttk.Label(stats_frame, text="")
        self.stats_label.pack()
        
        # Konfigurera grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
    
    def refresh_music_list(self):
        """Uppdatera musiklistan"""
        # Rensa trädet
        for item in self.music_tree.get_children():
            self.music_tree.delete(item)
        
        # Lägg till musiktracks
        for track_id, track in self.music_library.get("tracks", {}).items():
            title = track.get("title", "Okänd")
            artist = track.get("artist", "Okänd")
            categories = ", ".join(track.get("categories", []))
            moods = ", ".join(track.get("moods", []))
            description = track.get("description", "")
            
            self.music_tree.insert("", tk.END, values=(title, artist, categories, moods, description))
        
        # Uppdatera statistik
        total_tracks = len(self.music_library.get("tracks", {}))
        transition_tracks = sum(1 for track in self.music_library.get("tracks", {}).values() 
                              if "transition" in track.get("categories", []))
        self.stats_label.config(text=f"Totalt: {total_tracks} spår | Bryggmusik: {transition_tracks} spår")
    
    def play_selected(self):
        """Spela vald musik"""
        if not self.audio_enabled:
            messagebox.showwarning("Audio", "Audio-uppspelning inte tillgänglig")
            return
        
        selection = self.music_tree.selection()
        if not selection:
            messagebox.showwarning("Val", "Välj en musikfil först")
            return
        
        # Hitta vald track
        item = self.music_tree.item(selection[0])
        title = item['values'][0]
        
        for track in self.music_library.get("tracks", {}).values():
            if track.get("title") == title:
                music_path = track.get("path")
                if music_path and os.path.exists(music_path):
                    try:
                        pygame.mixer.music.load(music_path)
                        pygame.mixer.music.play()
                        messagebox.showinfo("Spelar", f"Spelar: {title}")
                    except Exception as e:
                        messagebox.showerror("Fel", f"Kunde inte spela musik: {e}")
                else:
                    messagebox.showerror("Fel", f"Musikfil hittades inte: {music_path}")
                break
    
    def stop_music(self):
        """Stoppa musik"""
        if self.audio_enabled:
            pygame.mixer.music.stop()
    
    def add_music(self):
        """Lägg till ny musik"""
        self.edit_music_dialog()
    
    def edit_selected(self):
        """Redigera vald musik"""
        selection = self.music_tree.selection()
        if not selection:
            messagebox.showwarning("Val", "Välj en musikfil först")
            return
        
        item = self.music_tree.item(selection[0])
        title = item['values'][0]
        
        for track_id, track in self.music_library.get("tracks", {}).items():
            if track.get("title") == title:
                self.edit_music_dialog(track_id, track)
                break
    
    def delete_selected(self):
        """Ta bort vald musik"""
        selection = self.music_tree.selection()
        if not selection:
            messagebox.showwarning("Val", "Välj en musikfil först")
            return
        
        if messagebox.askyesno("Bekräfta", "Är du säker på att du vill ta bort denna musik?"):
            item = self.music_tree.item(selection[0])
            title = item['values'][0]
            
            for track_id, track in list(self.music_library.get("tracks", {}).items()):
                if track.get("title") == title:
                    del self.music_library["tracks"][track_id]
                    self.save_music_library()
                    self.refresh_music_list()
                    break
    
    def edit_music_dialog(self, track_id=None, track_data=None):
        """Dialog för att redigera/lägga till musik"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Lägg till/Redigera musik")
        dialog.geometry("500x400")
        dialog.grab_set()
        
        # Fält
        ttk.Label(dialog, text="Titel:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        title_var = tk.StringVar(value=track_data.get("title", "") if track_data else "")
        ttk.Entry(dialog, textvariable=title_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Artist:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        artist_var = tk.StringVar(value=track_data.get("artist", "") if track_data else "")
        ttk.Entry(dialog, textvariable=artist_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Musikfil:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        file_frame = ttk.Frame(dialog)
        file_frame.grid(row=2, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        file_var = tk.StringVar(value=track_data.get("path", "") if track_data else "")
        file_entry = ttk.Entry(file_frame, textvariable=file_var, width=30)
        file_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        def browse_file():
            filename = filedialog.askopenfilename(
                title="Välj musikfil",
                filetypes=[("Audio files", "*.mp3 *.wav *.ogg"), ("All files", "*.*")]
            )
            if filename:
                file_var.set(filename)
        
        ttk.Button(file_frame, text="Bläddra", command=browse_file).pack(side=tk.LEFT)
        
        # Kategorier (checkboxes)
        ttk.Label(dialog, text="Kategorier:").grid(row=3, column=0, sticky=(tk.W, tk.N), padx=5, pady=5)
        cat_frame = ttk.Frame(dialog)
        cat_frame.grid(row=3, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        category_vars = {}
        current_categories = track_data.get("categories", []) if track_data else []
        
        for cat, desc in self.music_library.get("categories", {}).items():
            var = tk.BooleanVar(value=cat in current_categories)
            category_vars[cat] = var
            ttk.Checkbutton(cat_frame, text=f"{cat} ({desc})", variable=var).pack(anchor=tk.W)
        
        # Stämningar (checkboxes)
        ttk.Label(dialog, text="Stämningar:").grid(row=4, column=0, sticky=(tk.W, tk.N), padx=5, pady=5)
        mood_frame = ttk.Frame(dialog)
        mood_frame.grid(row=4, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        mood_vars = {}
        current_moods = track_data.get("moods", []) if track_data else []
        
        for mood, desc in self.music_library.get("moods", {}).items():
            var = tk.BooleanVar(value=mood in current_moods)
            mood_vars[mood] = var
            ttk.Checkbutton(mood_frame, text=f"{mood} ({desc})", variable=var).pack(anchor=tk.W)
        
        # Beskrivning
        ttk.Label(dialog, text="Beskrivning:").grid(row=5, column=0, sticky=(tk.W, tk.N), padx=5, pady=5)
        desc_var = tk.StringVar(value=track_data.get("description", "") if track_data else "")
        ttk.Entry(dialog, textvariable=desc_var, width=40).grid(row=5, column=1, padx=5, pady=5)
        
        # Knappar
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        def save_track():
            # Validering
            if not title_var.get().strip():
                messagebox.showerror("Fel", "Titel måste anges")
                return
            
            if not file_var.get().strip():
                messagebox.showerror("Fel", "Musikfil måste väljas")
                return
            
            # Samla data
            categories = [cat for cat, var in category_vars.items() if var.get()]
            moods = [mood for mood, var in mood_vars.items() if var.get()]
            
            if not categories:
                messagebox.showerror("Fel", "Minst en kategori måste väljas")
                return
            
            if not moods:
                messagebox.showerror("Fel", "Minst en stämning måste väljas")
                return
            
            # Skapa/uppdatera track
            new_track_id = track_id if track_id else str(uuid.uuid4())[:8]
            
            track_info = {
                "id": new_track_id,
                "title": title_var.get().strip(),
                "artist": artist_var.get().strip() or "unknown",
                "filename": os.path.basename(file_var.get()),
                "path": file_var.get(),
                "categories": categories,
                "moods": moods,
                "description": desc_var.get().strip(),
                "added_at": track_data.get("added_at", datetime.now().isoformat()) if track_data else datetime.now().isoformat(),
                "file_size": os.path.getsize(file_var.get()) if os.path.exists(file_var.get()) else 0
            }
            
            self.music_library["tracks"][new_track_id] = track_info
            
            if self.save_music_library():
                self.refresh_music_list()
                dialog.destroy()
                messagebox.showinfo("Sparad", "Musik sparad!")
        
        ttk.Button(button_frame, text="Spara", command=save_track).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def test_bridge(self):
        """Testa bryggmusik för vald emotion"""
        emotion = self.emotion_var.get()
        
        # Simulera musikval för brygga
        from music_mixer import MusicMixer
        mixer = MusicMixer()
        music_file = mixer.get_music_for_emotion(emotion, "transition")
        
        if music_file and os.path.exists(music_file):
            if self.audio_enabled:
                try:
                    pygame.mixer.music.load(music_file)
                    pygame.mixer.music.play()
                    messagebox.showinfo("Test", f"Spelar {emotion} bryggmusik:\n{os.path.basename(music_file)}")
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte spela musik: {e}")
            else:
                messagebox.showinfo("Test", f"Vald {emotion} bryggmusik:\n{os.path.basename(music_file)}")
        else:
            messagebox.showwarning("Test", f"Ingen bryggmusik hittades för emotion: {emotion}")
    
    def run(self):
        """Starta GUI"""
        self.root.mainloop()

def main():
    """Huvudfunktion"""
    app = MusicManagerGUI()
    app.run()

if __name__ == "__main__":
    main()
