#!/usr/bin/env python3
"""
Test script för Cloudflare R2 konfiguration
Testar anslutning och grundläggande funktioner för Människa Maskin Miljö
"""

import sys
import os
sys.path.append('src')

from cloudflare_uploader import CloudflareUploader
import json
from datetime import datetime

def test_r2_connection():
    print("=== CLOUDFLARE R2 CONNECTION TEST ===")
    print()
    
    try:
        uploader = CloudflareUploader()
        print(f"✅ R2 Uploader initialiserad")
        print(f"   Bucket: {uploader.bucket_name}")
        print(f"   Public URL: {uploader.public_url}")
        print()
        
        # Test 1: Skapa en test-fil
        print("📝 Test 1: Skapar test-fil...")
        test_content = {
            "test": "Människa Maskin Miljö R2 Test",
            "timestamp": datetime.now().isoformat(),
            "system": "morgonradio-automated"
        }
        
        test_file = "r2_test.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_content, f, ensure_ascii=False, indent=2)
        
        # Test 2: Ladda upp test-fil
        print("📤 Test 2: Laddar upp till R2...")
        upload_url = uploader.upload_file(test_file, "test/connection_test.json")
        print(f"✅ Upload lyckades!")
        print(f"   Public URL: {upload_url}")
        print()
        
        # Test 3: Testa bucket-anslutning direkt
        print("🔌 Test 3: Testar bucket-anslutning...")
        bucket_exists = uploader.s3_client.list_objects_v2(
            Bucket=uploader.bucket_name,
            MaxKeys=1
        )
        print("✅ Bucket-anslutning fungerar!")
        print()
        
        # Rensa upp
        os.remove(test_file)
        
        print("🎉 ALLA TESTER LYCKADES!")
        print()
        print("📋 Nästa steg:")
        print("   1. Konfigurera korrekt bucket-namn för Människa Maskin Miljö")
        print("   2. Sätt upp public URL")
        print("   3. Testa automatisk RSS-generering")
        
    except Exception as e:
        print(f"❌ FEL: {e}")
        print()
        print("🔧 Möjliga lösningar:")
        print("   1. Kontrollera API-nycklar i .env")
        print("   2. Kontrollera bucket-namn och behörigheter")
        print("   3. Följ cloudflare_r2_setup.md för konfiguration")

def test_sources_json_r2_config():
    print("=== SOURCES.JSON R2 KONFIGURATION ===")
    print()
    
    try:
        with open('sources.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        r2_config = config.get('cloudflare', {})
        
        print("Nuvarande R2-konfiguration i sources.json:")
        print(f"   Bucket: {r2_config.get('bucket', 'INTE SATT')}")
        print(f"   Public URL: {r2_config.get('publicUrl', 'INTE SATT')}")
        print()
        
        if not r2_config.get('bucket'):
            print("⚠️  Bucket inte konfigurerat i sources.json")
            print("   Bör uppdateras till 'manniska-maskin-miljo' eller liknande")
        else:
            print("✅ Bucket konfigurerat")
            
    except Exception as e:
        print(f"❌ Kunde inte läsa sources.json: {e}")

if __name__ == "__main__":
    test_r2_connection()
    print()
    test_sources_json_r2_config()
