#!/usr/bin/env python3
"""
SMHI Väder Integration för MMM Senaste Nytt
Officiell svensk väderdata från SMHI:s öppna API
"""

import requests
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SMHIWeatherService:
    """Klass för att hämta väderdata från SMHI:s API"""
    
    # Svenska koordinater för representativa områden
    REGIONS = {
        "Götaland": {"lat": 57.7089, "lon": 11.9746, "city": "Göteborg"},
        "Svealand": {"lat": 59.3293, "lon": 18.0649, "city": "Stockholm"}, 
        "Södra Norrland": {"lat": 62.3875, "lon": 17.3069, "city": "Sundsvall"},
        "Norra Norrland": {"lat": 67.8558, "lon": 20.2253, "city": "Kiruna"}
    }
    
    # API URL för väderprognos
    API_BASE = "https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10
        
    def get_weather_symbol_description(self, symbol_code: int) -> str:
        """Konvertera SMHI:s vädersymbol till svensk beskrivning"""
        symbols = {
            1: "Klart",
            2: "Mestadels klart", 
            3: "Växlande molnighet",
            4: "Halvklart",
            5: "Molnigt",
            6: "Mulet",
            7: "Dimma",
            8: "Lätt regnskur",
            9: "Måttlig regnskur",
            10: "Kraftig regnskur",
            11: "Åskskur",
            12: "Lätt snöblandat regn",
            13: "Måttligt snöblandat regn",
            14: "Kraftigt snöblandat regn",
            15: "Lätt snöfall",
            16: "Måttligt snöfall",
            17: "Kraftigt snöfall",
            18: "Lätt regn",
            19: "Måttligt regn",
            20: "Kraftigt regn",
            21: "Åska",
            22: "Lätt snöblandat regn",
            23: "Måttligt snöblandat regn", 
            24: "Kraftigt snöblandat regn",
            25: "Lätt snöfall",
            26: "Måttligt snöfall",
            27: "Kraftigt snöfall"
        }
        return symbols.get(symbol_code, "Okänt väder")
    
    def get_wind_description(self, wind_speed_ms: float) -> str:
        """Konvertera vindstyrka från m/s till svensk beskrivning"""
        if wind_speed_ms < 3:
            return "svaga vindar"
        elif wind_speed_ms < 8:
            return "måttliga vindar"
        elif wind_speed_ms < 14:
            return "friska vindar"
        elif wind_speed_ms < 20:
            return "hårda vindar"
        else:
            return "mycket hårda vindar"
    
    def get_parameter_value(self, parameters: List[Dict], param_name: str) -> Optional[float]:
        """Extrahera specifik parameter från SMHI data"""
        for param in parameters:
            if param.get("name") == param_name:
                values = param.get("values", [])
                return values[0] if values else None
        return None
    
    def fetch_location_weather(self, lat: float, lon: float, city: str) -> Optional[Dict]:
        """Hämta väderdata för en specifik plats"""
        try:
            url = f"{self.API_BASE}/lon/{lon}/lat/{lat}/data.json"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Hitta aktuell timme eller närmaste framtida prognos
            current_time = datetime.now(timezone.utc)
            current_forecast = None
            
            for forecast in data.get("timeSeries", []):
                forecast_time = datetime.fromisoformat(forecast["validTime"].replace("Z", "+00:00"))
                if forecast_time >= current_time:
                    current_forecast = forecast
                    break
            
            if not current_forecast:
                logger.warning(f"Ingen aktuell prognos hittades för {city}")
                return None
            
            parameters = current_forecast.get("parameters", [])
            
            # Extrahera viktiga väderparametrar
            temperature = self.get_parameter_value(parameters, "t")  # Temperatur i Celsius
            wind_speed = self.get_parameter_value(parameters, "ws")  # Vindstyrka i m/s
            humidity = self.get_parameter_value(parameters, "r")     # Luftfuktighet i %
            weather_symbol = self.get_parameter_value(parameters, "Wsymb2")  # Vädersymbol
            precipitation = self.get_parameter_value(parameters, "pmean")  # Nederbörd

            # Räkna temperaturintervall (min/max) för kommande ~24h
            horizon = current_time + timedelta(hours=24)
            temps: List[float] = []
            for forecast in data.get("timeSeries", []):
                try:
                    forecast_time = datetime.fromisoformat(forecast["validTime"].replace("Z", "+00:00"))
                except Exception:
                    continue
                if forecast_time < current_time or forecast_time > horizon:
                    continue
                t_val = self.get_parameter_value(forecast.get("parameters", []), "t")
                if t_val is not None:
                    temps.append(float(t_val))

            temp_min = min(temps) if temps else temperature
            temp_max = max(temps) if temps else temperature
            
            return {
                "city": city,
                "temperature": temperature,
                "temp_min": temp_min,
                "temp_max": temp_max,
                "wind_speed": wind_speed,
                "humidity": humidity, 
                "weather_symbol": int(weather_symbol) if weather_symbol else None,
                "precipitation": precipitation,
                "forecast_time": current_forecast["validTime"]
            }
            
        except Exception as e:
            logger.error(f"Fel vid hämtning av väder för {city}: {e}")
            return None
    
    def get_swedish_weather_summary(self) -> str:
        """Hämta vädersammanfattning för hela Sverige"""
        try:
            weather_data = []
            
            for region_name, location in self.REGIONS.items():
                weather = self.fetch_location_weather(
                    location["lat"], 
                    location["lon"], 
                    location["city"]
                )
                
                if weather:
                    temp = weather["temperature"]
                    temp_min = weather.get("temp_min")
                    temp_max = weather.get("temp_max")
                    wind_speed = weather["wind_speed"]
                    symbol = weather["weather_symbol"]
                    
                    if temp is not None and wind_speed is not None and symbol is not None:
                        # Visa temperatur som intervall per landsdel (min–max) om möjligt
                        if temp_min is not None and temp_max is not None:
                            tmin_i = int(round(float(temp_min)))
                            tmax_i = int(round(float(temp_max)))
                            if tmin_i == tmax_i:
                                temp_str = f"{tmin_i} grader"
                            else:
                                # Undvik "-12--6"; använd "till" när negativa tal förekommer
                                # eller när intervallet korsar noll (för tydlighet med plus).
                                crosses_zero = tmin_i < 0 < tmax_i
                                has_negative = tmin_i < 0 or tmax_i < 0
                                if has_negative or crosses_zero:
                                    tmax_fmt = f"+{tmax_i}" if crosses_zero and tmax_i > 0 else f"{tmax_i}"
                                    temp_str = f"{tmin_i} till {tmax_fmt} grader"
                                else:
                                    temp_str = f"{tmin_i}-{tmax_i} grader"
                        else:
                            temp_str = f"{temp:.0f} grader"
                        weather_desc = self.get_weather_symbol_description(symbol)
                        wind_desc = self.get_wind_description(wind_speed)
                        
                        weather_data.append(f"{region_name}: {weather_desc}, {temp_str}, {wind_desc}")
                        
                        logger.info(f"[SMHI] {region_name}: {weather_desc}, {temp_str}, {wind_desc}")
            
            if weather_data:
                # Ta bara första två för kompakthet i podcasten
                summary = f"Vädret idag enligt SMHI: {'; '.join(weather_data)}"  # Visa alla regioner
                return summary
            else:
                return "Vädret idag: Varierande väderförhållanden över Sverige"
                
        except Exception as e:
            logger.error(f"[SMHI] Fel vid vädersammanfattning: {e}")
            return "Vädret idag: Varierande väderförhållanden över Sverige"

def get_swedish_weather() -> str:
    """Huvudfunktion för att hämta svensk väderdata från SMHI"""
    service = SMHIWeatherService()
    return service.get_swedish_weather_summary()

# Test-funktion
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    weather = get_swedish_weather()
    print(weather)