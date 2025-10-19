import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('test_single_filter')

# Ladda scraped content
with open('scraped_content.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Hitta TechCrunch articles
techcrunch_data = None
for item in data:
    if item.get('source') == 'TechCrunch':
        techcrunch_data = item
        break

if techcrunch_data:
    articles = techcrunch_data.get('items', [])
    print(f"TechCrunch har {len(articles)} artiklar")
    
    # Testa första AI-artikeln
    test_article = None
    for article in articles:
        title = article.get('title', '').lower()
        if 'ai' in title:
            test_article = article
            break
    
    if test_article:
        print(f"\nTestar artikel: {test_article['title']}")
        
        # Samma filter som i run_podcast_complete.py
        title_text = test_article.get('title', '').lower()
        content_text = test_article.get('summary', '').lower()
        combined_text = title_text + " " + content_text
        
        # Irrelevanta ämnen
        irrelevant_keywords = [
            'våld', 'mord', 'knivskuren', 'skjutning', 'död', 'dödad',
            'krig', 'konflikt', 'gaza', 'palestina', 'palestinska', 'israel', 'ukraina',
            'knark', 'droger', 'narkotika', 'kriminell', 'polis', 'häktad',
            'val', 'politik', 'parti', 'regering', 'minister', 'kyrka', 'kyrkovalet',
            'sport', 'fotboll', 'hockey', 'motorsport', 'racing', 'trump', 'putin'
        ]
        
        # Relevanta nyckelord
        relevant_keywords = [
            'ai', 'artificiell intelligens', 'machine learning', 'maskininlärning',
            'teknik', 'teknologi', 'innovation', 'forskning', 'vetenskap',
            'datorer', 'mjukvara', 'app', 'digital', 'internet', 'cybersäkerhet',
            'klimat', 'miljö', 'hållbarhet', 'förnybar energi', 'koldioxid', 'co2'
        ]
        
        print(f"Kombinerad text: {combined_text[:100]}...")
        
        # Testa irrelevant filter
        has_irrelevant = any(keyword in combined_text for keyword in irrelevant_keywords)
        print(f"Har irrelevant innehåll: {has_irrelevant}")
        
        # Testa relevant filter  
        has_relevant = any(keyword in combined_text for keyword in relevant_keywords)
        relevant_matches = [kw for kw in relevant_keywords if kw in combined_text]
        print(f"Har relevant innehåll: {has_relevant}")
        print(f"Matchande nyckelord: {relevant_matches}")
        
        if not has_irrelevant and has_relevant:
            print("✅ ARTIKELN SKULLE PASSERA FILTRET")
        else:
            print("❌ ARTIKELN SKULLE FILTRERAS BORT")
    else:
        print("Ingen AI-artikel hittad i TechCrunch")