# 🎙️ MMM Senaste Nytt - Automatisk Daglig Nyhetspodcast

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

### Innehallskvalitet (miljovariabler)

Om underlaget blir tunt kan scraper automatiskt skarpa kraven och forsoka igen. Standarderna kan styras via miljovariabler:

- `MMM_THIN_AUTO_STRICT=1` aktiverar automatisk omkoring med strikt innehallskrav
- `MMM_THIN_RATIO_THRESHOLD=0.35` tröskel for andel tunna poster
- `MMM_THIN_RATIO_MIN_ITEMS=6` minsta antal poster innan tröskeln galler
- `MMM_REQUIRE_ARTICLE_CONTENT=false` (kan sattas till `true` for att alltid skippa tunna poster)

### Podcast Settings (GUI)

"Podcast Settings" är en sida i den lokala Streamlit-GUI:n (inte i GitHub Actions).

Starta GUI (Windows/macOS/Linux):
```bash
python -m streamlit run src/gui_app.py
```

Alternativ (större GUI):
```bash
python -m streamlit run src/enhanced_gui.py
```

När den startar skriver Streamlit ut en URL (oftast `http://localhost:8501`). Där hittar du sidan **Podcast Settings** i sidomenyn.

Tips: I **Podcast Settings** finns även sektionen **Aftertalk (Komiskt eftersnack)** (scrolla ner) där du kan slå på/av och välja veckodagar.

GitHub Actions läser bara konfigen från `sources.json` när workflow körs. Vill du ändra settings “i produktion” gör du det genom att uppdatera `sources.json` och pusha till GitHub.

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
- **Pelle** (Iapetus): Manlig svensk röst, specialist på AI och miljö

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
