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
    
    image = ET.SubElement(channel, "image")
    ET.SubElement(image, "url").text = cover_url
    ET.SubElement(image, "title").text = "Människa Maskin Miljö"
    ET.SubElement(image, "link").text = config.get("publicUrl", "")
    
    itunes_category = ET.SubElement(channel, "itunes:category")
    itunes_category.set("text", "Technology")
    
    itunes_explicit = ET.SubElement(channel, "itunes:explicit")
    itunes_explicit.text = "false"
    
    # Add episodes
    for episode in episodes:
        item = ET.SubElement(channel, "item")
        
        ET.SubElement(item, "title").text = f"Vecka {episode.get('week', 'XX')} - {episode.get('date', 'Datum')}"
        ET.SubElement(item, "description").text = episode.get('description', 'Veckans sammanfattning av AI och klimatnyheter')
        ET.SubElement(item, "link").text = episode.get('audio_url', '')
        ET.SubElement(item, "guid").text = episode.get('guid', episode.get('audio_url', ''))
        ET.SubElement(item, "pubDate").text = episode.get('pub_date', datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z"))
        
        # Audio enclosure
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", episode.get('audio_url', ''))
        enclosure.set("type", "audio/mpeg")
        enclosure.set("length", str(episode.get('file_size', 1000000)))  # Default 1MB
        
        # iTunes episode tags
        ET.SubElement(item, "itunes:author").text = "Människa Maskin Miljö"
        ET.SubElement(item, "itunes:duration").text = episode.get('duration', '08:00')
        ET.SubElement(item, "itunes:summary").text = episode.get('description', '')
        
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
    """Test RSS feed generation med exempel-data"""
    
    print("=== RSS FEED GENERATION TEST ===")
    print()
    
    # Test episodes
    test_episodes = [
        {
            "week": "38",
            "date": "2025-09-21",
            "description": "Vecka 38: AI-utveckling inom klimatteknik, nya EU-förordningar och svenska innovationer. Denna vecka fokuserar vi på genombrott inom smart energi och hur AI hjälper till att optimera resurser.",
            "audio_url": "https://pub-manniska-maskin-miljo.r2.dev/episodes/2025-w38.mp3",
            "guid": "mmm-2025-w38",
            "pub_date": "Wed, 18 Sep 2025 07:00:00 +0200",
            "file_size": 15000000,  # 15MB
            "duration": "12:30"
        },
        {
            "week": "37", 
            "date": "2025-09-11",
            "description": "Vecka 37: ChatGPT-uppdateringar, klimatpolitik och gröna investeringar. Vi diskuterar nya AI-verktyg för miljöanalys och hur teknikjättar satsar på förnybar energi.",
            "audio_url": "https://pub-manniska-maskin-miljo.r2.dev/episodes/2025-w37.mp3",
            "guid": "mmm-2025-w37", 
            "pub_date": "Wed, 11 Sep 2025 07:00:00 +0200",
            "file_size": 14500000,
            "duration": "11:45"
        }
    ]
    
    config = {
        "publicUrl": "https://pub-manniska-maskin-miljo.r2.dev"
    }
    
    # Generera RSS
    rss_content = create_rss_feed(test_episodes, config)
    
    # Spara RSS-feed
    rss_file = "public/feed.xml"
    os.makedirs("public", exist_ok=True)
    
    with open(rss_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\\n')
        f.write(rss_content)
    
    print(f"✅ RSS feed skapad: {rss_file}")
    print(f"📝 Storlek: {len(rss_content)} tecken")
    print(f"📡 Feed URL: {config['publicUrl']}/feed.xml")
    print()
    
    # Visa början av feed
    print("--- RSS FEED PREVIEW ---")
    print(rss_content[:500] + "...")
    print()
    
    print("🎯 NÄSTA STEG:")
    print("1. Konfigurera Cloudflare R2 med korrekta krediter")
    print("2. Ladda upp RSS-feeden till R2")
    print("3. Lägg till denna URL i Spotify/andra plattformar")

if __name__ == "__main__":
    test_rss_generation()
