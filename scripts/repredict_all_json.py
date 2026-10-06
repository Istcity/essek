"""
Repredict all program files using the upgraded Engine v5.0 (18-Factor Deep Empirical Engine).
Syncs to both data/ and frontend/data/.
"""

import os
import sys
import json
import glob

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except:
        pass

sys.path.insert(0, r"C:\Users\sinan.nergiz\.gemini\antigravity-ide\scratch\essek")
from backend.prediction_engine import predict_race

DATA_DIR = "data"
FRONTEND_DATA_DIR = "frontend/data"

os.makedirs(FRONTEND_DATA_DIR, exist_ok=True)

files = glob.glob(os.path.join(DATA_DIR, "program_*.json"))
print(f"Found {len(files)} program files to re-predict with Engine v5.0...")

all_programs = {}

for fpath in files:
    fname = os.path.basename(fpath)
    city_name = fname.replace("program_", "").replace(".json", "")
    
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            prog = json.load(f)
            
        races = prog.get("races", [])
        if not races:
            continue
            
        new_races = []
        for race in races:
            predicted_race = predict_race(race)
            new_races.append(predicted_race)
            
        prog["races"] = new_races
        prog["engine_version"] = "v5.0_deep_empirical_18_factors"
        
        # Save to data/
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(prog, f, ensure_ascii=False, indent=2)
            
        # Save to frontend/data/
        frontend_path = os.path.join(FRONTEND_DATA_DIR, fname)
        with open(frontend_path, "w", encoding="utf-8") as f:
            json.dump(prog, f, ensure_ascii=False, indent=2)
            
        all_programs[city_name] = prog
        print(f"✓ Re-predicted {city_name}: {len(new_races)} races with 18 factors & winning factors")
    except Exception as e:
        print(f"✗ Error processing {fname}: {e}")

# Save consolidated all_programs.json
with open(os.path.join(DATA_DIR, "all_programs.json"), "w", encoding="utf-8") as f:
    json.dump(all_programs, f, ensure_ascii=False, indent=2)

with open(os.path.join(FRONTEND_DATA_DIR, "all_programs.json"), "w", encoding="utf-8") as f:
    json.dump(all_programs, f, ensure_ascii=False, indent=2)

print("\nAll programs successfully re-predicted and synced to frontend/data/!")
