#!/usr/bin/env python3
"""
RSS Feed Generator för Människa Maskin Miljö
Skapar en Spotify-kompatibel RSS-feed med Cloudflare R2-integration
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys
from typing import List, Dict

# Lägg till src-mappen i Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from cloudflare_uploader import CloudflareUploader

def create_rss_feed(episodes: List[Dict], config: Dict) -> str:
    """Skapa RSS feed XML för podcast"""
    
    # Root RSS element
    rss = ET.Element("rss")
    rss.set("version", "2.0")
    rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    
    channel = ET.SubElement(rss, "channel")
    
    # Podcast metadata
    ET.SubElement(channel, "title").text = "Människa Maskin Miljö"
    ET.SubElement(channel, "description").text = "Veckans nyheter inom AI, klimat och teknik. Automatiskt genererad podcast som sammanfattar viktiga utvecklingar för en hållbar framtid."
    ET.SubElement(channel, "link").text = config.get("publicUrl", "https://manniska-maskin-miljo.r2.dev")
    ET.SubElement(channel, "language").text = "sv-SE"
    ET.SubElement(channel, "category").text = "Technology"
    ET.SubElement(channel, "pubDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    
    # iTunes-specific tags
    itunes_author = ET.SubElement(channel, "itunes:author")
    itunes_author.text = "Pontus - Människa Maskin Miljö"
    
    itunes_subtitle = ET.SubElement(channel, "itunes:subtitle")
    itunes_subtitle.text = "AI och klimatnyheter varje onsdag"
    
    itunes_summary = ET.SubElement(channel, "itunes:summary")
    itunes_summary.text = "Människa Maskin Miljö är en AI-genererad podcast som varje onsdag sammanfattar veckans viktigaste nyheter inom artificiell intelligens, klimat och hållbar teknik. Podden ger dig en snabb överblick av utvecklingen inom dessa kritiska områden för vår framtid."
    
    itunes_owner = ET.SubElement(channel, "itunes:owner")
    ET.SubElement(itunes_owner, "itunes:name").text = "Pontus"
    ET.SubElement(itunes_owner, "itunes:email").text = "podcast@example.com"
    
    # Cover image
    cover_url = f"{config.get('publicUrl', '')}/cover.jpg"
    ET.SubElement(channel, "itunes:image").set("href", cover_url)
    
    # Image tag for RSS
    image = ET.SubElement(channel, "image")
    ET.SubElement(image, "url").text = cover_url
    ET.SubElement(image, "title").text = "Människa Maskin Miljö"
    ET.SubElement(image, "link").text = config.get("publicUrl", "")
    
    # Lägg till episoder
    for episode in episodes:
        item = ET.SubElement(channel, "item")
        
        # Episod metadata
        title = f"Vecka {episode['week']}: Människa Maskin Miljö"
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "description").text = episode['description']
        ET.SubElement(item, "pubDate").text = episode['pub_date']
        ET.SubElement(item, "guid").text = episode['guid']
        
        # Audio enclosure
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", episode['audio_url'])
        enclosure.set("type", "audio/mpeg")
        enclosure.set("length", str(episode.get('file_size', 15000000)))
        
        # iTunes episode tags
        ET.SubElement(item, "itunes:duration").text = episode.get('duration', '12:00')
        ET.SubElement(item, "itunes:author").text = "Pontus - Människa Maskin Miljö"
        ET.SubElement(item, "itunes:subtitle").text = f"Vecka {episode['week']} - AI och klimatnyheter"
        ET.SubElement(item, "itunes:summary").text = episode['description']
    
    # Konvertera till sträng
    return ET.tostring(rss, encoding='unicode', method='xml')

def generate_and_upload_rss(episodes: List[Dict], config: Dict, upload_to_r2: bool = True) -> Dict:
    """
    Generera RSS feed och ladda upp till Cloudflare R2
    
    Args:
        episodes: Lista med episod-data
        config: Podcast konfiguration
        upload_to_r2: Om True, ladda upp till R2, annars bara spara lokalt
    
    Returns:
        dict: Resultat med local_path och optional public_url
    """
    print("📡 Genererar RSS feed...")
    
    # Generera RSS content
    rss_content = create_rss_feed(episodes, config)
    
    # Spara lokalt
    rss_file = "public/feed.xml"
    os.makedirs("public", exist_ok=True)
    
    with open(rss_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(rss_content)
    
    result = {
        "local_path": rss_file,
        "content_length": len(rss_content)
    }
    
    print(f"✅ RSS feed sparad lokalt: {rss_file}")
    print(f"📝 Storlek: {len(rss_content)} tecken")
    
    # Ladda upp till R2 om requested
    if upload_to_r2:
        try:
            print("☁️ Laddar upp till Cloudflare R2...")
            uploader = CloudflareUploader()
            
            # Test connection först
            if not uploader.test_connection():
                print("❌ R2 connection failed")
                return result
            
            # Upload RSS feed
            public_url = uploader.upload_file(rss_file, "feed.xml", "application/xml")
            
            if public_url:
                result["public_url"] = public_url
                print(f"✅ RSS feed uploaded: {public_url}")
                
                # Upload static files också
                print("📁 Laddar upp statiska filer...")
                static_urls = uploader.upload_static_files()
                if static_urls:
                    result["static_files"] = static_urls
                    print(f"✅ {len(static_urls)} statiska filer uppladdade")
                
            else:
                print("❌ RSS upload failed")
                
        except Exception as e:
            print(f"❌ R2 upload error: {e}")
    
    return result

def test_rss_generation():
    """Test RSS generation och upload"""
    print("=== RSS GENERATION & UPLOAD TEST ===\n")
    
    # Test data
    test_episodes = [
        {
            "week": "38",
            "date": "2025-09-18", 
            "description": "Vecka 38: AI-genombrott inom klimatmodellering, nya policyer för gröna investeringar och teknikjättarnas hållbarhetsrapporter. Vi täcker också de senaste rönen inom förnybar energi.",
            "audio_url": "https://manniska-maskin-miljo.9c5323b560f65e0ead7cee1bdba8a690.r2.dev/episodes/2025-w38.mp3",
            "guid": "mmm-2025-w38",
            "pub_date": "Wed, 18 Sep 2025 07:00:00 +0200",
            "file_size": 15000000,  # 15MB
            "duration": "12:30"
        },
        {
            "week": "37", 
            "date": "2025-09-11",
            "description": "Vecka 37: ChatGPT-uppdateringar, klimatpolitik och gröna investeringar. Vi diskuterar nya AI-verktyg för miljöanalys och hur teknikjättar satsar på förnybar energi.",
            "audio_url": "https://manniska-maskin-miljo.9c5323b560f65e0ead7cee1bdba8a690.r2.dev/episodes/2025-w37.mp3",
            "guid": "mmm-2025-w37", 
            "pub_date": "Wed, 11 Sep 2025 07:00:00 +0200",
            "file_size": 14500000,
            "duration": "11:45"
        }
    ]
    
    config = {
        "publicUrl": "https://manniska-maskin-miljo.9c5323b560f65e0ead7cee1bdba8a690.r2.dev"
    }
    
    # Generera och ladda upp RSS
    result = generate_and_upload_rss(test_episodes, config, upload_to_r2=True)
    
    print("\n📊 RESULTAT:")
    print(f"   Lokal fil: {result.get('local_path')}")
    print(f"   Storlek: {result.get('content_length')} tecken")
    
    if result.get('public_url'):
        print(f"   Public URL: {result['public_url']}")
        print(f"   📡 Feed redo för Spotify/podcasting platforms!")
    else:
        print("   ⚠️ Ingen public URL - upload misslyckades eller ej aktiverad")
    
    if result.get('static_files'):
        print(f"   🗂️ Statiska filer: {len(result['static_files'])} upladdade")
    
    print("\n🎯 NÄSTA STEG:")
    if result.get('public_url'):
        print("1. ✅ RSS feed är live och redo")
        print("2. 📱 Lägg till feed URL i Spotify for Podcasters")
        print("3. 🎧 Testa playback i podcast apps")
        print(f"4. 🔗 Feed URL: {result['public_url']}")
    else:
        print("1. 🔧 Fixa R2 upload-problem")
        print("2. 🔄 Kör test igen")
        print("3. 📡 Verifiera feed fungerar")
    
    # Visa början av feed för debug
    if os.path.exists(result.get('local_path', '')):
        print("\n--- RSS FEED PREVIEW ---")
        with open(result['local_path'], 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:500] + "...")

if __name__ == "__main__":
    test_rss_generation()
