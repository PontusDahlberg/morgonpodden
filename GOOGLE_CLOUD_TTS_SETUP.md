# 🔊 Google Cloud Text-to-Speech Setup Guide

## 🎯 Varför Google Cloud TTS?
- **94% billigare** än ElevenLabs ($0.004 vs $0.30 per 1000 tecken)
- **Högkvalitativt**: Chirp3-HD neurala röster
- **Svenska röster**: Lisa (Gacrux) & Pelle (Iapetus)
- **Inga begränsningar**: Obegränsad användning

## 📋 Snabb Setup (5 minuter)

### Steg 1: Skapa Google Cloud Projekt
1. Gå till [Google Cloud Console](https://console.cloud.google.com/)
2. Skapa nytt projekt eller välj befintligt
3. Aktivera **Text-to-Speech API**
   - Gå till "APIs & Services" > "Library"
   - Sök på "Text-to-Speech API"
   - Klicka "Enable"

### Steg 2: Skapa Service Account
1. Gå till "IAM & Admin" > "Service Accounts"
2. Klicka "Create Service Account"
3. Namn: `podcast-tts-service`
4. Beskrivning: `TTS för Människa Maskin Miljö podcast`
5. Klicka "Create and Continue"

### Steg 3: Tilldela Behörigheter
1. Role: "Cloud Text-to-Speech Client" 
2. Klicka "Continue" > "Done"

### Steg 4: Skapa API Key
1. Klicka på din nya service account
2. Gå till "Keys" tab
3. Klicka "Add Key" > "Create new key"
4. Välj **JSON** format
5. Klicka "Create"
6. JSON-filen laddas ned automatiskt

### Steg 5: Installera i Projektet
1. Byt namn på den nedladdade filen till: `google-cloud-service-account.json`
2. Flytta filen till projektmappen: `c:\\Users\\pontu\\Documents\\Autopodd\\morgonradio\\`
3. Kontrollera att filen finns på rätt plats

## 🧪 Testa Installationen

Kör detta kommando för att testa:
```bash
python simple_test.py
```

Du ska se:
```
✅ Google Cloud TTS: Konfigurerat och fungerar
🎵 Genererade testljud med Lisa & Pelle
```

## 💰 Kostnadsjämförelse

| Provider | Kostnad per 1000 tecken | Månadskostnad* |
|----------|-------------------------|----------------|
| **Google Cloud TTS** | $0.004 | **~$4** |
| ElevenLabs | $0.30 | ~$300 |
| **BESPARING** | **94%** | **$296/månad** |

*Baserat på daglig podcast (~100,000 tecken/månad)

## 🔒 Säkerhet

Din `google-cloud-service-account.json` fil innehåller känslig information:
- ✅ Redan i `.gitignore` (pushas inte till GitHub)
- ✅ Endast lokal användning
- ✅ GitHub Actions använder säker secret

## 🚨 Felsökning

### Problem: "File google-cloud-service-account.json was not found"
**Lösning**: 
1. Kontrollera att filen finns i projektmappen
2. Kör: `ls google-cloud-service-account.json` (ska visa filstorlek)

### Problem: "Credentials not valid"
**Lösning**:
1. Kontrollera att Text-to-Speech API är aktiverat
2. Verifiera att service account har rätt behörigheter
3. Skapa ny JSON-nyckel om nödvändigt

### Problem: "Quota exceeded"
**Lösning**: 
- Google Cloud TTS har generösa gratiskvoter
- Första 1 miljon tecken/månad är gratis
- Därefter mycket låga kostnader

## 📞 Support

Om problem uppstår:
1. Kör `python api_key_backup_manager.py verify`
2. Kontrollera alla API-nycklar fungerar
3. Systemet faller automatiskt tillbaka på ElevenLabs vid problem

## 🎉 Nästa Steg

När Google Cloud TTS är konfigurerat:
1. **Lokal test**: `python run_podcast.py`
2. **Deploy till GitHub**: Allt fungerar automatiskt i GitHub Actions
3. **Spara pengar**: 94% lägre TTS-kostnader!

---
*Skapad: 2025-09-28 | Människa Maskin Miljö Podcast Project*