import json

# Ladda scraped content
with open('scraped_content.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Relevant keywords
relevant_keywords = [
    'ai', 'artificiell intelligens', 'machine learning', 'maskininlärning',
    'teknik', 'teknologi', 'innovation', 'forskning', 'vetenskap',
    'datorer', 'mjukvara', 'app', 'digital', 'internet', 'cybersäkerhet',
    'klimat', 'miljö', 'hållbarhet', 'förnybar energi', 'koldioxid', 'co2'
]

def test_article(title, content=""):
    combined = (title + " " + content).lower()
    matches = [kw for kw in relevant_keywords if kw in combined]
    return matches

# Testa några artiklar från TechCrunch och The Verge
test_articles = [
    "You can now text Spotify's AI DJ",
    "Japan wants OpenAI to stop ripping off manga and anime", 
    "Major federation of unions calls for 'worker-centered AI' future",
    "Faster, Smaller AI Model Found for Image Geolocation",
    "Teaching AI to Predict What Cells Will Look Like Before Running Any Experiments"
]

print("TESTRESULTAT:")
for article in test_articles:
    matches = test_article(article)
    print(f"'{article}' -> {matches} ({'PASS' if matches else 'FAIL'})")