import os, json, sys, glob
sys.path.insert(0, '.')
from backend.prediction_engine import predict_race

data_dir = 'data'
frontend_data_dir = 'frontend/data'
os.makedirs(frontend_data_dir, exist_ok=True)

files = glob.glob(os.path.join(data_dir, 'program_*.json'))
print(f"Repredicting {len(files)} program files...")

all_programs = {}

for fpath in files:
    fname = os.path.basename(fpath)
    city_name = fname.replace('program_', '').replace('.json', '')
    with open(fpath, 'r', encoding='utf-8') as f:
        prog = json.load(f)
        
    races = prog.get('races', [])
    updated_races = []
    for race in races:
        updated = predict_race(race)
        updated_races.append(updated)
        
    prog['races'] = updated_races
    
    # Save back to data/
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(prog, f, ensure_ascii=False, indent=2)
        
    # Save to frontend/data/
    frontend_path = os.path.join(frontend_data_dir, fname)
    with open(frontend_path, 'w', encoding='utf-8') as f:
        json.dump(prog, f, ensure_ascii=False, indent=2)
        
    all_programs[city_name] = prog
    print(f"Updated {fname}: {len(updated_races)} races")

# Save all_programs.json
with open(os.path.join(data_dir, 'all_programs.json'), 'w', encoding='utf-8') as f:
    json.dump(all_programs, f, ensure_ascii=False, indent=2)

with open(os.path.join(frontend_data_dir, 'all_programs.json'), 'w', encoding='utf-8') as f:
    json.dump(all_programs, f, ensure_ascii=False, indent=2)

print("All programs repredicted and synchronized successfully!")
