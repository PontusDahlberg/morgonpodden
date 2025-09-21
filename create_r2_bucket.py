#!/usr/bin/env python3
"""
Skapa ny bucket för Människa Maskin Miljö
"""

import sys
import os
sys.path.append('src')

import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

def create_bucket():
    print("=== SKAPA NY BUCKET FÖR MÄNNISKA MASKIN MILJÖ ===")
    print()
    
    # Konfigurera S3-klient för Cloudflare R2
    endpoint_url = os.getenv('CLOUDFLARE_R2_ENDPOINT')
    access_key = os.getenv('CLOUDFLARE_ACCESS_KEY_ID')
    secret_key = os.getenv('CLOUDFLARE_SECRET_ACCESS_KEY')
    
    if not all([endpoint_url, access_key, secret_key]):
        print("❌ R2-krediter saknas i .env")
        print("Kontrollera CLOUDFLARE_R2_ENDPOINT, CLOUDFLARE_ACCESS_KEY_ID, CLOUDFLARE_SECRET_ACCESS_KEY")
        return
    
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3}
            ),
            region_name='auto'
        )
        
        # Lista befintliga buckets
        print("📋 Befintliga buckets:")
        response = s3_client.list_buckets()
        for bucket in response['Buckets']:
            print(f"   - {bucket['Name']}")
        print()
        
        # Föreslå bucket-namn
        suggested_bucket = "manniska-maskin-miljo"
        print(f"💡 Föreslaget bucket-namn: {suggested_bucket}")
        print()
        
        # Skapa bucket (om det inte finns)
        try:
            s3_client.create_bucket(Bucket=suggested_bucket)
            print(f"✅ Bucket '{suggested_bucket}' skapad!")
        except Exception as e:
            if "BucketAlreadyExists" in str(e):
                print(f"ℹ️  Bucket '{suggested_bucket}' finns redan")
            else:
                print(f"❌ Kunde inte skapa bucket: {e}")
                return
        
        # Testa upload till den nya bucketen
        print(f"📤 Testar upload till {suggested_bucket}...")
        test_content = "Människa Maskin Miljö test"
        s3_client.put_object(
            Bucket=suggested_bucket,
            Key="test/connection_test.txt",
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print("✅ Test-upload lyckades!")
        print()
        
        print("🎯 NÄSTA STEG:")
        print(f"1. Uppdatera .env med: CLOUDFLARE_R2_BUCKET={suggested_bucket}")
        print("2. Sätt upp public URL för bucketen")
        print("3. Uppdatera sources.json med R2-konfiguration")
        
    except Exception as e:
        print(f"❌ Anslutningsfel: {e}")
        print()
        print("🔧 Möjliga orsaker:")
        print("   - API-nycklarna är felaktiga")
        print("   - Endpoint-URL är fel")
        print("   - Nätverksanslutningsproblem")

if __name__ == "__main__":
    create_bucket()
