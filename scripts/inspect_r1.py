import json

with open('data/program_Bursa.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

r1 = data['races'][0]
print(f"Race 1: {r1.get('race_name')} | Distance: {r1.get('distance')} | Surface: {r1.get('surface')} | Track: {r1.get('track_condition')}")
print("="*80)
for r in r1['runners']:
    num = r.get('number')
    name = r.get('name')
    w = r.get('weight')
    j = r.get('jockey')
    l6 = r.get('last_6')
    h = r.get('handicap')
    bt = r.get('best_time')
    s20 = r.get('s20')
    comp = r.get('composite_rating')
    rank = r.get('rank')
    prob = r.get('win_probability')
    ta = r.get('time_analysis', {})
    ga = r.get('gallop_analysis', {})
    sa = r.get('surface_affinity', {})
    print(f"#{num:2d} {name:16s} | Rank:{rank:2d} | Prob:{prob:4.1f}% | Kilo:{w} | Jok:{j:12s} | Hand:{str(h):4s} | L6:{str(l6):18s} | BT:{str(bt):7s} | SpeedFig:{ta.get('speed_figure')} | GallopSc:{ga.get('gallop_score')} | SurfSc:{sa.get('score')}")
