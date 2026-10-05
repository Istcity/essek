"""
Daily TJK Data Pre-builder.
Scrapes today's race programs from TJK CDN, runs AI prediction engine,
and generates static JSON files in frontend/data/ for GitHub Pages.
"""

import os
import sys
import json
import urllib.parse
from datetime import datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tjk_scraper import get_available_cities, fetch_and_predict_city_program

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "data")

def build_daily_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%d.%m.%Y")
    print(f"Building daily data for: {today_str}")

    # 1. Fetch available cities
    cities = get_available_cities(today_str)
    cities_file = os.path.join(DATA_DIR, "today_cities.json")
    with open(cities_file, "w", encoding="utf-8") as f:
        json.dump(cities, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(cities)} cities to {cities_file}")

    # 2. Fetch and predict for each city
    all_programs = {}
    for city in cities:
        city_name = city["name"]
        print(f"Fetching program for {city_name}...")
        try:
            program = fetch_and_predict_city_program(city_name, today_str)
            all_programs[city_name] = program
            
            # Save individual city program
            safe_city_name = urllib.parse.quote_plus(city_name)
            city_file = os.path.join(DATA_DIR, f"program_{city_name}.json")
            with open(city_file, "w", encoding="utf-8") as f:
                json.dump(program, f, ensure_ascii=False, indent=2)
            print(f" -> Saved {len(program.get('races', []))} races for {city_name}")
        except Exception as e:
            print(f" -> Error processing {city_name}: {e}")

    # 3. Save master program.json
    master_file = os.path.join(DATA_DIR, "all_programs.json")
    with open(master_file, "w", encoding="utf-8") as f:
        json.dump(all_programs, f, ensure_ascii=False, indent=2)
    print("Successfully built all daily data!")

if __name__ == "__main__":
    build_daily_data()
