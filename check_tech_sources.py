import json

# Ladda scraped content
with open('scraped_content.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

tech_sources = ['Computer Sweden', 'Ny Teknik', 'Breakit Tech', 'TechCrunch', 'The Verge', 'MIT Technology Review', 'Wired', 'IEEE Spectrum']

for source_name in tech_sources:
    # Hitta source i data-listan
    source_data = None
    for item in data:
        if item.get('source') == source_name:
            source_data = item
            break
    
    if source_data:
        articles = source_data.get('items', [])
        print(f"\n=== {source_name.upper()} ({len(articles)} artiklar) ===")
        
        if articles:
            for i, article in enumerate(articles[:3], 1):
                title = article.get('title', 'No title')
                print(f"{i}. {title}")
        else:
            print("Inga artiklar!")
    else:
        print(f"\n=== {source_name.upper()} ===")
        print("Källa inte hittad!")