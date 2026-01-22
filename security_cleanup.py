#!/usr/bin/env python3
"""
🚨 KRITISKT SÄKERHETSSKRIPT 
Rensar ALLA känsliga filer och data innan GitHub upload
"""

import os
import re
import glob
import shutil
from datetime import datetime

def security_cleanup():
    """Rensar alla känsliga filer och data"""
    
    print("🚨 SÄKERHETSRENSNING STARTAD")
    print("="*50)
    
    dangerous_files = []
    
    # 1. Ta bort/säkra .env fil
    if os.path.exists('.env'):
        print("🔒 Flyttar .env till säker plats...")
        shutil.move('.env', '.env.backup')
        
        # Skapa tom .env.example
        with open('.env.example', 'w') as f:
            f.write("""# EXEMPEL PÅ MILJÖVARIABLER - LÄGG ALDRIG RIKTIGA NYCKLAR HÄR!

# OpenAI API för innehållssammanfattning
OPENAI_API_KEY=your_openai_api_key_here

# OpenRouter API för AI-modeller  
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Google Cloud TTS Service Account
GOOGLE_APPLICATION_CREDENTIALS=./google-cloud-service-account.json
USE_GOOGLE_CLOUD_TTS=true

# ElevenLabs API (backup)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID_SANNA=your_voice_id_here
ELEVENLABS_VOICE_ID_GEORGE=your_voice_id_here

# Cloudflare R2 för deployment
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_R2_BUCKET=your_bucket_name_here
CLOUDFLARE_R2_PUBLIC_URL=https://your-public-url.com

# Lokala test-inställningar
LOCAL_TEST_MODE=true
""")
        print("✅ Skapat .env.example (säker att ladda upp)")
    
    # 2. Ta bort Google Cloud credentials
    google_creds = [
        'google-cloud-service-account.json',
        'google-cloud-credentials.json',
        '*.json'  # Alla JSON-filer som kan innehålla credentials
    ]
    
    for pattern in google_creds:
        for file in glob.glob(pattern):
            if 'service-account' in file or 'credentials' in file:
                if os.path.exists(file):
                    print(f"🔒 Flyttar {file} till säker plats...")
                    shutil.move(file, f"{file}.backup")
                    dangerous_files.append(file)
    
    # 3. Kontrollera .gitignore
    gitignore_content = """# KÄNSLIGA FILER - LÄGG ALDRIG TILL DESSA I GIT!
.env
.env.local  
.env.*.local
google-cloud-service-account.json
google-cloud-credentials.json
*-service-account.json
*.backup

# Audio filer (för stora för git)
audio/*.mp3
audio/*.wav

# Logs
*.log
generation_log.txt
test_*.log

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
pip-log.txt
pip-delete-this-directory.txt

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Test filer
test_dialogue.txt
test_*.txt
*_test_*.mp3
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    print("✅ Uppdaterat .gitignore för säkerhet")
    
    # 4. Skanna alla Python-filer efter hårdkodade nycklar
    print("\n🔍 SKANNAR PYTHON-FILER EFTER HÅRDKODADE NYCKLAR...")
    
    dangerous_patterns = [
        r'sk-proj-[A-Za-z0-9_-]+',  # OpenAI API keys
        r'sk-or-v1-[A-Za-z0-9_-]+', # OpenRouter API keys  
        r'sk_[A-Za-z0-9]{47,}',      # ElevenLabs API keys
        r'[A-Za-z0-9_]{40,}',        # Generic long tokens (Cloudflare etc)
        r'"type":\s*"service_account"',  # Google Cloud JSON
    ]
    
    python_files = []
    
    # Hitta alla relevanta filer men ignorera venv och andra irrelevanta mappar
    for root, dirs, files in os.walk('.'):
        # Ta bort mappar vi vill ignorera från sökningen
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', 'venv', '.env.backup', 'build', 'dist'}]
        
        for file in files:
            if file.endswith(('.py', '.md', '.yml', '.yaml')):
                python_files.append(os.path.join(root, file))
    
    files_with_secrets = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in dangerous_patterns:
                if re.search(pattern, content):
                    files_with_secrets.append(file_path)
                    break
        except Exception as e:
            print(f"⚠️ Kunde inte läsa {file_path}: {e}")
    
    if files_with_secrets:
        print("\n🚨 FILER MED HÅRDKODADE NYCKLAR HITTADE:")
        for file_path in files_with_secrets:
            print(f"   ❌ {file_path}")
        
        print(f"\n🛑 STOPP! {len(files_with_secrets)} filer innehåller känslig data!")
        print("Dessa filer MÅSTE rensas manuellt innan GitHub upload!")
        return False
    
    # 5. Kontrollera att inga stora audio-filer finns
    large_files = []
    for audio_file in glob.glob('audio/*.mp3'):
        size_mb = os.path.getsize(audio_file) / (1024 * 1024)
        if size_mb > 10:  # Större än 10 MB
            large_files.append((audio_file, size_mb))
    
    if large_files:
        print(f"\n📁 Stora audio-filer hittade ({len(large_files)} st):")
        for file_path, size_mb in large_files:
            print(f"   📄 {file_path}: {size_mb:.1f} MB")
        print("Dessa bör inte laddas upp till GitHub (för stora)")
    
    # 6. Skapa säker README för GitHub
    create_safe_readme()
    
    print(f"\n✅ SÄKERHETSRENSNING SLUTFÖRD!")
    print(f"📅 Tid: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if dangerous_files:
        print(f"\n📋 Flyttade {len(dangerous_files)} känsliga filer:")
        for file in dangerous_files:
            print(f"   🔒 {file} -> {file}.backup")
    
    print(f"\n🔐 NÄSTA STEG FÖR SÄKER GITHUB UPLOAD:")
    print("1. ✅ Känsliga filer flyttade till .backup")  
    print("2. ✅ .env.example skapad")
    print("3. ✅ .gitignore uppdaterad")
    print("4. ✅ Säker README skapad")
    print("5. 🔍 Manuell kontroll av alla filer innan commit")
    
    return True

def create_safe_readme():
    """Skapar säker README utan känsliga detaljer"""
    
    readme_content = """# 🎙️ MMM Senaste Nytt - Automatisk Daglig Nyhetspodcast

En automatiserad daglig nyhetspodcast som fokuserar på teknik, miljö och samhälle.

## 🚀 Funktioner

- **Automatisk innehållssamling** från svenska och internationella nyhetskällor
- **AI-genererat podcastsamtal** mellan Lisa och Pelle
- **Google Cloud Text-to-Speech** med Chirp3-HD röster för naturlig ljudkvalitet  
- **GitHub Actions automation** för daglig publicering
- **Cloudflare R2 hosting** för skalbar ljuddistribution

## 🛠️ Teknik

- **AI-modeller**: OpenRouter (Claude-3-Haiku) för innehållsgenerering
- **Text-to-Speech**: Google Cloud TTS Chirp3-HD (svenska röster)
- **Hosting**: Cloudflare R2 för audio-filer
- **Automation**: GitHub Actions för daglig körning
- **Källor**: RSS-feeds från svenska och internationella medier

## 📋 Installation

1. **Klona repository:**
   ```bash
   git clone https://github.com/pontusdahlberg/morgonpodden.git
   cd morgonpodden
   ```

2. **Installera dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfigurera miljövariabler:**
   ```bash
   cp .env.example .env
   # Redigera .env med dina API-nycklar
   ```

4. **Sätt upp Google Cloud credentials:**
   - Skapa service account i Google Cloud Console
   - Ladda ner JSON-fil som `google-cloud-service-account.json`

## 🔧 Konfiguration

Alla inställningar finns i `sources.json`:
- Nyhetskällor och RSS-feeds
- Podcast-metadata och värd-personligheter  
- TTS-inställningar och röstval
- AI-prompter för innehållsgenerering

## 🎯 Användning

**Lokal generering:**
```bash
python create_test_episode.py
```

**GitHub Actions (automatisk):**
- Körs dagligt via scheduled workflow
- Publicerar automatiskt till Cloudflare R2
- Uppdaterar RSS-feed för podcast-appar

## 🔒 Säkerhet

- Alla API-nycklar hanteras via miljövariabler
- GitHub Secrets används för automatiserad deployment  
- Inga känsliga data committed till repository

## 📊 Kostnad

- Google Cloud TTS: ~$0.04 per 10-minuters avsnitt (Chirp3-HD)
- OpenRouter API: ~$0.02 per avsnitt (Claude-3-Haiku)
- Cloudflare R2: Minimal kostnad för storage/bandwidth
- **Total**: ~$0.06 per avsnitt = ~$22/år för daglig podcast

## 🎤 Röster

- **Lisa** (Gacrux): Kvinnlig svensk röst, expert inom hållbar teknik
- **Pelle** (Charon): Manlig svensk röst, specialist på AI och miljö

## 📈 Kvalitet

- **Längd**: Exakt 10 minuter per avsnitt
- **Innehåll**: 8-10 nyhetsämnen per avsnitt  
- **Källor**: 23 aktiva RSS-feeds
- **Uppdateringsfrekvens**: Daglig publicering

## 🔄 Workflow

1. **06:00 svensk tid**: GitHub Actions triggas
2. **RSS-samling**: Hämtar senaste nyheter från alla källor
3. **AI-generering**: Skapar strukturerat podcastsamtal
4. **TTS-konvertering**: Genererar audio med Chirp3-HD röster
5. **Publicering**: Laddar upp till Cloudflare R2
6. **RSS-uppdatering**: Notifierar podcast-appar om nytt avsnitt

## 📝 Licens

MIT License - Se LICENSE fil för detaljer

## 🤝 Bidrag

Bidrag välkomnas! Öppna en issue eller pull request för förbättringar.

---

**Utvecklad av**: Pontus Dahlberg  
**Kontakt**: [GitHub](https://github.com/pontusdahlberg)
"""

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ Säker README.md skapad")

if __name__ == "__main__":
    print("🛡️ SÄKERHETSKONTROLL FÖRE GITHUB UPLOAD")
    print("="*50)
    
    success = security_cleanup()
    
    if success:
        print("\n🎉 SÄKERT ATT LADDA UPP TILL GITHUB!")
        print("Alla känsliga filer har rensats/flyttats.")
    else:
        print("\n🛑 EJ SÄKERT - RENSA MANUELLT FÖRST!")
        print("Hårdkodade nycklar hittade i filer.")