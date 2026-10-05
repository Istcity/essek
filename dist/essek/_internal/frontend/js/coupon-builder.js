/**
 * Altılı Ganyan & Bet Ticket Assistant.
 * Generates automated or custom tickets with unit price calculation and banko/surprise strategies.
 */

class CouponBuilder {
  constructor(containerId, summaryId) {
    this.container = document.getElementById(containerId);
    this.summary = document.getElementById(summaryId);
    this.races = [];
    this.selectedLegs = {}; // { legIndex: [horseNumbers] }
    this.unitPrice = 0.40; // TJK Standard unit price per combo
  }

  loadProgram(programData) {
    if (!programData || !programData.races) return;
    // Usually Altılı Ganyan starts from race 2 or 3 (6 consecutive races)
    const allRaces = programData.races;
    if (allRaces.length >= 6) {
      // Last 6 races or starting from race 2/3
      const startIdx = Math.max(0, allRaces.length - 6);
      this.races = allRaces.slice(startIdx, startIdx + 6);
    } else {
      this.races = allRaces;
    }

    // Default strategy: Ideal
    this.generateAutoTicket('ideal');
    this.render();
  }

  generateAutoTicket(strategy = 'ideal') {
    this.selectedLegs = {};
    this.races.forEach((race, legIdx) => {
      const runners = race.runners || [];
      if (!runners.length) return;

      this.selectedLegs[legIdx] = [];

      if (strategy === 'economic') {
        // Leg 1 or highest confidence race is a Banko (Rank 1)
        if (legIdx === 0 || legIdx === 3) {
          this.selectedLegs[legIdx].push(runners[0].number);
        } else {
          // Top 2 runners
          this.selectedLegs[legIdx] = runners.slice(0, 2).map(r => r.number);
        }
      } else if (strategy === 'ideal') {
        // 1 Banko, others top 3
        if (runners[0].win_probability >= 28.0) {
          this.selectedLegs[legIdx].push(runners[0].number);
        } else {
          this.selectedLegs[legIdx] = runners.slice(0, 3).map(r => r.number);
        }
      } else if (strategy === 'surprise') {
        // Top 2 + value bet / surprise runner
        const picks = runners.slice(0, 2).map(r => r.number);
        const valueBet = runners.find(r => r.is_value_bet);
        if (valueBet && !picks.includes(valueBet.number)) {
          picks.push(valueBet.number);
        }
        if (picks.length < 4 && runners[3]) picks.push(runners[3].number);
        this.selectedLegs[legIdx] = picks;
      }
    });

    this.render();
  }

  toggleHorse(legIdx, horseNumber) {
    if (!this.selectedLegs[legIdx]) this.selectedLegs[legIdx] = [];
    const idx = this.selectedLegs[legIdx].indexOf(horseNumber);
    if (idx > -1) {
      if (this.selectedLegs[legIdx].length > 1) {
        this.selectedLegs[legIdx].splice(idx, 1);
      }
    } else {
      this.selectedLegs[legIdx].push(horseNumber);
    }
    this.render();
  }

  calculateTotalCombos() {
    let combos = 1;
    let validLegs = 0;
    Object.keys(this.selectedLegs).forEach(legIdx => {
      const count = this.selectedLegs[legIdx].length;
      if (count > 0) {
        combos *= count;
        validLegs++;
      }
    });
    return validLegs === this.races.length ? combos : 0;
  }

  render() {
    if (!this.container || !this.summary) return;

    let html = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem; flex-wrap:wrap; gap:0.8rem;">
        <h3 style="font-family:var(--font-heading); font-size:1.1rem; font-weight:700;">
          🎫 Altılı Ganyan Şablonu (${this.races.length} Ayak)
        </h3>
        <div style="display:flex; gap:0.5rem;">
          <button class="btn-glass" onclick="window.couponApp.generateAutoTicket('economic')">⚡ Ekonomik</button>
          <button class="btn-glass" onclick="window.couponApp.generateAutoTicket('ideal')">🎯 İdeal Şablon</button>
          <button class="btn-glass" onclick="window.couponApp.generateAutoTicket('surprise')">💣 Bomba / Sürpriz</button>
        </div>
      </div>
    `;

    this.races.forEach((race, legIdx) => {
      const selected = this.selectedLegs[legIdx] || [];
      const isBanko = selected.length === 1;

      html += `
        <div class="coupon-leg-row">
          <div class="coupon-leg-header">
            <div>
              <strong style="color:var(--text-main); font-size:0.9rem;">${legIdx + 1}. Ayak: ${race.name}</strong>
              <span style="font-size:0.75rem; color:var(--text-secondary); margin-left:0.5rem;">(${race.distance}m ${race.surface})</span>
            </div>
            <div>
              ${isBanko ? '<span style="font-size:0.7rem; font-weight:700; background:rgba(245,158,11,0.2); color:var(--gold-400); padding:0.15rem 0.5rem; border-radius:4px; border:1px solid var(--gold-500);">⭐ BANKO</span>' : `<span style="font-size:0.75rem; color:var(--text-muted);">${selected.length} At Seçili</span>`}
            </div>
          </div>
          <div class="leg-horse-pills">
            ${(race.runners || []).map(r => {
              const isSel = selected.includes(r.number);
              const isTop = r.rank === 1;
              return `
                <button class="coupon-horse-btn ${isSel ? 'selected' : ''} ${isBanko && isSel ? 'banko' : ''}"
                        onclick="window.couponApp.toggleHorse(${legIdx}, ${r.number})">
                  #${r.number} ${r.name.split(' ')[0]} ${isTop ? '🏆' : ''} (${r.win_probability}%)
                </button>
              `;
            }).join('')}
          </div>
        </div>
      `;
    });

    this.container.innerHTML = html;

    // Render Summary Card
    const combos = this.calculateTotalCombos();
    const cost = (combos * this.unitPrice).toFixed(2);

    this.summary.innerHTML = `
      <div class="coupon-summary-sticky">
        <h4 style="font-family:var(--font-heading); font-size:1.1rem; font-weight:700; margin-bottom:0.85rem;">
          📊 Kupon Hesap Özeti
        </h4>
        <div style="font-size:0.85rem; color:var(--text-secondary); display:flex; flex-direction:column; gap:0.5rem;">
          <div style="display:flex; justify-content:space-between;">
            <span>Koşu Sayısı:</span>
            <strong style="color:var(--text-main);">${this.races.length} Koşu</strong>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span>Birim Fiyat:</span>
            <strong style="color:var(--text-main);">${this.unitPrice.toFixed(2)} TL</strong>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span>Toplam Kombinasyon:</span>
            <strong style="color:var(--emerald-400); font-size:1.1rem;">${combos.toLocaleString()} Adet</strong>
          </div>
        </div>

        <div class="summary-cost-box">
          <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">
            Tahmini Kupon Tutarı
          </div>
          <div class="summary-cost-value">
            ${cost} <small style="font-size:1rem; font-weight:600; color:var(--text-muted);">TL</small>
          </div>
        </div>

        <button class="btn-primary" style="width:100%; justify-content:center; margin-top:1.2rem; padding:0.75rem;" onclick="window.couponApp.copyTicket()">
          📋 Kupon Kodunu / Şablonu Kopyala
        </button>
      </div>
    `;
  }

  copyTicket() {
    let text = `TJK AI ALTILI GANYAN ŞABLONU\n`;
    this.races.forEach((r, idx) => {
      const sel = this.selectedLegs[idx] || [];
      text += `${idx + 1}. Ayak (${r.name}): ${sel.join(', ')}\n`;
    });
    const combos = this.calculateTotalCombos();
    text += `Toplam Kombinasyon: ${combos} | Tutar: ${(combos * this.unitPrice).toFixed(2)} TL`;

    navigator.clipboard.writeText(text).then(() => {
      alert("Kupon şablonu panoya kopyalandı!");
    });
  }
}

window.CouponBuilder = CouponBuilder;
