#!/usr/bin/env python3
"""
SÄKERHETSKONTROLL - Kör före varje commit
Kontrollerar att inga secrets läcker ut
"""

import os
import re
import glob
import sys
from typing import List, Tuple

def check_hardcoded_secrets() -> List[Tuple[str, str]]:
    """Sök efter hårdkodade secrets i alla Python-filer"""
    violations = []
    
    # Mönster för olika typer av secrets
    patterns = {
        'ElevenLabs API Key': r'sk_[a-zA-Z0-9]{47,}',
        'OpenRouter API Key': r'sk-or-v1-[a-zA-Z0-9]{64,}',
        'Generic API Key': r'api_key\s*=\s*["\'][a-zA-Z0-9_-]{20,}["\']',
        'Bearer Token': r'Bearer\s+[a-zA-Z0-9_-]{20,}',
        'Secret Key': r'secret_key\s*=\s*["\'][a-zA-Z0-9_-]{20,}["\']'
    }
    
    # Kontrollerba alla Python-filer i projektets rotkatalog
    for py_file in glob.glob("*.py"):
        # Skippa säkra filer
        if py_file.startswith('secure_'):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for pattern_name, pattern in patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Kontrollera att det inte är en kommentar eller dokumentation
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line = content[line_start:content.find('\n', match.start())]
                    
                    # Skippa kommentarer och dokumentation
                    if line.strip().startswith('#') or '"""' in line or "'''" in line:
                        continue
                    
                    violations.append((py_file, f"{pattern_name}: {match.group()[:20]}..."))
        except Exception as e:
            print(f"⚠️ Kunde inte läsa {py_file}: {e}")
    
    return violations

def check_env_gitignore() -> bool:
    """Kontrollera att .env är i .gitignore"""
    if not os.path.exists('.gitignore'):
        return False
    
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    return '.env' in gitignore_content

def check_no_env_in_git() -> bool:
    """Kontrollera att .env inte är tracked av git"""
    import subprocess
    try:
        result = subprocess.run(['git', 'ls-files', '.env'], 
                              capture_output=True, text=True)
        return result.returncode != 0 or not result.stdout.strip()
    except:
        return True  # Om git inte finns, anta att det är OK

def main():
    """Huvudfunktion för säkerhetskontroll"""
    print("🔐 SÄKERHETSKONTROLL")
    print("=" * 50)
    
    all_checks_passed = True
    
    # 1. Kontrollera hårdkodade secrets
    print("🔍 Söker efter hårdkodade secrets...")
    violations = check_hardcoded_secrets()
    
    if violations:
        print("❌ HÅRDKODADE SECRETS HITTADE:")
        for file, violation in violations:
            print(f"  {file}: {violation}")
        all_checks_passed = False
    else:
        print("✅ Inga hårdkodade secrets hittade")
    
    # 2. Kontrollera .env i .gitignore
    print("\n🔍 Kontrollerar .gitignore...")
    if check_env_gitignore():
        print("✅ .env är skyddad i .gitignore")
    else:
        print("❌ .env saknas i .gitignore")
        all_checks_passed = False
    
    # 3. Kontrollera att .env inte är tracked
    print("\n🔍 Kontrollerar git tracking...")
    if check_no_env_in_git():
        print("✅ .env är inte tracked av git")
    else:
        print("❌ .env är tracked av git - TA BORT OMEDELBART!")
        all_checks_passed = False
    
    # Sammanfattning
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("✅ ALLA SÄKERHETSKONTROLLER GODKÄNDA")
        print("Säkert att fortsätta med commit")
        return 0
    else:
        print("❌ SÄKERHETSKONTROLLER MISSLYCKADES")
        print("FIX PROBLEMEN INNAN COMMIT!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
