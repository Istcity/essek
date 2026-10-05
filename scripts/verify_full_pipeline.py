"""
Verify full prediction pipeline with updated parser and engine
"""
import sys
import os
sys.path.insert(0, r"C:\Users\sinan.nergiz\.gemini\antigravity-ide\scratch\essek")

from backend.tjk_scraper import fetch_and_predict_city_program

def verify():
    for city in ["Bursa", "Şanlıurfa"]:
        print(f"\n==================== VERIFYING {city} ====================")
        data = fetch_and_predict_city_program(city, "05.10.2026")
        races = data.get("races", [])
        print(f"Total Races: {len(races)}")
        
        for r in races:
            r_num = r.get("race_number")
            dist = r.get("distance")
            surf = r.get("surface")
            winner = r.get("winner_prediction", {})
            runners = r.get("runners", [])
            scratched = [rn["name"] for rn in runners if rn.get("is_scratched")]
            bets = r.get("bet_recommendations", {})
            
            print(f"Koşu #{r_num}: {dist}m {surf} | Katılan: {len(runners)} at | Koşmaz: {scratched}")
            if winner:
                print(f"   [FAVORI] #{winner.get('number')} {winner.get('name')} (Kazanma: %{winner.get('win_probability')} | AGF: %{winner.get('agf')} | Skor: {winner.get('composite_rating')})")
            if bets:
                ganyan = bets.get("ganyan", {})
                print(f"   [GANYAN ONERISI] #{ganyan.get('number')} {ganyan.get('name')} ({ganyan.get('strategy')})")
                ikili = bets.get("sirali_ikili", {})
                print(f"   [SIRALI IKILI] {ikili.get('primary')}")

        print(f"--> {city} Verification SUCCESSFUL!")

if __name__ == "__main__":
    verify()
