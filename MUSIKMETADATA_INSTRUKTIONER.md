# 🎵 Musikmetadata-system för MMM Senaste Nytt

## 📋 Översikt
Systemet låter dig tagga musikfiler med metadata som mood, tempo, energi och kategorier för intelligent musikval i podcast-produktion.

## 🏷️ Tillgängliga taggar

### Moods (Känslor)
- `calm` - Lugn musik
- `energetic` - Energisk musik  
- `peaceful` - Fridful musik
- `mysterious` - Mystisk musik
- `uplifting` - Upplyftande musik
- `dreamy` - Drömsk musik
- `contemplative` - Eftertänksam musik
- `meditative` - Meditativ musik

### Tempo
- `slow` - Långsamt tempo
- `medium` - Medeltempo  
- `fast` - Snabbt tempo

### Energinivåer
- `low` - Låg energi
- `medium` - Medel energi
- `high` - Hög energi

### Kategorier
- `ambient` - Ambient bakgrundsmusik
- `background` - Allmän bakgrundsmusik
- `intro` - Intromusik
- `outro` - Outromusik  
- `news` - Nyhetsmusik
- `relaxing` - Avslappnande musik
- `transition` - Övergångsmusik

## 🔧 Så här använder du systemet

### 1. Lägg till nya låtar
```bash
# Kopiera MP3-filer till music-mappen
cp "Min Nya Låt.mp3" audio/music/
```

### 2. Skanna efter nya filer
```bash
python music_metadata_manager.py
```

### 3. Tagga dina låtar
Redigera `complete_music_config.json`:

```json
{
  "Min Nya Låt.mp3": {
    "moods": ["intense", "dramatic"],
    "tempo": "fast", 
    "energy": "high",
    "intensity": "high",
    "categories": ["news", "urgent"],
    "description": "Intensiv musik för viktiga nyheter"
  },
  "Lugn Bakgrund.mp3": {
    "moods": ["calm", "peaceful"],
    "tempo": "slow",
    "energy": "low", 
    "intensity": "low",
    "categories": ["background", "ambient"],
    "description": "Mycket lugn för bakgrundsmusik"
  }
}
```

### 4. Applicera metadata
```bash
python apply_music_metadata.py
```

## 🎯 Exempel på musiksökning

### Programmatisk sökning (i kod):
```python
from music_mixer import MusicMixer

mixer = MusicMixer()

# Sök lugn musik
calm_track = mixer.get_music_by_metadata(mood="calm")

# Sök energisk intro-musik
intro_track = mixer.get_music_by_metadata(mood="energetic", category="intro")

# Sök låg energi för bakgrund
bg_track = mixer.get_music_by_metadata(energy="low", category="background")
```

## 🎵 Intelligent musikvariation

Systemet skapar automatiskt varierad musik genom att:

1. **Dela upp avsnittet i zoner:**
   - Intro → Energisk musik
   - Bakgrund → Lugn musik  
   - Höjdpunkter → Hög energi
   - Transitions → Fridful musik

2. **Byta musik var 60:e sekund** med 3s crossfade

3. **Undvika repetition** genom smart rotation

## 📁 Hantera varianter med parenteser

✅ **Fungerar perfekt:**
- `Vågornas Sång.mp3`
- `Vågornas Sång (1).mp3` 
- `Vågornas Sång (2).mp3`
- `Vågornas Sång (3).mp3`

Varje variant kan taggas individuellt med olika metadata.

## 🔍 Felsökning

### Problem: Musik hittas inte
```bash
# Kontrollera att filer finns
ls audio/music/

# Synkronisera metadata
python music_metadata_manager.py
```

### Problem: Metadata appliceras inte
```bash
# Kontrollera JSON-syntax
python -c "import json; json.load(open('complete_music_config.json'))"

# Applicera igen
python apply_music_metadata.py
```

### Problem: Ingen musikvariation
Kontrollera att `music_metadata.json` innehåller dina taggar och att `MusicMixer` laddar metadata-managern korrekt.

## 📊 Visa aktuell status

```bash
# Visa alla låtar och deras taggar
python -c "
from music_metadata_manager import MusicMetadataManager
manager = MusicMetadataManager()
for track in manager.metadata['tracks'].values():
    print(f'{track['filename']}: {track.get('moods', [])}')
"
```

## 🎊 Resultat

- **Ingen repetitiv musik** - lyssnarna tröttnar inte
- **Intelligent musikval** - passar innehållets känsla
- **Automatisk variation** - nytt i varje avsnitt
- **Enkel hantering** - lägg till filer och tagga

---
**Skapad:** 5 oktober 2025  
**System:** MMM Senaste Nytt Podcast Generator