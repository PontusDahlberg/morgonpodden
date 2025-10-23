#!/usr/bin/env python3
"""
RSS Feed Generator för Människa Maskin Miljö - Enkel GitHub Pages version
Skapar en Spotify-kompatibel RSS-feed utan Cloudflare R2 krångel
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys
from typing import List, Dict
import re
import html

# Lägg till src-mappen i Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def clean_xml_text(text: str) -> str:
    """Rensa text för säker XML-användning"""
    if not text:
        return ""
    
    # Ta bort problematiska Unicode-tecken (bold/italic mathematical symbols)
    text = re.sub(r'[\U0001D400-\U0001D7FF]', '', text)  # Mathematical symbols
    
    # Ta bort kontrollkaraktärer utom vanliga whitespace
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalisera befintliga entiteter först för att undvika dubbel-escaping
    text = html.unescape(text)
    
    # Escapa för säker XML-serialisering
    text = html.escape(text, quote=True)
    
    return text

def create_rss_feed(episodes: List[Dict], config: Dict) -> str:
    """Skapa RSS feed XML för podcast"""
    
    # Root RSS element
    rss = ET.Element("rss")
    rss.set("version", "2.0")
    rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    
    channel = ET.SubElement(rss, "channel")
    
    # Podcast metadata
    ET.SubElement(channel, "title").text = "MMM Senaste Nytt - MÄNNISKA MASKIN MILJÖ"
    ET.SubElement(channel, "description").text = "Dagliga nyheter från världen av människa, maskin och miljö - med Lisa och Pelle. En del av Människa Maskin Miljö-familjen."
    ET.SubElement(channel, "link").text = config.get("publicUrl", "https://pontusdahlberg.github.io/morgonpodden")
    ET.SubElement(channel, "language").text = "sv-SE"
    ET.SubElement(channel, "category").text = "Technology"
    
    # Datum
    now = datetime.now(timezone.utc)
    ET.SubElement(channel, "pubDate").text = now.strftime("%a, %d %b %Y %H:%M:%S +0000")
    ET.SubElement(channel, "lastBuildDate").text = now.strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # iTunes metadata
    ET.SubElement(channel, "itunes:author").text = "Pontus - Människa Maskin Miljö"
    ET.SubElement(channel, "itunes:subtitle").text = "AI och klimatnyheter varje onsdag"
    ET.SubElement(channel, "itunes:summary").text = "Människa Maskin Miljö är en AI-genererad podcast som varje onsdag sammanfattar veckans viktigaste nyheter inom artificiell intelligens, klimat och hållbar teknik. Podden ger dig en snabb överblick av utvecklingen inom dessa kritiska områden för vår framtid."
    
    # Owner
    owner = ET.SubElement(channel, "itunes:owner")
    ET.SubElement(owner, "itunes:name").text = "Pontus"
    ET.SubElement(owner, "itunes:email").text = "podcast@example.com"
    
    # Image
    ET.SubElement(channel, "itunes:image").set("href", f"{config.get('publicUrl')}/cover.jpg")
    
    image = ET.SubElement(channel, "image")
    ET.SubElement(image, "url").text = f"{config.get('publicUrl')}/cover.jpg"
    ET.SubElement(image, "title").text = "Människa Maskin Miljö"
    ET.SubElement(image, "link").text = config.get("publicUrl")
    
    # Lägg till episoder
    for episode in episodes:
        item = ET.SubElement(channel, "item")
        
        # Grundläggande episode info
        ET.SubElement(item, "title").text = clean_xml_text(episode.get("title", ""))
        ET.SubElement(item, "description").text = clean_xml_text(episode.get("description", ""))
        ET.SubElement(item, "pubDate").text = episode.get("pub_date", "Mon, 01 Jan 2025 00:00:00 +0000")
        ET.SubElement(item, "guid").text = episode.get("guid", f"mmm-{episode.get('date', '2025-01-01')}")
        
        # Audio file
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", episode.get("audio_url", ""))
        enclosure.set("type", "audio/mpeg")
        enclosure.set("length", str(episode.get("file_size", 0)))
        
        # iTunes episode metadata
        ET.SubElement(item, "itunes:duration").text = episode.get("duration", "8:00")
        ET.SubElement(item, "itunes:author").text = "Lisa & Pelle - MMM Senaste Nytt"
        ET.SubElement(item, "itunes:subtitle").text = "Vardag  Nyheter - Människa Maskin Miljö"
        ET.SubElement(item, "itunes:summary").text = clean_xml_text(episode.get("description", ""))
    
    # Konvertera till string
    rss_str = ET.tostring(rss, encoding='unicode', method='xml')
    return rss_str

def generate_rss_feed(episodes: List[Dict], config: Dict) -> Dict:
    """
    Generera RSS feed för GitHub Pages
    
    Args:
        episodes: Lista med episod-data
        config: Podcast konfiguration
    
    Returns:
        dict: Resultat med local_path och content_length
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
        "content_length": len(rss_content),
        "public_url": f"{config.get('publicUrl', 'https://pontusdahlberg.github.io/morgonpodden')}/feed.xml"
    }
    
    print(f"✅ RSS feed sparad lokalt: {rss_file}")
    print(f"📝 Storlek: {len(rss_content)} tecken")
    
    return result

def load_episodes_from_history() -> List[Dict]:
    """Ladda episoder från episode_history.json"""
    try:
        with open('episode_history.json', 'r', encoding='utf-8') as f:
            episodes = json.load(f)
        
        # Konvertera till RSS-format
        rss_episodes = []
        for i, episode in enumerate(episodes):
            # Skapa audio URL från filename
            audio_url = f"https://pontusdahlberg.github.io/morgonpodden/audio/{episode['filename']}"
            
            # Konvertera datum till pubDate format
            try:
                date_obj = datetime.strptime(episode['date'], '%Y-%m-%d')
                pub_date = date_obj.strftime('%a, %d %b %Y 00:00:00 +0000')
            except:
                pub_date = "Mon, 01 Jan 2025 00:00:00 +0000"
            
            rss_episode = {
                "title": episode.get('title', f"MMM Senaste Nytt - {episode.get('date')}"),
                "description": episode.get('description', ''),
                "audio_url": audio_url,
                "guid": f"mmm-{episode.get('date', '2025-01-01')}",
                "pub_date": pub_date,
                "file_size": episode.get('size', 0),
                "duration": episode.get('duration', '8:00'),
                "date": episode.get('date')
            }
            rss_episodes.append(rss_episode)
        
        print(f"📚 Laddade {len(rss_episodes)} episoder från historik")
        return rss_episodes
        
    except FileNotFoundError:
        print("⚠️ episode_history.json hittades inte, använder tom lista")
        return []
    except Exception as e:
        print(f"❌ Fel vid laddning av episoder: {e}")
        return []

def test_rss_generation():
    """Test RSS generation för GitHub Pages"""
    print("=== RSS GENERATION TEST ===")
    
    # Ladda episoder från history
    episodes = load_episodes_from_history()
    
    # Konfiguration för GitHub Pages
    config = {
        "publicUrl": "https://pontusdahlberg.github.io/morgonpodden"
    }
    
    # Generera RSS
    result = generate_rss_feed(episodes, config)
    
    print("\n📊 RESULTAT:")
    print(f"   Lokal fil: {result.get('local_path')}")
    print(f"   Storlek: {result.get('content_length')} tecken")
    print(f"   Public URL: {result.get('public_url')}")
    print(f"   📡 Feed redo för GitHub Pages deployment!")
    
    print("\n🎯 NÄSTA STEG:")
    print("1. ✅ RSS feed är genererad")
    print("2. 🔄 Committa och pusha till GitHub")
    print("3. 📡 GitHub Pages uppdaterar automatiskt")
    print(f"4. 🔗 Feed URL: {result.get('public_url')}")
    
    # Visa början av feed för debug
    if os.path.exists(result.get('local_path', '')):
        print("\n--- RSS FEED PREVIEW ---")
        with open(result['local_path'], 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:500] + "...")

if __name__ == "__main__":
    test_rss_generation()