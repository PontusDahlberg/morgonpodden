#!/usr/bin/env python3
"""
Komplett Cloudflare R2 setup och test för Människa Maskin Miljö
"""

import sys
import os
sys.path.append('src')

def main_menu():
    print("=== CLOUDFLARE R2 SETUP - MÄNNISKA MASKIN MILJÖ ===")
    print()
    print("1. 📋 Visa nuvarande konfiguration")
    print("2. 🔍 Testa R2-anslutning") 
    print("3. 📤 Ladda upp test-filer")
    print("4. 📡 Generera och ladda upp RSS-feed")
    print("5. 🚀 Komplett deployment-test")
    print("6. ❓ Visa Cloudflare-instruktioner")
    print("0. 🚪 Avsluta")
    print()
    
    while True:
        choice = input("Välj alternativ (0-6): ").strip()
        
        if choice == "0":
            print("Hej då! 👋")
            break
        elif choice == "1":
            show_config()
        elif choice == "2":
            test_connection()
        elif choice == "3":
            upload_test_files()
        elif choice == "4":
            upload_rss_feed()
        elif choice == "5":
            full_deployment_test()
        elif choice == "6":
            show_instructions()
        else:
            print("❌ Ogiltigt val. Försök igen.")
        
        print("\\n" + "="*50 + "\\n")

def show_config():
    """Visa nuvarande R2-konfiguration"""
    print("📋 NUVARANDE KONFIGURATION")
    print()
    
    from dotenv import load_dotenv
    load_dotenv()
    
    configs = [
        ("CLOUDFLARE_ACCESS_KEY_ID", "Access Key ID"),
        ("CLOUDFLARE_SECRET_ACCESS_KEY", "Secret Access Key"),
        ("CLOUDFLARE_R2_ENDPOINT", "R2 Endpoint"),
        ("CLOUDFLARE_R2_BUCKET", "Bucket Name"),
        ("CLOUDFLARE_R2_PUBLIC_URL", "Public URL")
    ]
    
    for env_var, description in configs:
        value = os.getenv(env_var, "❌ INTE SATT")
        if "secret" in env_var.lower() and value != "❌ INTE SATT":
            value = value[:8] + "..." if len(value) > 8 else value
        elif "key" in env_var.lower() and value != "❌ INTE SATT":
            value = value[:12] + "..." if len(value) > 12 else value
            
        print(f"{description}: {value}")

def test_connection():
    """Testa R2-anslutning"""
    print("🔍 TESTAR R2-ANSLUTNING")
    print()
    
    try:
        from cloudflare_uploader import CloudflareUploader
        uploader = CloudflareUploader()
        
        # Test bucket access
        bucket_response = uploader.s3_client.list_objects_v2(
            Bucket=uploader.bucket_name,
            MaxKeys=5
        )
        
        print(f"✅ Anslutning till bucket '{uploader.bucket_name}' lyckades!")
        
        objects = bucket_response.get('Contents', [])
        if objects:
            print(f"📁 Hittade {len(objects)} objekt i bucket:")
            for obj in objects[:3]:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("📁 Bucket är tom")
            
    except Exception as e:
        print(f"❌ Anslutningsfel: {e}")
        print()
        print("🔧 Lösningsförslag:")
        print("   1. Kontrollera API-nycklar i .env")
        print("   2. Verifiera bucket-namn och behörigheter")
        print("   3. Följ instruktionerna (alternativ 6)")

def upload_test_files():
    """Ladda upp test-filer till R2"""
    print("📤 LADDAR UPP TEST-FILER")
    print()
    
    try:
        from cloudflare_uploader import CloudflareUploader
        import json
        from datetime import datetime
        
        uploader = CloudflareUploader()
        
        # Skapa test-filer
        test_files = []
        
        # 1. Test JSON
        test_data = {
            "project": "Människa Maskin Miljö",
            "test_time": datetime.now().isoformat(),
            "status": "R2 upload test"
        }
        
        with open("test_data.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # 2. Test HTML (index page)
        html_content = """<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <title>Människa Maskin Miljö - Podcast</title>
</head>
<body>
    <h1>Människa Maskin Miljö</h1>
    <p>Veckans AI och klimatnyheter - automatiskt genererad podcast</p>
    <p>RSS Feed: <a href="feed.xml">feed.xml</a></p>
</body>
</html>"""
        
        os.makedirs("public", exist_ok=True)
        with open("public/index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Ladda upp filer
        test_files = [
            ("test_data.json", "test/data.json"),
            ("public/index.html", "index.html")
        ]
        
        uploaded_urls = []
        
        for local_file, remote_path in test_files:
            if os.path.exists(local_file):
                url = uploader.upload_file(local_file, remote_path)
                uploaded_urls.append(url)
                print(f"✅ {local_file} → {url}")
        
        # Cleanup
        if os.path.exists("test_data.json"):
            os.remove("test_data.json")
            
        print(f"\\n🎉 {len(uploaded_urls)} filer uppladdade!")
        print("\\n📋 Testa URL:er:")
        for url in uploaded_urls:
            print(f"   {url}")
            
    except Exception as e:
        print(f"❌ Upload-fel: {e}")

def upload_rss_feed():
    """Generera och ladda upp RSS-feed"""
    print("📡 GENERERAR OCH LADDAR UPP RSS-FEED")
    print()
    
    try:
        # Generera RSS först
        exec(open("generate_rss.py").read())
        
        if os.path.exists("public/feed.xml"):
            from cloudflare_uploader import CloudflareUploader
            uploader = CloudflareUploader()
            
            url = uploader.upload_file("public/feed.xml", "feed.xml")
            print(f"✅ RSS-feed uppladdad: {url}")
            print()
            print("🎯 För Spotify/Apple Podcasts använd URL:")
            print(f"   {url}")
        else:
            print("❌ RSS-feed kunde inte genereras")
            
    except Exception as e:
        print(f"❌ RSS-fel: {e}")

def full_deployment_test():
    """Komplett deployment-test"""
    print("🚀 KOMPLETT DEPLOYMENT-TEST")
    print()
    
    print("1️⃣ Testar anslutning...")
    test_connection()
    
    print("\\n2️⃣ Laddar upp test-filer...")  
    upload_test_files()
    
    print("\\n3️⃣ Genererar RSS-feed...")
    upload_rss_feed()
    
    print("\\n🎉 DEPLOYMENT KOMPLETT!")
    print("\\nSystemet är redo för:")
    print("   ✅ Automatisk podcast-generering")
    print("   ✅ R2-distribution")
    print("   ✅ RSS-feed för Spotify/Apple Podcasts")

def show_instructions():
    """Visa Cloudflare-instruktioner"""
    print("❓ CLOUDFLARE R2 SETUP INSTRUKTIONER")
    print()
    print("Se detaljerade instruktioner i:")
    print("   📄 CLOUDFLARE_R2_GUIDE.md")
    print()
    print("Snabbguide:")
    print("1. 🌐 Gå till dash.cloudflare.com")
    print("2. 📦 Skapa bucket: 'manniska-maskin-miljo'")
    print("3. 🔑 Skapa API-token med Read & Write")
    print("4. ⚙️ Uppdatera .env med dina krediter")
    print("5. 🧪 Kör detta script igen för att testa")

if __name__ == "__main__":
    main_menu()
