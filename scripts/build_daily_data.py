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
from backend.live_odds_service import get_live_odds_for_race

ROOT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FRONTEND_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "data")

def save_to_both(filename, obj):
    for d in [ROOT_DATA_DIR, FRONTEND_DATA_DIR]:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

def build_daily_data():
    today_str = datetime.now().strftime("%d.%m.%Y")
    print(f"Building daily data for: {today_str}")

    # 1. Fetch available cities
    cities = get_available_cities(today_str)
    save_to_both("today_cities.json", cities)
    print(f"Saved {len(cities)} cities to today_cities.json")

    # 2. Fetch and predict for each city
    all_programs = {}
    for city in cities:
        city_name = city["name"]
        print(f"Fetching program for {city_name}...")
        try:
            program = fetch_and_predict_city_program(city_name, today_str)
            
            # Enrich with live odds & 2'li ganyanlar
            for race in (program.get("races") or []):
                r_num = race.get("race_number", 1)
                runners = race.get("runners") or []
                try:
                    odds = get_live_odds_for_race(city_name, r_num, runners)
                    if odds and odds.get("success"):
                        race["is_live_odds"] = odds.get("is_live", False)
                        race["live_odds_source"] = odds.get("source", "TJK")
                        race["ikili_ganyanlar"] = odds.get("ikili_ganyanlar", [])
                        race["sirali_ikili_ganyanlar"] = odds.get("sirali_ikili", [])
                        g_map = {g["number"]: g["ganyan"] for g in odds.get("ganyanlar", []) if "number" in g and "ganyan" in g}
                        for r in runners:
                            rn = r.get("number")
                            if rn in g_map:
                                r["live_ganyan"] = g_map[rn]
                                r["ganyan"] = g_map[rn]
                except Exception:
                    pass

            all_programs[city_name] = program
            save_to_both(f"program_{city_name}.json", program)
            print(f" -> Saved {len(program.get('races', []))} races for {city_name}")
        except Exception as e:
            print(f" -> Error processing {city_name}: {e}")

    # 3. Save master all_programs.json
    save_to_both("all_programs.json", all_programs)
    print("Successfully built and enriched all daily data in both data/ and frontend/data/!")

if __name__ == "__main__":
    build_daily_data()
