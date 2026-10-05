import json, sys
sys.path.insert(0, '.')
from backend.prediction_engine import predict_race

with open('data/program_Bursa.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

res = predict_race(d['races'][0])
print('=== NEW PREDICTION RESULTS FOR BURSA RACE 1 ===')
for r in res['runners']:
    print(f"Rank #{r['rank']:2d} | #{r['number']:2d} {r['name'][:16]:16s} | WinProb: {r['win_probability']:4.1f}% | Jok: {r['jockey'][:10]:10s} | Comp: {r['composite_rating']:5.2f} | Tag: {r['value_tag']}")

print('\nBetting recommendations:')
print('Ganyan:', res['bet_recommendations'].get('ganyan'))
print('İkili:', res['bet_recommendations'].get('ikili'))
print('Sıralı İkili:', res['bet_recommendations'].get('sirali_ikili'))
print('3lü Bahis:', res['bet_recommendations'].get('uclu_bahis'))
print('Tabela Bahis:', res['bet_recommendations'].get('tabela_bahis'))
