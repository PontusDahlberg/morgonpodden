# 🚀 Cloudflare R2 Setup Guide för Människa Maskin Miljö

## Steg 1: Cloudflare-konto
1. Gå till https://cloudflare.com/
2. Skapa konto eller logga in
3. Gå till Dashboard

## Steg 2: Aktivera R2 Storage
1. I Dashboard, klicka "R2 Object Storage" i sidomenyn
2. Klicka "Get Started" eller "Enable R2"
3. Du får gratis tier: 10GB storage, 1 miljon requests/månad

## Steg 3: Skapa bucket för Människa Maskin Miljö
1. Klicka "Create bucket"
2. Bucket name: `manniska-maskin-miljo` 
3. Välj location: "Automatic" 
4. Klicka "Create bucket"

## Steg 4: Konfigurera public access
1. Gå till din bucket
2. Klicka "Settings"
3. Under "Public access" klicka "Allow Access"
4. Kopiera den public URL som visas (typ: https://pub-xxxxx.r2.dev)

## Steg 5: Skapa API-tokens
1. Gå till "R2" > "Manage R2 API tokens"
2. Klicka "Create API token"
3. Token name: "Människa Maskin Miljö Podcast"
4. Permissions: 
   - "Object Read & Write" 
   - Bucket: din bucket (manniska-maskin-miljo)
5. Klicka "Create API token"
6. **VIKTIG:** Kopiera Access Key ID och Secret Access Key DIREKT

## Steg 6: Uppdatera .env
Ersätt i .env-filen:
```
CLOUDFLARE_ACCESS_KEY_ID=din_nya_access_key_id
CLOUDFLARE_SECRET_ACCESS_KEY=din_nya_secret_key
CLOUDFLARE_R2_ENDPOINT=https://DITT_ACCOUNT_ID.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET=manniska-maskin-miljo
CLOUDFLARE_R2_PUBLIC_URL=https://pub-xxxxx.r2.dev
```

## Steg 7: Testa anslutning
Kör: `python test_r2.py`

## Kostnader
- **Gratis tier**: 10GB storage, 1M requests/månad
- **Betald**: $0.015/GB storage, $0.36/miljon requests
- **För ditt podcast**: ~$1-3/månad för 50+ avsnitt

## Alternativ: Använd befintligt R2-konto
Om du redan har R2-krediter som fungerar, kan vi bara skapa en ny bucket i det kontot.
