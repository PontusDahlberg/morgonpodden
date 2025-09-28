# 🔒 GIT SÄKERHETSGUIDE - API-Nycklar & Känslig Data

## ⚠️ **KRITISKT: Skydda dina API-nycklar från att läcka till GitHub!**

### 🛡️ **Automatiskt skyddade filer** (via `.gitignore`)
```
✅ .env                           # Dina API-nycklar
✅ .env.*                         # Alla .env varianter  
✅ backups/**                     # Alla backup-filer
✅ google-cloud-service-account.json  # Google Cloud credentials
✅ api_keys_backup_*.json         # API-nyckel backupper
✅ api_keys_readable_*.txt        # Läsbara backupper
```

### 🚨 **Vad händer om känsliga filer läcker?**
- **GitHub är publikt** - alla kan se dina API-nycklar
- **Bots skannar** GitHub efter nycklar och använder dem
- **Kostnad explosion** - de kan köra upp enorma API-räkningar
- **Säkerhetsbrott** - Fullständig kontroll över dina tjänster

### 🔍 **Säkerhetskontroll innan commit**
Kör alltid dessa innan du committar:

```bash
# 1. Kontrollera vad som ska commitas
git status

# 2. Kontrollera att känsliga filer ignoreras
git check-ignore .env backups/

# 3. Se exakt vad som läggs till
git diff --cached
```

### ⚡ **Om du råkar commita API-nycklar**

**OMEDELBAR ÅTGÄRD:**
1. **Återkalla nycklar**: Logga in på alla tjänster och skapa nya nycklar
2. **Ta bort från git historik**:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' HEAD
   git push origin --force --all
   ```
3. **Uppdatera backupper** med nya nycklar

### 🔒 **Säkra commit-rutiner**

**Innan varje commit:**
```bash
# Säker commit-process
git add .
git status                        # Kontrollera vad som läggs till
git check-ignore .env backups/    # Verifiera att känsliga filer ignoreras
git diff --cached                 # Granska exakt vad som commitas
git commit -m "Din commit-message"
```

### 🎯 **Best Practices**

1. **Aldrig commit**:
   - `.env` filer
   - API-nycklar
   - Lösenord
   - Service account JSON
   - Backup-filer med credentials

2. **Alltid commit**:
   - `.env.local` (template utan riktiga nycklar)
   - Kodfiler
   - Dokumentation
   - README filer

3. **Dubbelkolla**:
   - Kör `git status` före commit
   - Granska `git diff --cached`
   - Använd `git check-ignore` för tveksamma filer

### 🚨 **Emergency: Om nycklar redan är på GitHub**

1. **Genast**: 
   - Gå till OpenRouter/Cloudflare/ElevenLabs
   - Radera gamla nycklar
   - Skapa nya nycklar

2. **Uppdatera lokalt**:
   ```bash
   python api_key_backup_manager.py backup  # Backup gamla
   # Uppdatera .env med nya nycklar
   python api_key_backup_manager.py backup  # Backup nya
   ```

3. **Städa git**:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' HEAD
   git push origin --force --all
   ```

### ✅ **Verifiering**

Kör detta för att kontrollera säkerheten:
```bash
# Kontrollera att .gitignore fungerar
git check-ignore .env backups/ 

# Lista alla trackade filer (inga känsliga ska visas)
git ls-tree -r --name-only HEAD | grep -E "(env|key|credential|backup)"
```

---
**🛡️ Kom ihåg: En läckt API-nyckel kan kosta tusentals kronor på minuter!**

*Skapad: 2025-09-28 | Människa Maskin Miljö Security Guide*