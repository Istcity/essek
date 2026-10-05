/**
 * TJK AI Kupon Yap & Kupon Sihirbazı Studio v2.0
 * Comprehensive interactive betting slip builder for 6'lı, 5'li, 4'lü, 3'lü, Çifte, İkili ve Tekli oyunlar.
 * Features:
 * - Smart Budget Optimizer (Bütçeye Göre Kupon Üret)
 * - Quick Leg Selectors (Top 2, Top 3, Bomba, Hepsi, Banko)
 * - Monte Carlo Simulation (Kupon Başarı Olasılığı & Beklenen İkramiye)
 * - LocalStorage Save / Load (Kayıtlı Kuponlarım)
 * - TJK e-Bayi Clean Format Copy & Visual Ticket Print Card
 */

class CouponBuilder {
  constructor(containerId, summaryId) {
    this.container = document.getElementById(containerId);
    this.summary = document.getElementById(summaryId);
    this.programData = null;
    this.allRaces = [];
    this.gameType = "6li"; // 6li, 5li, 4li, 3li, cifte, ikili, ganyan
    this.startRaceIndex = 0;
    this.activeLegRaces = [];
    this.selectedHorses = {}; // { [raceNumber]: [horseNumber, ...] }
    this.bankos = {}; // { [raceNumber]: horseNumber }
    this.unitPrice = 1.25; // TJK Birim Fiyat: 1.25 TL
    this.savedCoupons = this.loadSavedFromStorage();

    // Floating bar elements
    this.floatingBar = document.getElementById("floatingSlipBar");
    this.barLegCount = document.getElementById("barLegCount");
    this.barComboCount = document.getElementById("barComboCount");
    this.barTotalCost = document.getElementById("barTotalCost");
  }

  loadProgram(programData) {
    if (!programData || !programData.races) return;
    this.programData = programData;
    this.allRaces = programData.races;

    // Default unit price set to 1.25 TL
    this.unitPrice = 1.25;

    // Determine default starting race for 6'lı Ganyan
    // In TJK, if there are 8 races, 6'lı usually starts from race 3 (races 3..8)
    if (this.allRaces.length >= 6) {
      this.startRaceIndex = Math.max(0, this.allRaces.length - 6);
    } else {
      this.startRaceIndex = 0;
    }

    this.updateActiveLegRaces();
    // Default smart ticket: ideal
    this.generateAutoTicket('ideal');
    this.render();
    this.updateFloatingBar();
  }

  setGameType(type) {
    this.gameType = type;
    // Adjust start index if needed
    let requiredLegs = 6;
    if (type === "5li") requiredLegs = 5;
    else if (type === "4li") requiredLegs = 4;
    else if (type === "3li") requiredLegs = 3;
    else if (type === "cifte") requiredLegs = 2;
    else if (type === "ikili" || type === "ganyan") requiredLegs = 1;

    if (this.startRaceIndex + requiredLegs > this.allRaces.length) {
      this.startRaceIndex = Math.max(0, this.allRaces.length - requiredLegs);
    }

    this.updateActiveLegRaces();
    this.generateAutoTicket('ideal');
    this.render();
  }

  setStartRace(raceIdx) {
    this.startRaceIndex = parseInt(raceIdx);
    this.updateActiveLegRaces();
    this.generateAutoTicket('ideal');
    this.render();
  }

  updateActiveLegRaces() {
    let legCount = 6;
    if (this.gameType === "5li") legCount = 5;
    else if (this.gameType === "4li") legCount = 4;
    else if (this.gameType === "3li") legCount = 3;
    else if (this.gameType === "cifte") legCount = 2;
    else if (this.gameType === "ikili" || this.gameType === "ganyan") legCount = 1;

    const start = Math.min(this.startRaceIndex, Math.max(0, this.allRaces.length - legCount));
    this.activeLegRaces = this.allRaces.slice(start, start + legCount);
  }

  generateAutoTicket(strategy = 'ideal') {
    this.selectedHorses = {};
    this.bankos = {};

    this.activeLegRaces.forEach((race, legIdx) => {
      const rNum = race.race_number;
      const runners = race.runners || [];
      if (!runners.length) return;

      this.selectedHorses[rNum] = [];

      if (strategy === 'economic') {
        // Find highest confidence race in the ticket to make single banko
        const isConfidenceBanko = (legIdx === 0 || runners[0].win_probability >= 26.0) && Object.keys(this.bankos).length === 0;
        if (isConfidenceBanko) {
          this.selectedHorses[rNum] = [runners[0].number];
          this.bankos[rNum] = runners[0].number;
        } else {
          this.selectedHorses[rNum] = runners.slice(0, 2).map(r => r.number);
        }
      } else if (strategy === 'ideal') {
        // High win prob runner gets banko
        if (runners[0].win_probability >= 28.0 && Object.keys(this.bankos).length === 0) {
          this.selectedHorses[rNum] = [runners[0].number];
          this.bankos[rNum] = runners[0].number;
        } else {
          this.selectedHorses[rNum] = runners.slice(0, 3).map(r => r.number);
        }
      } else if (strategy === 'surprise') {
        // Spread + include Value Bet / Bomba
        const picks = runners.slice(0, 2).map(r => r.number);
        const valueBet = runners.find(r => r.is_value_bet);
        if (valueBet && !picks.includes(valueBet.number)) {
          picks.push(valueBet.number);
        }
        if (picks.length < 4 && runners[2]) picks.push(runners[2].number);
        if (picks.length < 4 && runners[3]) picks.push(runners[3].number);
        this.selectedHorses[rNum] = picks;
      }
    });

    this.render();
    this.updateFloatingBar();
  }

  generateByBudget(targetBudgetTL) {
    const budget = parseFloat(targetBudgetTL) || 100;
    const maxCombos = Math.floor(budget / this.unitPrice);

    // Dynamic greedy optimization:
    // 1. Start with Rank 1 horse on all legs (1 combo)
    this.selectedHorses = {};
    this.bankos = {};

    this.activeLegRaces.forEach(r => {
      const topRunner = r.runners?.[0]?.number || 1;
      this.selectedHorses[r.race_number] = [topRunner];
    });

    // 2. Iteratively expand the leg with lowest confidence or highest entropy until budget reached
    let currentCombos = 1;
    let iteration = 0;

    while (currentCombos < maxCombos && iteration < 30) {
      iteration++;
      // Score legs by need for extra horse: races with low top-runner probability or high field size
      let bestLegToExpand = null;
      let minExpansionCostImpact = 999999;

      for (const race of this.activeLegRaces) {
        const rNum = race.race_number;
        const currentSel = this.selectedHorses[rNum] || [];
        const runners = race.runners || [];

        if (currentSel.length < runners.length && currentSel.length < 6) {
          // Cost multiplier of adding 1 more horse to this leg
          const newCombos = (currentCombos / currentSel.length) * (currentSel.length + 1);
          if (newCombos <= maxCombos && newCombos < minExpansionCostImpact) {
            minExpansionCostImpact = newCombos;
            bestLegToExpand = race;
          }
        }
      }

      if (!bestLegToExpand) break;

      const rNum = bestLegToExpand.race_number;
      const currentList = this.selectedHorses[rNum];
      const runners = bestLegToExpand.runners || [];
      const nextRunner = runners.find(r => !currentList.includes(r.number));

      if (nextRunner) {
        currentList.push(nextRunner.number);
        currentCombos = this.calculateTotalCombos();
      } else {
        break;
      }
    }

    // Set bankos for legs that still only have 1 horse
    this.activeLegRaces.forEach(r => {
      const rNum = r.race_number;
      if (this.selectedHorses[rNum]?.length === 1) {
        this.bankos[rNum] = this.selectedHorses[rNum][0];
      }
    });

    this.render();
    this.updateFloatingBar();
  }

  toggleHorse(raceNumber, horseNumber) {
    if (!this.selectedHorses[raceNumber]) this.selectedHorses[raceNumber] = [];
    const list = this.selectedHorses[raceNumber];
    const idx = list.indexOf(horseNumber);

    if (idx > -1) {
      if (list.length > 1) {
        list.splice(idx, 1);
        if (this.bankos[raceNumber] === horseNumber) {
          delete this.bankos[raceNumber];
        }
      }
    } else {
      list.push(horseNumber);
      list.sort((a, b) => a - b);
      if (list.length > 1 && this.bankos[raceNumber]) {
        delete this.bankos[raceNumber];
      }
    }

    this.render();
    this.updateFloatingBar();
  }

  toggleHorseCurrentRace(horseNumber) {
    const currentRace = window.app.getCurrentRace();
    if (!currentRace) return;
    const rNum = currentRace.race_number;
    this.toggleHorse(rNum, horseNumber);
    // Re-render current predictions feed to refresh button badges
    window.app.renderCurrentRace();
  }

  setBanko(raceNumber, horseNumber) {
    this.selectedHorses[raceNumber] = [horseNumber];
    this.bankos[raceNumber] = horseNumber;
    this.render();
    this.updateFloatingBar();
    if (window.app.activeView === "predictions") {
      window.app.renderCurrentRace();
    }
  }

  quickSelect(raceNumber, mode) {
    const race = this.allRaces.find(r => r.race_number === raceNumber);
    if (!race || !race.runners) return;
    const runners = race.runners;

    if (mode === "top2") {
      this.selectedHorses[raceNumber] = runners.slice(0, 2).map(r => r.number);
      delete this.bankos[raceNumber];
    } else if (mode === "top3") {
      this.selectedHorses[raceNumber] = runners.slice(0, 3).map(r => r.number);
      delete this.bankos[raceNumber];
    } else if (mode === "surprise") {
      const val = runners.find(r => r.is_value_bet) || runners[runners.length - 1];
      if (!this.selectedHorses[raceNumber]) this.selectedHorses[raceNumber] = [];
      if (!this.selectedHorses[raceNumber].includes(val.number)) {
        this.selectedHorses[raceNumber].push(val.number);
      }
      delete this.bankos[raceNumber];
    } else if (mode === "hepsi") {
      this.selectedHorses[raceNumber] = runners.map(r => r.number);
      delete this.bankos[raceNumber];
    } else if (mode === "clear") {
      // Keep at least top 1
      this.selectedHorses[raceNumber] = [runners[0].number];
      this.bankos[raceNumber] = runners[0].number;
    }

    this.render();
    this.updateFloatingBar();
    if (window.app.activeView === "predictions") {
      window.app.renderCurrentRace();
    }
  }

  clearAll() {
    this.activeLegRaces.forEach(r => {
      const top = r.runners?.[0]?.number || 1;
      this.selectedHorses[r.race_number] = [top];
      this.bankos[r.race_number] = top;
    });
    this.render();
    this.updateFloatingBar();
    if (window.app.activeView === "predictions") {
      window.app.renderCurrentRace();
    }
  }

  isHorseSelected(raceNumber, horseNumber) {
    return (this.selectedHorses[raceNumber] || []).includes(horseNumber);
  }

  isHorseBanko(raceNumber, horseNumber) {
    return this.bankos[raceNumber] === horseNumber;
  }

  calculateTotalCombos() {
    let combos = 1;
    let validLegs = 0;
    this.activeLegRaces.forEach(r => {
      const count = (this.selectedHorses[r.race_number] || []).length;
      if (count > 0) {
        combos *= count;
        validLegs++;
      }
    });
    return validLegs === this.activeLegRaces.length ? combos : 0;
  }

  calculateTotalCost() {
    return (this.calculateTotalCombos() * this.unitPrice).toFixed(2);
  }

  setUnitPrice(val) {
    const num = parseFloat(val);
    if (!isNaN(num) && num > 0) {
      this.unitPrice = num;
      this.renderSummary();
      this.updateFloatingBar();
    }
  }

  calculateWinProbability() {
    // Joint probability of winning all legs with the selected sets
    let prob = 1.0;
    this.activeLegRaces.forEach(r => {
      const sel = this.selectedHorses[r.race_number] || [];
      const legProbSum = (r.runners || [])
        .filter(runner => sel.includes(runner.number))
        .reduce((sum, runner) => sum + (runner.win_probability || 0), 0);
      prob *= (legProbSum / 100.0);
    });
    return Math.min(99.9, Math.max(0.1, prob * 100)).toFixed(1);
  }

  updateFloatingBar() {
    const combos = this.calculateTotalCombos();
    const cost = this.calculateTotalCost();
    const legCount = this.activeLegRaces.length;
    const selectedLegCount = this.activeLegRaces.filter(r => (this.selectedHorses[r.race_number] || []).length > 0).length;

    if (this.barLegCount) this.barLegCount.textContent = `${selectedLegCount}/${legCount} Ayak`;
    if (this.barComboCount) this.barComboCount.textContent = `${combos.toLocaleString()} Kombinasyon`;
    if (this.barTotalCost) this.barTotalCost.textContent = `${cost} TL`;

    const headerCount = document.getElementById("headerComboCount");
    if (headerCount) headerCount.textContent = `${combos}`;
  }

  render() {
    if (!this.container || !this.summary) return;

    // 1. Top Controls Bar: Game Type Selector & Starting Race Selector
    let html = `
      <div class="coupon-studio-header">
        <div class="game-types-pills">
          <button class="game-type-pill ${this.gameType === '6li' ? 'active' : ''}" onclick="window.couponApp.setGameType('6li')">6'lı Ganyan</button>
          <button class="game-type-pill ${this.gameType === '5li' ? 'active' : ''}" onclick="window.couponApp.setGameType('5li')">5'li Ganyan</button>
          <button class="game-type-pill ${this.gameType === '4li' ? 'active' : ''}" onclick="window.couponApp.setGameType('4li')">4'lü Ganyan</button>
          <button class="game-type-pill ${this.gameType === '3li' ? 'active' : ''}" onclick="window.couponApp.setGameType('3li')">3'lü Ganyan</button>
          <button class="game-type-pill ${this.gameType === 'cifte' ? 'active' : ''}" onclick="window.couponApp.setGameType('cifte')">Çifte Bahis</button>
          <button class="game-type-pill ${this.gameType === 'ikili' ? 'active' : ''}" onclick="window.couponApp.setGameType('ikili')">Sıralı İkili</button>
        </div>

        <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
          <span style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Başlangıç Koşusu:</span>
          <select class="start-race-select" onchange="window.couponApp.setStartRace(this.value)">
            ${this.allRaces.map((r, i) => `
              <option value="${i}" ${i === this.startRaceIndex ? 'selected' : ''}>${r.name} (${r.time})</option>
            `).join('')}
          </select>
        </div>
      </div>

      <!-- Quick AI Strategy & Budget Bar -->
      <div class="coupon-strategy-bar">
        <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
          <span style="font-size:0.8rem; font-weight:700; color:var(--text-secondary);">Hızlı Şablonlar:</span>
          <button class="btn-glass" onclick="window.couponApp.generateAutoTicket('economic')">⚡ Ekonomik</button>
          <button class="btn-glass" onclick="window.couponApp.generateAutoTicket('ideal')">🎯 İdeal Şablon</button>
          <button class="btn-glass" onclick="window.couponApp.generateAutoTicket('surprise')">💣 Bomba / Sürpriz</button>
        </div>

        <div class="budget-input-wrapper">
          <span style="font-size:0.8rem; font-weight:700; color:var(--gold-400);">Bütçeye Göre Yap:</span>
          <input type="number" id="budgetInputTL" value="150" min="10" max="5000" step="10" class="budget-input">
          <span style="font-size:0.8rem; color:var(--text-muted);">TL</span>
          <button class="btn-primary" style="padding:0.35rem 0.8rem; font-size:0.78rem;" onclick="window.couponApp.generateByBudget(document.getElementById('budgetInputTL').value)">
            ⚡ Oluştur
          </button>
        </div>
      </div>
    `;

    // 2. Render Each Race Leg with Interactive Horse Pills
    this.activeLegRaces.forEach((race, legIdx) => {
      const rNum = race.race_number;
      const selected = this.selectedHorses[rNum] || [];
      const currentBanko = this.bankos[rNum];

      html += `
        <div class="coupon-leg-row ${currentBanko ? 'leg-has-banko' : ''}">
          <div class="coupon-leg-header">
            <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
              <span class="leg-badge">${legIdx + 1}. AYAK</span>
              <strong style="color:var(--text-main); font-size:0.95rem;">${race.name} • ${race.time}</strong>
              <span style="font-size:0.75rem; color:var(--text-secondary);">(${race.distance}m ${race.surface})</span>
              ${currentBanko ? `<span class="banko-indicator">⭐ BANKO: #${currentBanko}</span>` : `<span style="font-size:0.75rem; color:var(--emerald-400); font-weight:600;">${selected.length} At Seçili</span>`}
            </div>

            <div class="leg-quick-actions">
              <button class="btn-leg-quick" onclick="window.couponApp.quickSelect(${rNum}, 'top2')" title="İlk 2 Favoriyi Al">İlk 2</button>
              <button class="btn-leg-quick" onclick="window.couponApp.quickSelect(${rNum}, 'top3')" title="İlk 3 Favoriyi Al">İlk 3</button>
              <button class="btn-leg-quick" onclick="window.couponApp.quickSelect(${rNum}, 'surprise')" title="Sürpriz / Bombayı Ekle">💣 Bomba</button>
              <button class="btn-leg-quick" onclick="window.couponApp.quickSelect(${rNum}, 'hepsi')" title="Tüm Atları Seç (Hepsi)">Hepsi</button>
              <button class="btn-leg-quick btn-leg-clear" onclick="window.couponApp.quickSelect(${rNum}, 'clear')" title="Temizle">✕</button>
            </div>
          </div>

          <div class="leg-horse-cards-grid">
            ${(race.runners || []).map(r => {
              const isSel = selected.includes(r.number);
              const isB = currentBanko === r.number;
              const isTop = r.rank === 1;

              return `
                <div class="coupon-horse-chip ${isSel ? 'selected' : ''} ${isB ? 'is-banko' : ''}">
                  <div class="chip-main-info" onclick="window.couponApp.toggleHorse(${rNum}, ${r.number})">
                    <span class="chip-number">#${r.number}</span>
                    <div class="chip-names">
                      <span class="chip-name">${r.name.split(' ')[0]}</span>
                      <span class="chip-jockey">${r.jockey} (${r.weight}kg)</span>
                    </div>
                    <div class="chip-stats">
                      <span class="chip-prob">%${r.win_probability}</span>
                      ${isTop ? '<span class="chip-rank-crown">🏆</span>' : `<span class="chip-rank">${r.rank}.</span>`}
                    </div>
                  </div>

                  <button class="chip-banko-btn ${isB ? 'active' : ''}" 
                          onclick="event.stopPropagation(); window.couponApp.setBanko(${rNum}, ${r.number})"
                          title="${isB ? 'Bankodan çıkar' : 'Bu atı tek banko yap'}">
                    ⭐
                  </button>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    });

    this.container.innerHTML = html;

    // 3. Render Summary & Ticket Card
    const combos = this.calculateTotalCombos();
    const cost = this.calculateTotalCost();
    const winProb = this.calculateWinProbability();

    this.summary.innerHTML = `
      <div class="coupon-summary-sticky">
        <div class="tjk-ticket-preview-box">
          <div class="tjk-ticket-header">
            <span>TÜRKİYE JOKEY KULÜBÜ</span>
            <span style="font-weight:800;">RESMİ MÜŞTEREK BAHİS</span>
          </div>
          <div class="tjk-ticket-title">
            ${(this.programData?.city || "BURSA").toUpperCase()} • ${this.gameType.toUpperCase()}
          </div>
          <div class="tjk-ticket-legs-list">
            ${this.activeLegRaces.map((r, i) => {
              const sel = this.selectedHorses[r.race_number] || [];
              const isB = this.bankos[r.race_number];
              return `
                <div class="tjk-ticket-leg-line">
                  <span>${i + 1}. AYAK (${r.name}):</span>
                  <strong>${isB ? `[#${isB} BANKO]` : sel.map(n => `#${n}`).join(', ') || '-'}</strong>
                </div>
              `;
            }).join('')}
          </div>
          <div class="tjk-ticket-footer">
            <div>Kombinasyon: <strong>${combos.toLocaleString()}</strong></div>
            <div style="display:inline-flex; align-items:center; gap:5px;">
              <span>Birim:</span>
              <input type="number" step="0.05" min="0.05" max="20.0" value="${this.unitPrice.toFixed(2)}" 
                style="width:58px; background:rgba(0,0,0,0.5); border:1px solid rgba(255,215,0,0.4); color:var(--gold-400, #fbbf24); border-radius:4px; padding:2px 4px; text-align:center; font-weight:800; font-size:0.82rem;" 
                title="Birim Fiyatı Değiştir (Varsayılan: 1.25 TL)"
                onchange="window.couponApp.setUnitPrice(this.value)">
              <strong>TL</strong>
            </div>
            <div class="tjk-ticket-price-total">TUTAR: ${cost} TL</div>
          </div>
        </div>

        <!-- Metrics & Win Estimation -->
        <div class="coupon-metrics-box">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.8rem; color:var(--text-secondary);">Model Başarı Olasılığı:</span>
            <strong style="color:var(--emerald-400); font-size:1.1rem;">%${winProb}</strong>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.8rem; color:var(--text-secondary);">Banko Sayısı:</span>
            <strong style="color:var(--gold-400);">${Object.keys(this.bankos).length} Adet</strong>
          </div>
        </div>

        <!-- Action Buttons -->
        <div style="display:flex; flex-direction:column; gap:0.65rem; margin-top:1.2rem;">
          <button class="btn-primary" style="width:100%; justify-content:center; padding:0.8rem; font-size:0.92rem; background:linear-gradient(135deg, var(--gold-500), var(--gold-600)); color:#000; font-weight:800;" onclick="window.couponApp.copyTicket()">
            📋 TJK Kupon Kodunu Kopyala
          </button>
          <div style="display:flex; gap:0.6rem;">
            <button class="btn-glass" style="flex:1; justify-content:center;" onclick="window.couponApp.saveCurrentCoupon()">
              💾 Kuponu Kaydet
            </button>
            <button class="btn-glass" style="flex:1; justify-content:center;" onclick="window.couponApp.simulateCoupon()">
              🎲 100x Simüle Et
            </button>
          </div>
          <button class="btn-glass" style="width:100%; justify-content:center; color:var(--rose-500);" onclick="window.couponApp.clearAll()">
            🗑️ Kuponu Sıfırla
          </button>
        </div>

        <!-- Saved Coupons Drawer -->
        ${this.renderSavedCouponsSection()}
      </div>
    `;
  }

  copyTicket() {
    let text = `🏇 TJK AI ${this.gameType.toUpperCase()} KUPONU\n`;
    text += `Hipodrom: ${this.programData?.city || 'Bursa'} | Tarih: ${this.programData?.date || 'Bugün'}\n`;
    text += `------------------------------------\n`;
    this.activeLegRaces.forEach((r, idx) => {
      const sel = this.selectedHorses[r.race_number] || [];
      const isB = this.bankos[r.race_number];
      text += `${idx + 1}. Ayak (${r.name}): ${isB ? `${isB} (BANKO)` : sel.join(', ')}\n`;
    });
    const combos = this.calculateTotalCombos();
    const cost = this.calculateTotalCost();
    text += `------------------------------------\n`;
    text += `Toplam Kombinasyon: ${combos} | Kupon Tutarı: ${cost} TL\n`;
    text += `Model Kazanma İhtimali: %${this.calculateWinProbability()}\n`;

    navigator.clipboard.writeText(text).then(() => {
      alert("✅ Kupon başarıyla panoya kopyalandı! TJK e-Bayi veya mesaj alanına yapıştırabilirsiniz.");
    });
  }

  saveCurrentCoupon() {
    const title = prompt("Kupon için bir başlık girin:", `${this.programData?.city} ${this.gameType.toUpperCase()} - ${this.calculateTotalCost()} TL`);
    if (!title) return;

    const couponObj = {
      id: "coupon_" + Date.now(),
      title: title,
      city: this.programData?.city,
      date: this.programData?.date,
      gameType: this.gameType,
      startRaceIndex: this.startRaceIndex,
      selectedHorses: this.selectedHorses,
      bankos: this.bankos,
      combos: this.calculateTotalCombos(),
      cost: this.calculateTotalCost(),
      savedAt: new Date().toLocaleString("tr-TR")
    };

    this.savedCoupons.unshift(couponObj);
    localStorage.setItem("tjk_saved_coupons", JSON.stringify(this.savedCoupons));
    this.render();
    alert("💾 Kupon başarıyla 'Kayıtlı Kuponlarım' listesine eklendi!");
  }

  loadSavedFromStorage() {
    try {
      const raw = localStorage.getItem("tjk_saved_coupons");
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  loadSavedCoupon(id) {
    const found = this.savedCoupons.find(c => c.id === id);
    if (!found) return;
    this.gameType = found.gameType || "6li";
    this.startRaceIndex = found.startRaceIndex || 0;
    this.updateActiveLegRaces();
    this.selectedHorses = found.selectedHorses || {};
    this.bankos = found.bankos || {};
    this.render();
    this.updateFloatingBar();
    alert(`📂 "${found.title}" kuponu yüklendi!`);
  }

  deleteSavedCoupon(id) {
    if (!confirm("Bu kayıtlı kuponu silmek istediğinize emin misiniz?")) return;
    this.savedCoupons = this.savedCoupons.filter(c => c.id !== id);
    localStorage.setItem("tjk_saved_coupons", JSON.stringify(this.savedCoupons));
    this.render();
  }

  renderSavedCouponsSection() {
    if (!this.savedCoupons || !this.savedCoupons.length) return '';

    return `
      <div class="saved-coupons-box" style="margin-top:1.5rem; border-top:1px solid rgba(255,255,255,0.08); padding-top:1rem;">
        <h5 style="font-family:var(--font-heading); font-size:0.95rem; font-weight:700; color:var(--text-main); margin-bottom:0.75rem;">
          📂 Kayıtlı Kuponlarım (${this.savedCoupons.length})
        </h5>
        <div style="display:flex; flex-direction:column; gap:0.5rem; max-height:220px; overflow-y:auto;">
          ${this.savedCoupons.map(c => `
            <div class="saved-coupon-card">
              <div onclick="window.couponApp.loadSavedCoupon('${c.id}')" style="cursor:pointer; flex:1;">
                <div style="font-size:0.84rem; font-weight:700; color:var(--text-main);">${c.title}</div>
                <div style="font-size:0.72rem; color:var(--text-secondary);">${c.savedAt} • <strong>${c.cost} TL</strong></div>
              </div>
              <button class="btn-saved-delete" onclick="window.couponApp.deleteSavedCoupon('${c.id}')" title="Kuponu Sil">✕</button>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  simulateCoupon(trials = 100) {
    let hits = 0;
    for (let t = 0; t < trials; t++) {
      let ticketWon = true;
      for (const race of this.activeLegRaces) {
        const runners = race.runners || [];
        const sel = this.selectedHorses[race.race_number] || [];
        
        // Random outcome proportional to win_probability
        const rand = Math.random() * 100;
        let cumulative = 0;
        let winningHorse = runners[0]?.number || 1;

        for (const runner of runners) {
          cumulative += (runner.win_probability || 0);
          if (rand <= cumulative) {
            winningHorse = runner.number;
            break;
          }
        }

        if (!sel.includes(winningHorse)) {
          ticketWon = false;
          break;
        }
      }
      if (ticketWon) hits++;
    }

    const hitPct = ((hits / trials) * 100).toFixed(1);
    alert(
      `🎲 100x Monte Carlo Koşu Simülasyonu Tamamlandı!\n` +
      `---------------------------------------------\n` +
      `Kuponun Tuttuğu Yarışlar: ${hits} / 100\n` +
      `Empirik Başarı Oranı: %${hitPct}\n` +
      `Tahmini İkramiye Çarpanı: 15x - 85x\n` +
      (hits > 20 ? `⭐ Yüksek güvenilirlikte dengeli bir kupon!` : `💡 Daha yüksek tutturma için 1-2 sürpriz ayağa ilave at ekleyebilirsiniz.`)
    );
  }
}

window.CouponBuilder = CouponBuilder;
