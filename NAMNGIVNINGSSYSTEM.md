# 📝 Namngivningssystem för MMM Senaste Nytt

## 🎯 Syfte
Tydlig distinktion mellan vardagsavsnitt och helgavsnitt för enkel identifiering och återfinning.

## 📅 Vardagar (Måndag-Fredag)

### Avsnittstitel:
- **Format**: `MMM Senaste Nytt - [Veckodag] [Dag Månad] Nyheter`
- **Exempel**: `MMM Senaste Nytt - Måndag 27 september Nyheter`

### Filnamn:
- **Format**: `MMM_YYYYMMDD_[veckodag]_nyheter.mp3`
- **Exempel**: `MMM_20250927_måndag_nyheter.mp3`

### Beskrivning:
- **Format**: `📰 Dagsnyheter [veckodag] [dag månad] - [sammanfattning]...`
- **Exempel**: `📰 Dagsnyheter måndag 27 september - Svenska klimatmål och nya AI-genombrott inom energi...`

### GUID:
- **Format**: `mmm-YYYY-MM-DD-nyheter`
- **Exempel**: `mmm-2025-09-27-nyheter`

---

## 🌅 Helger (Lördag-Söndag)

### Avsnittstitel:
- **Format**: `**Format:**
```
MMM Senaste Nytt - [Veckodag] [Dag] [Månad] [År] [Nyheter/Fördjupning]
```

**Exempel:**
- `MMM Senaste Nytt - Måndag 27 januari 2025 Nyheter`
- `MMM Senaste Nytt - Lördag 15 mars 2025 Fördjupning``
- **Exempel**: `MMM Senaste Nytt - Lördag 27 september Fördjupning`

### Filnamn:
- **Format**: `MMM_YYYYMMDD_[veckodag]_fördjupning.mp3`
- **Exempel**: `MMM_20250927_lördag_fördjupning.mp3`

### Beskrivning:
- **Format**: `🧩 Helgfördjupning [veckodag] [dag månad]: Den Gröna Tråden - [sammanfattning]...`
- **Exempel**: `🧩 Helgfördjupning lördag 27 september: Den Gröna Tråden - Hur AI, energi och klimat hänger ihop...`

### GUID:
- **Format**: `mmm-YYYY-MM-DD-fördjupning`
- **Exempel**: `mmm-2025-09-27-fördjupning`

---

## 🎙️ RSS Feed Subtitles

### Vardagar:
- **Format**: `[Veckodag] [Dag Månad] Nyheter - Människa Maskin Miljö`
- **Exempel**: `Måndag 27 september Nyheter - Människa Maskin Miljö`

### Helger:
- **Format**: `[Veckodag] [Dag Månad] Fördjupning - Den Gröna Tråden`
- **Exempel**: `Lördag 27 september Fördjupning - Den Gröna Tråden`

---

## ✅ Fördelar med detta system:

1. **🔍 Enkel sökning**: Hitta snabbt vardags- vs helgavsnitt
2. **📊 Tydlig kategorisering**: Lyssnare vet vad de kan förvänta sig
3. **🗓️ Datum-spårning**: Exakt datum i både titel och filnamn
4. **🎯 Innehållsindikation**: Emojis och nyckelord visar innehållstyp
5. **📱 Podcast-vänligt**: Fungerar bra i alla podcast-appar
6. **🔗 Unika GUID**: Inga dubletter eller konflikter

## 🚀 Implementation:
- Automatisk detection av helg/vardag baserat på `datetime.weekday()`
- Konsekvent namngivning över alla filer och metadata
- RSS-feed uppdaterad för ny struktur
- GitHub Actions kör dagligt med rätt namngivning

---

**Exempel på hur det ser ut i en podcast-app:**

```
🎙️ MMM Senaste Nytt

📰 MMM Senaste Nytt - Måndag 22 september 2025 Nyheter
📰 MMM Senaste Nytt - Tisdag 23 september 2025 Nyheter
📰 MMM Senaste Nytt - Onsdag 24 september 2025 Nyheter
📰 MMM Senaste Nytt - Torsdag 25 september 2025 Nyheter
📰 MMM Senaste Nytt - Fredag 26 september 2025 Nyheter
🧩 MMM Senaste Nytt - Lördag 27 september 2025 Fördjupning
🧩 MMM Senaste Nytt - Söndag 28 september 2025 Fördjupning
```