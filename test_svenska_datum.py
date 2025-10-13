#!/usr/bin/env python3
"""
Test av svenska datum
"""
from datetime import datetime

# Test svenska månadsnamn
today = datetime.now()

# Svenska månadsnamn
swedish_months = {
    1: 'januari', 2: 'februari', 3: 'mars', 4: 'april', 5: 'maj', 6: 'juni',
    7: 'juli', 8: 'augusti', 9: 'september', 10: 'oktober', 11: 'november', 12: 'december'
}
swedish_weekdays = {
    'Monday': 'måndag', 'Tuesday': 'tisdag', 'Wednesday': 'onsdag',
    'Thursday': 'torsdag', 'Friday': 'fredag', 'Saturday': 'lördag', 'Sunday': 'söndag'
}

month_swedish = swedish_months[today.month]
weekday_swedish = swedish_weekdays[today.strftime('%A')]

print("🗓️ DATUM-TEST:")
print(f"Engelska: {today.strftime('%A, %d %B %Y')}")
print(f"Svenska: {weekday_swedish}, {today.strftime('%d')} {month_swedish} {today.year}")
print(f"Titel: MMM Senaste Nytt - {today.strftime('%d')} {month_swedish} {today.year}")
print(f"Beskrivning: ...{weekday_swedish} den {today.strftime('%d')} {month_swedish} {today.year}")