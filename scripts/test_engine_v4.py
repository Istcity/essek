"""Quick test for prediction engine v4.0"""
import sys
import os
sys.path.insert(0, r"C:\Users\sinan.nergiz\.gemini\antigravity-ide\scratch\essek")

from backend.prediction_engine import predict_race

test_race = {
  'race_number': 1, 'distance': 1400, 'surface': 'Kum',
  'race_type': 'Sartli', 'name': 'Test Kosusu',
  'record_time': '1.24.50', 'track_condition': 'Normal',
  'runners': [
    {'number': 1, 'name': 'AT BIR', 'jockey': 'V.Abis', 'weight': 60.0, 'gate': 2,
     'agf': 35.5, 'handicap': 70, 'last_6': 'K1K2K1K3K1K2', 'sire': 'Kaneko',
     'dam': 'Guzel', 'age': '4y', 'kgs': 20, 'gallops': None, 'equipment': ''},
    {'number': 2, 'name': 'AT IKI', 'jockey': 'Sal.Celik', 'weight': 55.0, 'gate': 8,
     'agf': 12.3, 'handicap': 55, 'last_6': 'K3K4K5K3K4K3', 'sire': 'Turbo',
     'dam': 'Hizli', 'age': '5y', 'kgs': 15, 'gallops': None, 'equipment': 'GKR'},
    {'number': 3, 'name': 'AT UC', 'jockey': 'A.Kursun', 'weight': 58.0, 'gate': 4,
     'agf': 22.0, 'handicap': 63, 'last_6': 'K2K1K2K2K3K2', 'sire': 'Torok',
     'dam': 'Guclu', 'age': '3y', 'kgs': 12, 'gallops': None, 'equipment': 'DB'},
  ]
}

result = predict_race(test_race)
print("--- PREDICTION ENGINE v4.0 TEST ---")
for r in result['runners']:
    print(f"Rank {r['rank']}: #{r['number']} {r['name']}")
    print(f"  AGF Score: {r.get('agf_score', 0):.1f} | Class-Weight: {r.get('class_weight_score',0):.1f}")
    print(f"  Gate Bonus: {r.get('gate_bonus',0):.2f} | Gear Mod: {r.get('gear_mod',0):.2f}")
    print(f"  Composite: {r['composite_rating']:.2f} | Win%: {r['win_probability']:.1f}%")
    print()
print("Engine OK!")
