# Guide för Cloudflare R2 Setup - Människa Maskin Miljö

## Steg 1: Logga in på Cloudflare Dashboard
1. Gå till https://dash.cloudflare.com/
2. Navigera till "R2 Object Storage" på vänster sida

## Steg 2: Skapa ny bucket
1. Klicka "Create bucket"
2. Bucket name: `manniska-maskin-miljo` (eller valfritt namn)
3. Välj region (rekommenderat: "Automatic" för bästa prestanda)
4. Klicka "Create bucket"

## Steg 3: Konfigurera public access (viktigt för podcast-distribution)
1. Gå till din nya bucket
2. Klicka på "Settings" 
3. Under "Public access" klicka "Allow Access"
4. Detta ger dig en public URL som: https://pub-xxxxx.r2.dev

## Steg 4: API-nycklar (du har redan dessa men vi kollar)
1. Gå till "R2" > "Manage R2 API tokens"
2. Skapa nya API-nycklar:
   - Access Key ID: YOUR_ACCESS_KEY_ID
   - Secret: YOUR_SECRET_KEY

## Steg 5: Custom domain (valfritt men rekommenderat)
1. Om du har en domän kan du sätta upp: https://podcast.din-domain.com
2. Detta ger mer professionell RSS-feed för Spotify

## När du har gjort detta:
1. Uppdatera bucket-namnet i .env
2. Uppdatera public URL i .env  
3. Testa upload-funktionen
