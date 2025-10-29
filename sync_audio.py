#!/usr/bin/env python3
"""
Synkar audio-filer från public/audio till audio/
Körs efter varje git pull för att få senaste avsnitt lokalt
"""

import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_audio():
    """Kopiera nya filer från public/audio till audio/"""
    source_dir = Path("public/audio")
    dest_dir = Path("audio")
    
    # Skapa audio/ om den inte finns
    dest_dir.mkdir(exist_ok=True)
    
    if not source_dir.exists():
        logger.warning(f"⚠️ {source_dir} finns inte")
        return
    
    # Hitta alla MP3-filer i källan
    source_files = list(source_dir.glob("MMM_senaste_nytt_*.mp3"))
    
    copied = 0
    skipped = 0
    
    for source_file in source_files:
        dest_file = dest_dir / source_file.name
        
        # Kopiera om filen inte finns eller är äldre
        if not dest_file.exists() or source_file.stat().st_mtime > dest_file.stat().st_mtime:
            logger.info(f"📥 Kopierar {source_file.name}")
            shutil.copy2(source_file, dest_file)
            copied += 1
        else:
            skipped += 1
    
    logger.info(f"✅ Synkning klar: {copied} kopierade, {skipped} hoppade över")

if __name__ == "__main__":
    sync_audio()
