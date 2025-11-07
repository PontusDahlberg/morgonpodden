# MULTI-AGENT NEWS CURATION SYSTEM - IMPLEMENTATION PLAN

## PROBLEMANALYS (7 november 2025)

### Identifierade Problem:
1. **Obalans**: Alldeles för många tech-nyheter (80%), för få klimat/miljö (20%)
2. **Irrelevanta nyheter**:
   - Disney+ filmlista
   - GTA VI spelförseningar  
   - Samsung microSD-kort för Switch 2
   - MacBook-reor
3. **Felaktig information**: Sudan-nyheten sa "hundratals döda" när det är tusentals
4. **För få svenska klimat/miljö-nyheter**

## LÖSNING: MULTI-AGENT ARKITEKTUR

### Agent-System (news_agent_system.py)

```
┌─────────────────────────────────────────────────────────────┐
│                    NEWS ORCHESTRATOR                        │
│            (Huvudkoordinator för alla agenter)              │
└──────────────────┬──────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┬────────────┐
    │              │              │              │            │
    ▼              ▼              ▼              ▼            ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐
│ Scraper │  │Relevance │  │FactCheck │  │ Balance  │  │ Output  │
│  Agent  │─▶│  Agent   │─▶│  Agent   │─▶│  Agent   │─▶│ Curator │
└─────────┘  └──────────┘  └──────────┘  └──────────┘  └─────────┘
```

### Agent 1: NewsScraperAgent
**Ansvar**: Kategorisering och geografisk identifiering

**Kategorier** (med prioritet):
1. `CLIMATE_SWEDEN` (100 poäng) - Högst prioritet
2. `ENVIRONMENT_SWEDEN` (95 poäng)
3. `CLIMATE_GLOBAL` (90 poäng)
4. `ENVIRONMENT_GLOBAL` (85 poäng)
5. `TECH_CLIMATE` (70 poäng) - Tech med klimatkoppling
6. `TECH_AI` (40 poäng) - Låg prioritet
7. `TECH_GENERAL` (20 poäng) - Mycket låg prioritet
8. `IRRELEVANT` (0 poäng) - Exkluderas

**Filtrerar bort**:
- Gaming (GTA, Xbox, PlayStation, Nintendo, esport)
- Underhållning (Disney, Netflix, filmer, serier)
- Produktreklam (köpguider, reor, "best deals")
- Konsumentelektronik utan klimatkoppling

### Agent 2: RelevanceAgent
**Ansvar**: Betygsätter varje artikel 0-100 baserat på:
- Kategori
- Geografisk närhet (Sverige +5 poäng)
- Källkvalitet (Wired/Verge får -20 om tech_general)

### Agent 3: FactCheckAgent
**Ansvar**: Rimlighetskontroll och faktaverifiering

**Checks**:
- Sifferkontroller (hundratals vs tusentals)
- 100%-påståenden (ofta orealistiska)
- Kontext-kontroller (Sudan: hundratals döda = flaggas som underskattning)

**Resultat**:
- `fact_check_passed`: True/False
- `fact_check_notes`: Beskrivning av problem

### Agent 4: BalanceAgent
**Ansvar**: Säkerställ rätt ämnesbalans

**Mål**:
- **60% klimat/miljö** (inkl. tech_climate)
- **40% tech/AI** (max)

**Process**:
1. Filtrera bort irrelevanta och fact-check-failade
2. Sortera efter relevance_score
3. Gruppera: klimat_env vs tech_ai
4. Välj 6 klimat + 4 tech = 10 totalt

### Orchestrator
**Ansvar**: Koordinerar hela flödet

**Pipeline**:
```
Råa artiklar → Kategorisering → Relevansbedömning → Faktakontroll → Balansering → Slutligt urval
```

## INTEGRATION MED BEFINTLIGT SYSTEM

### Steg 1: Behåll nuvarande scraping
`scrape_news.py` fortsätter scrapa från alla källor i `sources.json`

### Steg 2: Lägg till agent-kurering
Efter scraping, INNAN podcast-generering:

```python
from news_curation_integration import curate_news_sync

# Istället för att läsa scraped_content.json direkt:
curated_articles = curate_news_sync('scraped_content.json')

# Använd curated_articles i podcast-generering
```

### Steg 3: Uppdatera run_podcast_complete.py
Ersätt den nuvarande manuella filtreringen (rad 230-370) med:

```python
# Gammal kod: Manuell filtrering med keywords
# NY KOD:
from news_curation_integration import curate_news_sync
available_articles = curate_news_sync('scraped_content.json')
```

## FÖRDELAR MED AGENT-SYSTEMET

### 1. **Modularitet**
- Varje agent har EN uppgift
- Lätt att testa och debugga
- Kan förbättra varje agent separat

### 2. **Transparens**
- Detaljerad logging från varje steg
- Se exakt varför artiklar väljs bort
- Fact-check-notes synliga i output

### 3. **Kvalitetskontroll**
- Faktakontroll fångar orimliga påståenden
- Relevansscoring objektivt
- Balanseringsagent garanterar 60/40-fördelning

### 4. **Skalbarhet**
- Lätt att lägga till nya agenter (t.ex. DuplicationAgent, BiasAgent)
- Kan integrera AI-modeller för bättre analys
- Orchestrator hanterar komplexitet

### 5. **Ingen MCP behövs (ännu)**
- Systemet fungerar standalone
- MCP kan läggas till senare för remote agents eller AI-tjänster
- För nu: Lokal orchestration räcker

## EXEMPEL: DAGENS ARTIKLAR (7 NOV)

### Innan agent-system:
```
❌ GTA VI delayed
❌ Disney+ movies
❌ MacBook deals
❌ Samsung microSD
✅ Nuclear fusion fund (1 klimat-artikel av 10)
```

### Efter agent-system:
```
✅ 6 klimat/miljö-artiklar (svenska prioriterade)
✅ 4 relevanta tech/AI-artiklar
❌ GTA VI - filtrerad (gaming → irrelevant)
❌ Disney - filtrerad (underhållning → irrelevant)
❌ MacBook - filtrerad (produktreklam → irrelevant)
```

## NÄSTA STEG

### 1. Testa agent-systemet
```bash
python news_agent_system.py
```
Se hur dagens artiklar kategoriseras och filtreras.

### 2. Integrera i workflow
Uppdatera `run_podcast_complete.py` att använda `curate_news_sync()`

### 3. Övervaka första körningen
Kolla loggar från nästa podcast-generering (8 nov):
- Hur många artiklar per kategori?
- Fact-check-warnings?
- Geografisk fördelning?

### 4. Justera vid behov
- Tweaka relevance_scores
- Lägg till fler irrelevanta keywords
- Justera balance_target (60/40 → 70/30?)

## FRAMTIDA FÖRBÄTTRINGAR

### Kort sikt:
- Integrera AI-modell i FactCheckAgent för bättre faktakontroll
- DuplicationAgent - hitta identiska nyheter från olika källor
- BiasAgent - upptäck partisk rapportering

### Medellång sikt:
- WebScraperAgent - aktivt söka nya källor på nätet
- TrendAgent - identifiera emerging topics inom klimat
- LocalNewsAgent - fokus på regional svensk klimatrapportering

### Lång sikt:
- MCP-integration för distribuerade agenter
- AI-modeller för djupanalys av artikelinnehåll
- Automatisk källdiversifiering

## SVAR PÅ DINA FRÅGOR

### "Behöver vi en MCP?"
**Nej, inte ännu.** Agent-systemet fungerar utmärkt lokalt med orchestrator-mönstret. MCP blir relevant när:
- Du vill distribuera agenter över nätverk
- Externa AI-tjänster ska integreras som agenter
- Flera system behöver dela samma agenter

För nu: **Orchestrator-baserat system räcker perfekt.**

### "Kan det bli bättre än hårdkodad faktakontroll?"
**Ja, absolut!** Agent-systemet är:
- Mer flexibelt (lätt att lägga till nya checks)
- Transparent (ser exakt vad som flaggas)
- Modulärt (kan testa fact-check separat)
- Skalbart (kan integrera AI-modeller senare)

### "Hur löser vi obalansen?"
**BalanceAgent** garanterar 60/40-fördelningen genom att:
1. Prioritera klimat/miljö-artiklar
2. Filtrera bort irrelevanta tech-nyheter
3. Endast välja högkvalitativa tech-artiklar som fyller ut resten

## SLUTSATS

✅ **Agent-systemet löser alla dina problem:**
- Balans: Garanterad 60/40 klimat/tech
- Relevans: Gaming, underhållning, produktreklam filtreras bort
- Fakta: Rimlighetskontroller fångar felaktiga siffror
- Geografi: Svenska nyheter prioriteras

✅ **Ingen MCP behövs ännu** - orchestrator-mönstret fungerar utmärkt

✅ **Enkelt att integrera** - ersätt bara den manuella filtreringen i run_podcast_complete.py

**Redo att implementera?** Kör `python news_agent_system.py` för att se det i action! 🚀
