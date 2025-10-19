import json
from datetime import datetime

# Ladda scraped content
with open('scraped_content.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Hitta TechCrunch
techcrunch_data = None
for item in data:
    if item.get('source') == 'TechCrunch':
        techcrunch_data = item
        break

if techcrunch_data:
    articles = techcrunch_data.get('items', [])
    print("TechCrunch artiklar och timestamps:")
    
    for i, article in enumerate(articles[:5], 1):
        title = article.get('title', 'No title')[:60]
        timestamp = article.get('timestamp', 'No timestamp')
        published = article.get('published', 'No published date')
        
        print(f"{i}. {title}")
        print(f"   Timestamp: {timestamp}")
        print(f"   Published: {published}")
        print()

# Kolla också när filen senast uppdaterades
import os
file_time = datetime.fromtimestamp(os.path.getmtime('scraped_content.json'))
print(f"scraped_content.json senast uppdaterad: {file_time}")