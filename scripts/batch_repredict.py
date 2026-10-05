import os, json, sys
sys.path.insert(0, '.')
from backend.tjk_scraper import fetch_and_predict_city_program, get_available_cities

data_dir = 'data'
frontend_data_dir = 'frontend/data'
os.makedirs(data_dir, exist_ok=True)
os.makedirs(frontend_data_dir, exist_ok=True)

cities = ["Bursa", "Şanlıurfa"]
date_str = '05.10.2026'

print(f"Fetching fresh bulletin data and predicting for cities: {cities}...")
all_programs = {}

for city in cities:
    try:
        prog = fetch_and_predict_city_program(city, date_str)
        if prog and prog.get("races"):
            fname = f"program_{city}.json"
            fpath = os.path.join(data_dir, fname)
            frontend_path = os.path.join(frontend_data_dir, fname)
            
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(prog, f, ensure_ascii=False, indent=2)
            with open(frontend_path, 'w', encoding='utf-8') as f:
                json.dump(prog, f, ensure_ascii=False, indent=2)
                
            all_programs[city] = prog
            print(f"Successfully processed {city}: {len(prog['races'])} races")
    except Exception as e:
        print(f"Error fetching {city}: {e}")

# Save consolidated all_programs.json
with open(os.path.join(data_dir, 'all_programs.json'), 'w', encoding='utf-8') as f:
    json.dump(all_programs, f, ensure_ascii=False, indent=2)

with open(os.path.join(frontend_data_dir, 'all_programs.json'), 'w', encoding='utf-8') as f:
    json.dump(all_programs, f, ensure_ascii=False, indent=2)

print("Batch repredict and fresh bulletin sync completed successfully!")
