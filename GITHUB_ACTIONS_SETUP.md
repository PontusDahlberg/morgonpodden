# 🔐 GitHub Secrets Setup Guide

För att GitHub Actions ska fungera behöver du lägga till dina API-nycklar som "Secrets" i ditt GitHub repository.

## 📝 STEG-FÖR-STEG:

### 1. Gå till Repository Settings
1. Öppna https://github.com/fltman/morgonradio
2. Klicka på **"Settings"** (längst till höger i menyn)
3. I vänster sidofält, klicka **"Secrets and variables"** → **"Actions"**

### 2. Lägg till följande Secrets:
Klicka **"New repository secret"** för varje:

#### 🤖 AI & Voice APIs:
```
Name: OPENROUTER_API_KEY
Value: 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

Name: ELEVENLABS_API_KEY  
Value: sk_66306c824bc74cf65efd0094398f8dfd2d077f8ee2a9987a

Name: ELEVENLABS_VOICE_ID
Value: 4xkUqaR9MYOJHoaC1Nak
```

#### ☁️ Cloudflare R2:
```
Name: CLOUDFLARE_API_TOKEN
Value: Abwq-QDnP30ARf21VOx4o-ZRRFSh-nWU4PA7Q4f3

Name: CLOUDFLARE_R2_BUCKET
Value: manniska-maskin-miljo

Name: CLOUDFLARE_R2_PUBLIC_URL
Value: https://manniska-maskin-miljo.9c5323b560f65e0ead7cee1bdba8a690.r2.dev
```

## ✅ VERIFIERING:

När alla secrets är tillagda ska du se:
- ✅ OPENROUTER_API_KEY
- ✅ ELEVENLABS_API_KEY  
- ✅ ELEVENLABS_VOICE_ID
- ✅ CLOUDFLARE_API_TOKEN
- ✅ CLOUDFLARE_R2_BUCKET
- ✅ CLOUDFLARE_R2_PUBLIC_URL

## 🚀 TEST WORKFLOW:

1. Gå till **"Actions"** tab i ditt repo
2. Välj **"📡 Människa Maskin Miljö - Weekly Podcast"**
3. Klicka **"Run workflow"** → **"Run workflow"** (för manuell test)
4. Vänta ~5-10 minuter
5. ✅ Kolla att ny podcast laddats upp till din R2-bucket

## 📅 AUTOMATISK SCHEMALÄGGNING:

Efter setup körs podcast automatiskt:
- ⏰ **Varje onsdag kl 07:00 CET**
- 🌍 **Från GitHub's servrar** (inte din dator)
- 📡 **RSS uppdateras automatiskt**
- 📱 **Spotify får nya episoder inom 24h**

## 🔧 FELSÖKNING:

Om något går fel:
1. Gå till **Actions** → senaste workflow run
2. Klicka på det röda krysset för att se fel
3. Kontrollera att alla Secrets är korrekta
4. Kör **"Run workflow"** manuellt för retry

## 📊 MONITORING:

GitHub Actions ger dig:
- 📈 **Historia**: Se alla tidigare körningar
- 📋 **Logs**: Detaljerade loggar för felsökning  
- 🔔 **Notifications**: Email om något går fel
- 📁 **Artifacts**: Nedladdningsbara logfiler

## 💡 TIPS:

- Secrets är **säkra** - syns aldrig i logs
- Du kan **uppdatera** secrets när som helst
- **Manuell trigger** fungerar alltid för testing
- **Workflow history** sparas i 90 dagar

---

🎉 **När allt är setup har du en professionell podcast-automation som aldrig missar ett avsnitt!**
