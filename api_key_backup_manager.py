#!/usr/bin/env python3
"""
🔐 API Key Backup Manager för Människa Maskin Miljö
Skapar säkra backupper av dina API-nycklar och hjälper dig återställa dem.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import getpass

class APIKeyBackupManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.backup_dir = self.project_root / "backups" / "credentials"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self):
        """Skapa en säker backup av API-nycklar"""
        print("🔐 SKAPAR SÄKER BACKUP AV API-NYCKLAR")
        print("=" * 50)
        
        # SÄKERHETSKONTROLL: Verifiera att backups ignoreras av git
        self._verify_git_ignore_security()
        
        if not self.env_file.exists():
            print("❌ .env fil saknas!")
            return
            
        # Läs .env filen
        env_vars = {}
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        # Identifiera API-nycklar
        api_keys = {}
        sensitive_patterns = [
            'API_KEY', 'TOKEN', 'SECRET', 'CREDENTIAL', 'PASSWORD'
        ]
        
        for key, value in env_vars.items():
            if any(pattern in key.upper() for pattern in sensitive_patterns):
                if value and value != 'your_' + key.lower() + '_here':
                    api_keys[key] = value
        
        if not api_keys:
            print("⚠️ Inga API-nycklar hittades att säkerhetskopiera")
            return
            
        # Skapa timestampad backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"api_keys_backup_{timestamp}.json"
        
        backup_data = {
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "project": "Människa Maskin Miljö",
            "api_keys": api_keys,
            "env_file_backup": str(self.env_file)
        }
        
        # Spara backup
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Backup skapad: {backup_file}")
        print(f"🔑 Säkerhetskopierade {len(api_keys)} API-nycklar:")
        for key in api_keys.keys():
            print(f"   - {key}")
            
        # Skapa också en human-readable backup
        readable_backup = self.backup_dir / f"api_keys_readable_{timestamp}.txt"
        with open(readable_backup, 'w', encoding='utf-8') as f:
            f.write(f"# API Keys Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Människa Maskin Miljö Podcast Project\n\n")
            for key, value in api_keys.items():
                f.write(f"{key}={value}\n")
                
        print(f"📄 Läsbar backup: {readable_backup}")
        return backup_file
    
    def list_backups(self):
        """Lista alla tillgängliga backupper"""
        print("📋 TILLGÄNGLIGA API-NYCKEL BACKUPPER")
        print("=" * 50)
        
        backups = list(self.backup_dir.glob("api_keys_backup_*.json"))
        backups.sort(reverse=True)  # Nyaste först
        
        if not backups:
            print("❌ Inga backupper hittades")
            return []
            
        for i, backup in enumerate(backups, 1):
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                timestamp = data.get('datetime', 'Unknown')
                key_count = len(data.get('api_keys', {}))
                print(f"{i}. {backup.name}")
                print(f"   Skapad: {timestamp}")
                print(f"   API-nycklar: {key_count}")
                print()
            except Exception as e:
                print(f"{i}. {backup.name} (fel vid läsning: {e})")
                
        return backups
    
    def restore_from_backup(self, backup_file=None):
        """Återställ API-nycklar från backup"""
        print("🔄 ÅTERSTÄLLA API-NYCKLAR FRÅN BACKUP")
        print("=" * 50)
        
        if backup_file is None:
            backups = self.list_backups()
            if not backups:
                return
                
            try:
                choice = int(input("Välj backup nummer att återställa från: ")) - 1
                if 0 <= choice < len(backups):
                    backup_file = backups[choice]
                else:
                    print("❌ Ogiltigt val")
                    return
            except ValueError:
                print("❌ Måste vara ett nummer")
                return
        
        # Läs backup
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
        except Exception as e:
            print(f"❌ Kunde inte läsa backup: {e}")
            return
            
        api_keys = backup_data.get('api_keys', {})
        if not api_keys:
            print("❌ Inga API-nycklar i backup")
            return
            
        # Bekräfta återställning
        print(f"📦 Backup från: {backup_data.get('datetime', 'Unknown')}")
        print(f"🔑 Innehåller {len(api_keys)} API-nycklar:")
        for key in api_keys.keys():
            print(f"   - {key}")
            
        confirm = input("\nVill du återställa dessa nycklar till .env? (j/N): ")
        if confirm.lower() not in ['j', 'ja', 'y', 'yes']:
            print("❌ Avbröt återställning")
            return
            
        # Backup nuvarande .env först
        if self.env_file.exists():
            backup_current = self.env_file.parent / f".env.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.env_file, backup_current)
            print(f"💾 Säkerhetskopierade nuvarande .env till {backup_current}")
        
        # Läs nuvarande .env för att behålla icke-API inställningar
        current_env = {}
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
            
        # Skriv ny .env med återställda API-nycklar
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(f"# Människa Maskin Miljö - Återställd från backup\n")
            f.write(f"# Återställd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Från backup: {backup_data.get('datetime', 'Unknown')}\n\n")
            
            # Skriv alla API-nycklar från backup
            for key, value in api_keys.items():
                f.write(f"{key}={value}\n")
                
            f.write("\n# Andra inställningar från .env.local template\n")
            f.write("USE_GOOGLE_CLOUD_TTS=true\n")
            f.write("GOOGLE_APPLICATION_CREDENTIALS=./google-cloud-service-account.json\n")
            f.write("PODCAST_TITLE=Människa Maskin Miljö\n")
            f.write("PODCAST_AUTHOR=Pontus - Människa Maskin Miljö\n")
            f.write("PODCAST_EMAIL=podcast@example.com\n")
            f.write("PODCAST_LANGUAGE=sv-SE\n")
            f.write("LOCAL_TEST_MODE=false\n")
            f.write("DEBUG_MODE=false\n")
            
        print(f"✅ API-nycklar återställda till .env")
        print(f"🔑 Återställde {len(api_keys)} API-nycklar")
        
    def verify_keys(self):
        """Verifiera att alla nödvändiga API-nycklar finns"""
        print("🔍 VERIFIERAR API-NYCKLAR")
        print("=" * 50)
        
        if not self.env_file.exists():
            print("❌ .env fil saknas!")
            return False
            
        # Läs .env
        env_vars = {}
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        # Obligatoriska nycklar
        required_keys = [
            'OPENROUTER_API_KEY',
            'CLOUDFLARE_API_TOKEN',
            'CLOUDFLARE_R2_ACCOUNT_ID',
            'CLOUDFLARE_R2_BUCKET'
        ]
        
        # Google Cloud eller ElevenLabs krävs
        tts_keys = [
            'GOOGLE_APPLICATION_CREDENTIALS',
            'ELEVENLABS_API_KEY'
        ]
        
        missing = []
        present = []
        
        # Kontrollera obligatoriska
        for key in required_keys:
            if key in env_vars and env_vars[key] and env_vars[key] != f'your_{key.lower()}_here':
                present.append(key)
                print(f"✅ {key}")
            else:
                missing.append(key)
                print(f"❌ {key} - SAKNAS")
        
        # Kontrollera TTS
        has_tts = False
        for key in tts_keys:
            if key in env_vars and env_vars[key] and env_vars[key] != f'your_{key.lower()}_here':
                present.append(key)
                print(f"✅ {key} (TTS)")
                has_tts = True
        
        if not has_tts:
            print("❌ Ingen TTS provider konfigurerad (Google Cloud eller ElevenLabs)")
            missing.extend(tts_keys)
            
        print(f"\n📊 RESULTAT:")
        print(f"✅ Konfigurerade: {len(present)}")
        print(f"❌ Saknade: {len(missing)}")
        
        if missing:
            print(f"\n🚨 ÅTGÄRD KRÄVS:")
            print("Du kan:")
            print("1. Köra 'python api_key_backup_manager.py restore' för att återställa från backup")
            print("2. Manuellt lägga till saknade nycklar i .env")
            
        return len(missing) == 0
    
    def _verify_git_ignore_security(self):
        """Verifiera att känsliga filer ignoreras av git"""
        import subprocess
        
        try:
            # Testa om .env ignoreras
            result = subprocess.run(
                ['git', 'check-ignore', '.env'],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode != 0:
                print("🚨 SÄKERHETSVARNING: .env filen ignoreras INTE av git!")
                print("⚠️  Risk: API-nycklar kan läcka till GitHub!")
                print("🔧 Åtgärd: Kontrollera .gitignore filen")
                return False
                
            # Testa om backup-mappen ignoreras  
            test_backup = self.backup_dir / "test.json"
            test_backup.parent.mkdir(parents=True, exist_ok=True)
            test_backup.write_text("{}")
            
            result = subprocess.run(
                ['git', 'check-ignore', str(test_backup)],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            test_backup.unlink()  # Ta bort testfil
            
            if result.returncode != 0:
                print("🚨 SÄKERHETSVARNING: Backup-filer ignoreras INTE av git!")
                print("⚠️  Risk: API-nycklar kan läcka till GitHub!")
                print("🔧 Åtgärd: Uppdatera .gitignore med 'backups/**'")
                return False
                
            print("🛡️ Git säkerhet: Känsliga filer skyddade ✅")
            return True
            
        except Exception as e:
            print(f"⚠️ Kunde inte verifiera git säkerhet: {e}")
            print("🔧 Kontrollera manuellt att .env och backups/ finns i .gitignore")
            return False

def main():
    manager = APIKeyBackupManager()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1].lower()
        
        if command == 'backup':
            manager.create_backup()
        elif command == 'list':
            manager.list_backups()
        elif command == 'restore':
            manager.restore_from_backup()
        elif command == 'verify':
            manager.verify_keys()
        else:
            print(f"❌ Okänt kommando: {command}")
            print("Tillgängliga kommandon: backup, list, restore, verify")
    else:
        print("🔐 API KEY BACKUP MANAGER - Människa Maskin Miljö")
        print("=" * 60)
        print("Kommandon:")
        print("  python api_key_backup_manager.py backup   - Skapa backup")
        print("  python api_key_backup_manager.py list     - Lista backupper") 
        print("  python api_key_backup_manager.py restore  - Återställ från backup")
        print("  python api_key_backup_manager.py verify   - Verifiera nuvarande nycklar")
        print()
        
        # Kör interaktiv meny
        while True:
            print("\nVälj en åtgärd:")
            print("1. 🔐 Skapa backup av API-nycklar")
            print("2. 📋 Lista tillgängliga backupper")
            print("3. 🔄 Återställ från backup")
            print("4. 🔍 Verifiera nuvarande nycklar")
            print("5. 🚪 Avsluta")
            
            try:
                choice = input("Ditt val (1-5): ").strip()
                
                if choice == '1':
                    manager.create_backup()
                elif choice == '2':
                    manager.list_backups()
                elif choice == '3':
                    manager.restore_from_backup()
                elif choice == '4':
                    manager.verify_keys()
                elif choice == '5':
                    print("👋 Hej då!")
                    break
                else:
                    print("❌ Ogiltigt val. Välj 1-5.")
            except KeyboardInterrupt:
                print("\n👋 Avbröt!")
                break

if __name__ == "__main__":
    main()