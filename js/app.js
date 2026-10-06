/**
 * TJK AI Prediction & Analytics Platform - Master Application Controller
 */

class TJKApp {
  constructor() {
    this.cities = [];
    this.currentCity = "Bursa";
    this.currentProgram = null;
    this.activeRaceIndex = 0;
    this.activeView = "predictions"; // predictions, matrix, gallops, simulator, coupon

    this.initElements();
    this.bindEvents();
    this.initSubModules();
    this.loadCities();
  }

  initElements() {
    this.trackContainer = document.getElementById("trackContainer");
    this.raceRibbon = document.getElementById("raceRibbon");
    this.raceBanner = document.getElementById("raceBanner");
    this.viewsContainer = document.getElementById("viewsContainer");
    this.dateDisplay = document.getElementById("currentDateDisplay");
    this.statusText = document.getElementById("connectionStatusText");

    // Modals
    this.gallopModal = document.getElementById("gallopModal");
    this.gallopModalBody = document.getElementById("gallopModalBody");
    this.h2hModal = document.getElementById("h2hModal");
    this.h2hModalBody = document.getElementById("h2hModalBody");
    this.pwaModal = document.getElementById("pwaModal");

    // Format current date display
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    this.currentDateStr = `${day}.${month}.${year}`;
    if (this.dateDisplay) {
      this.dateDisplay.textContent = this.currentDateStr;
    }

    this.notifiedRaces = {};
    this.initTjkTv();
    this.initCountdownTimer();
  }

  initCountdownTimer() {
    setInterval(() => {
      const race = this.getCurrentRace();
      if (!race) return;
      
      const now = new Date();
      const [rHour, rMin] = (race.time || "14:00").split(':').map(Number);
      
      const raceTime = new Date();
      raceTime.setHours(rHour, rMin, 0, 0);
      
      const diffMs = raceTime - now;
      const cBox = document.getElementById("raceCountdownBox");
      const cText = document.getElementById("countdownText");
      if(!cBox || !cText) return;
      
      const raceKey = `${this.currentCity}_${race.number || this.activeRaceIndex}`;

      if (diffMs > 0 && diffMs <= 180000) { // 3 minutes or less before race
        const mins = Math.floor(diffMs / 60000);
        const secs = Math.floor((diffMs % 60000) / 1000);
        cText.textContent = `${race.time} Koşusuna ${mins}:${secs.toString().padStart(2, '0')}`;
        cBox.classList.add("alert-glow");
        cBox.style.color = "var(--rose-500)";
        
        // Auto alert & open TJK TV PiP if not yet notified for this race
        if (!this.notifiedRaces[raceKey]) {
          this.notifiedRaces[raceKey] = true;
          this.showRaceAlert(race, mins + 1);
          this.toggleTjkTv(true);
        }
      } else if (diffMs <= 0 && diffMs > -300000) { // Up to 5 mins after start
        cText.textContent = `${race.time} Koşusu Başladı!`;
        cBox.classList.add("alert-glow");
        cBox.style.color = "var(--emerald-400)";
        if (!this.notifiedRaces[raceKey]) {
          this.notifiedRaces[raceKey] = true;
          this.showRaceAlert(race, 0);
          this.toggleTjkTv(true);
        }
      } else {
        cText.textContent = `${race.time} Koşusu Bekleniyor`;
        cBox.classList.remove("alert-glow");
        cBox.style.color = "";
      }
    }, 1000);
  }

  initSubModules() {
    this.simulator = new window.RaceSimulator("raceCanvas", "simTicker");
    this.couponBuilder = new window.CouponBuilder("couponRacesContainer", "couponSummaryContainer");
    this.h2hComparator = new window.H2HComparator("h2hModal", "h2hModalBody");
    window.couponApp = this.couponBuilder;
    window.h2hApp = this.h2hComparator;
  }

  bindEvents() {
    // View tab switching
    document.querySelectorAll(".view-tab").forEach(tab => {
      tab.addEventListener("click", (e) => {
        const view = e.currentTarget.getAttribute("data-view");
        this.switchView(view);
      });
    });

    // TJK TV PiP Button in Header
    document.getElementById("btnToggleTjkTv")?.addEventListener("click", () => this.toggleTjkTv());

    // PWA Install guide modal
    const btnPwa = document.getElementById("btnPwaInstall");
    if (btnPwa) {
      btnPwa.addEventListener("click", () => this.openPwaModal());
    }

    // Refresh button
    const btnRefresh = document.getElementById("btnRefresh");
    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => this.refreshData());
    }

    // Simulator controls
    document.getElementById("btnSimPlay")?.addEventListener("click", () => this.simulator.start());
    document.getElementById("btnSimPause")?.addEventListener("click", () => this.simulator.pause());
    document.getElementById("btnSimReset")?.addEventListener("click", () => this.simulator.stop());
    document.getElementById("simSpeedSelect")?.addEventListener("change", (e) => {
      this.simulator.setSpeed(parseFloat(e.target.value));
    });
  }

  async loadCities() {
    if (this.statusText) this.statusText.textContent = "TJK Şehirleri Yükleniyor...";
    
    // 1. Try backend server if available
    try {
      const res = await fetch(`/api/cities?date=${this.currentDateStr}`);
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.cities && json.cities.length) {
          this.cities = json.cities;
          this.renderCities();
          const defaultCity = this.cities.find(c => !c.is_foreign) || this.cities[0];
          this.selectCity(defaultCity.name);
          return;
        }
      }
    } catch (err) {
      // Backend not running
    }

    // 2. Try pre-scraped live TJK data from GitHub Pages / static directory
    const cityPaths = [
      'data/today_cities.json',
      './data/today_cities.json',
      'frontend/data/today_cities.json',
      './frontend/data/today_cities.json'
    ];

    for (const path of cityPaths) {
      try {
        const res = await fetch(path);
        if (res.ok) {
          const list = await res.json();
          if (Array.isArray(list) && list.length > 0) {
            this.cities = list;
            this.renderCities();
            const defaultCity = this.cities.find(c => !c.is_foreign) || this.cities[0];
            this.selectCity(defaultCity.name);
            return;
          }
        }
      } catch (e) {
        // try next path
      }
    }

    // 3. Fallback default list
    this.cities = [
      { id: "4", name: "Bursa", display_name: "Bursa (Gündüz)", is_foreign: false },
      { id: "6", name: "Şanlıurfa", display_name: "Şanlıurfa (Gece)", is_foreign: false },
      { id: "3", name: "İstanbul", display_name: "İstanbul (Veliefendi)", is_foreign: false },
      { id: "1", name: "Adana", display_name: "Adana (Yeşiloba)", is_foreign: false },
      { id: "2", name: "İzmir", display_name: "İzmir (Şirinyer)", is_foreign: false },
      { id: "541", name: "Le Mans Fransa", display_name: "Le Mans Fransa (YD)", is_foreign: true },
      { id: "59", name: "Philadelphia ABD", display_name: "Philadelphia ABD (YD)", is_foreign: true }
    ];
    this.renderCities();
    this.selectCity("Bursa");
  }

  renderCities() {
    if (!this.trackContainer) return;
    this.trackContainer.innerHTML = this.cities.map(c => `
      <button class="track-tab ${c.name === this.currentCity ? 'active' : ''}" onclick="window.app.selectCity('${c.name}')">
        <span class="city-dot"></span>
        <span>${c.display_name || c.name}</span>
        ${c.is_foreign ? '<span class="foreign-tag">Yabancı</span>' : ''}
      </button>
    `).join('');

    setTimeout(() => {
      const activeTab = this.trackContainer?.querySelector(".track-tab.active");
      if (activeTab) {
        activeTab.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
    }, 60);
  }

  async selectCity(cityName) {
    this.currentCity = cityName;
    this.renderCities();
    if (this.statusText) this.statusText.textContent = `${cityName} Canlı Bülteni Çekiliyor...`;

    // 1. Try local/cloud backend server
    try {
      const res = await fetch(`/api/program?city=${encodeURIComponent(cityName)}&date=${this.currentDateStr}&t=${Date.now()}`);
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.data) {
          this.applyProgram(json.data, `🟢 Canlı TJK API: ${cityName}`);
          return;
        }
      }
    } catch (err) {
      // Backend not running
    }

    // 2. Try pre-scraped live TJK data for this city
    const programPaths = [
      `data/program_${cityName}.json`,
      `./data/program_${cityName}.json`,
      `data/program_${encodeURIComponent(cityName)}.json`,
      `./data/program_${encodeURIComponent(cityName)}.json`,
      `data/all_programs.json`,
      `./data/all_programs.json`,
      `frontend/data/program_${cityName}.json`,
      `./frontend/data/program_${cityName}.json`
    ];

    for (const path of programPaths) {
      try {
        const res = await fetch(path);
        if (res.ok) {
          const json = await res.json();
          let prog = null;
          if (path.includes('all_programs')) {
            prog = json[cityName] || json[Object.keys(json)[0]];
          } else if (json.races) {
            prog = json;
          }
          if (prog && prog.races && prog.races.length > 0) {
            this.applyProgram(prog, `🟢 Canlı TJK Bülteni: ${cityName}`);
            return;
          }
        }
      } catch (e) {
        // try next
      }
    }

    // 3. Fallback client synthesis
    const fallback = this.generateClientFallbackProgram(cityName, this.currentDateStr);
    this.applyProgram(fallback, `🟡 Simüle Veri: ${cityName}`);
  }

  applyProgram(program, statusText) {
    this.currentProgram = program;
    this.activeRaceIndex = 0;
    if (this.statusText) {
      this.statusText.textContent = `${statusText} (${program.races.length} Koşu)`;
    }
    this.renderRaceRibbon();
    this.renderCurrentRace();
    this.couponBuilder.loadProgram(this.currentProgram);
  }

  async refreshData() {
    if (this.statusText) this.statusText.textContent = "🔄 Veriler güncelleniyor...";
    await this.loadCities();
  }

  generateClientFallbackProgram(cityName, dateStr) {
    const distances = [1400, 1500, 1200, 1900, 1400, 1600, 2000, 1400];
    const surfaces = ["Çim", "Çim", "Kum", "Kum", "Sentetik", "Çim", "Kum", "Çim"];
    const types = ["Maiden/DHÖW", "ŞARTLI 3", "HANDİKAP 16", "KV-7", "ŞARTLI 4", "KISA VADE 8", "HANDİKAP 15", "MAIDEN"];
    const recordTimes = ["1:29.33", "1:27.03", "1:12.40", "2:02.15", "1:23.50", "1:35.20", "2:08.40", "1:30.10"];

    const sampleRunners = [
      { name: "ÇİLDUTAY KG DB SK", jockey: "MAH.TURAN", sire: "UÇANBEY", dam: "KUSURSUZAŞK", weight: 60, h: 36, last6: "Ç2S3Ç2S7", best: "1:34.91" },
      { name: "GÜLNARLI KG", jockey: "MER.ÇELİK", sire: "SİLAH", dam: "NAZLI DELAL", weight: 58, h: 42, last6: "Ç1Ç2Ç2", best: "1:32.40" },
      { name: "İZOTOP KG K", jockey: "M.KAYA", sire: "BALALAYKA", dam: "İZDEN", weight: 57, h: 39, last6: "Ç2Ç3Ç4", best: "1:34.48" },
      { name: "AŞAN SİMAY KG DB", jockey: "M.M.BİLGİN", sire: "GÜMBÜRGÜMBÜR", dam: "BAYKANCA", weight: 55, h: 34, last6: "K4K4K6", best: "1:36.10" },
      { name: "ATAK KIZ KG K DB", jockey: "E.KADİRLER", sire: "ORHUNKAAN", dam: "ŞEF SULTAN", weight: 54, h: 38, last6: "Ç3Ç1Ç5", best: "1:33.20" },
      { name: "BALKIZIM KG K DB", jockey: "N.AVCİ", sire: "GÜMBÜRGÜMBÜR", dam: "NESMİYANA", weight: 57, h: 44, last6: "S2Ç1Ç2", best: "1:31.95" },
      { name: "BATMAN KIZI KG", jockey: "A.MEH.ALTIN", sire: "BATMANASLANI", dam: "DEVİRAL", weight: 56, h: 31, last6: "Ç4Ç6Ç7", best: "1:37.05" },
      { name: "GÜZEL ELAM KG K", jockey: "U.TEMUR", sire: "SERHANTAY", dam: "ATİKKOBRAM", weight: 57, h: 40, last6: "Ç4Ç2Ç2", best: "1:34.83" },
      { name: "ÖZGÜNDEN KG SK", jockey: "M.KEÇECİ", sire: "GELİBOLU", dam: "GÖCEK GÜLÜ", weight: 57, h: 33, last6: "Ç3K3Ç8", best: "1:35.09" }
    ];

    const races = [];
    for (let rIdx = 0; rIdx < 8; rIdx++) {
      const rNum = rIdx + 1;
      const dist = distances[rIdx];
      const surf = surfaces[rIdx];
      const rec = recordTimes[rIdx];

      const runners = sampleRunners.map((base, idx) => {
        const num = idx + 1;
        const speedFig = Math.max(50, Math.min(96, Math.round(92 - (idx * 4.2) + ((rIdx * 7 + idx * 11) % 9))));
        const winProb = idx === 0 ? 26.5 : (idx === 1 ? 21.0 : (idx === 2 ? 15.5 : (idx === 3 ? 11.0 : Math.max(3.0, (100 - 74) / 5))));
        const mean400 = (24.8 + idx * 0.35).toFixed(2);
        const hasOutlier = (idx % 3 === 0);

        return {
          number: num,
          name: `${base.name}`,
          age: "3y k d",
          sire: base.sire,
          dam: base.dam,
          weight: base.weight,
          jockey: base.jockey,
          gate: num,
          agf: Math.max(2, Math.round(35 / (idx + 1))),
          handicap: base.h,
          last_6: base.last6,
          kgs: 12 + (idx * 4),
          s20: 14 + (idx % 5),
          best_time: base.best,
          rank: idx + 1,
          win_probability: winProb,
          is_value_bet: idx === 2 && winProb >= 15.0,
          value_tag: idx === 0 ? "Öncelikli Favori" : (idx === 1 ? "Ciddi Rakip" : (idx === 2 ? "Bomba / Değer Bahsi" : "Tabela")),
          time_analysis: {
            adjusted_time_sec: 94.5 + idx * 0.45,
            adjusted_time_str: `1:${(34.5 + idx * 0.45).toFixed(2)}`,
            pace_100m: (6.75 + idx * 0.03).toFixed(2),
            speed_figure: speedFig,
            is_exact_match: idx < 3,
            source_desc: "Hedef mesafe ve pist derecesinden uyarlandı",
            weight_penalty_sec: 0.22
          },
          surface_affinity: {
            score: 85 - idx * 4,
            runs_count: 4,
            podium_count: Math.max(1, 4 - idx),
            details: `${surf} pistte yüksek uyum sergiliyor.`
          },
          gallop_analysis: {
            mean_400_pace: mean400,
            gallop_score: Math.round(95 - idx * 3.5),
            is_consistent: !hasOutlier,
            outlier_count: hasOutlier ? 1 : 0,
            status_badge: hasOutlier ? "Dalgalanma Ayıklandı" : "İstikrarlı Galop",
            summary: `Son sprint temposu 400m ${mean400}sn.`
          },
          jockey_score: 88 - idx * 2,
          form_score: 82 - idx * 3,
          composite_rating: 85 - idx * 3.8,
          rationale: `Grup genelinde ${dist}m ${surf} şartlarında ${speedFig} hız endeksi ve istikrarlı idman temposuyla ${idx + 1}. sıraya yerleşti. ${hasOutlier ? '1 adet aşırı dalgalı kenter idmanı ortalamadan ayıklandı.' : 'Tüm galopları tutarlı ve dengeli.'}`
        };
      });

      races.push({
        race_number: rNum,
        name: `${rNum}. Koşu`,
        time: `${14 + Math.floor(rIdx / 2)}:${rIdx % 2 === 1 ? '30' : '00'}`,
        race_type: types[rIdx],
        age_group: "3 Yaşlı Araplar / İngilizler",
        base_weight: "57.00kg",
        distance: dist,
        surface: surf,
        record_time: rec,
        city: cityName,
        date: dateStr,
        runners: runners,
        winner_prediction: runners[0],
        pace_overview: {
          tempo: rIdx % 2 === 0 ? "Dengeli / Standart Tempo" : "Kırıcı / Çok Hızlı Tempo",
          tempo_description: "Ön grupta liderlik mücadelesi dengeli seyredecek; virajı iyi dönen atlar avantajlı.",
          front_runners: [runners[0].name.split(' ')[0]],
          closers: [runners[1].name.split(' ')[0], runners[2].name.split(' ')[0]]
        }
      });
    }

    return {
      city: cityName,
      date: dateStr,
      total_races: races.length,
      races: races,
      fetched_at: new Date().toISOString()
    };
  }

  renderRaceRibbon() {
    if (!this.raceRibbon || !this.currentProgram) return;
    const races = this.currentProgram.races || [];

    this.raceRibbon.innerHTML = races.map((r, idx) => {
      const isFin = r.is_finished;
      const bankoHit = r.accuracy_report && r.accuracy_report.banko_hit;
      return `
        <div class="race-pill ${idx === this.activeRaceIndex ? 'active' : ''}" onclick="window.app.selectRace(${idx})">
          <div class="race-pill-header">
            <span class="race-pill-title">${r.name}</span>
            <span class="race-pill-time">${r.time}</span>
            ${isFin ? '<span class="pill-finished-badge">🏁 Bitti</span>' : ''}
            ${bankoHit ? '<span class="pill-banko-hit" title="1. Banko Tahmin Kazandı!">🥇 Banko</span>' : ''}
          </div>
          <div class="race-pill-meta">
            <span>${r.distance}m</span>
            <span>•</span>
            <span>${r.surface}</span>
            <span>•</span>
            <span>${(r.runners || []).length} At</span>
          </div>
        </div>
      `;
    }).join('');

    setTimeout(() => {
      const activePill = this.raceRibbon?.querySelector(".race-pill.active");
      if (activePill) {
        activePill.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
    }, 60);
  }

  selectRace(idx) {
    this.activeRaceIndex = idx;
    this.renderRaceRibbon();
    this.renderCurrentRace();
  }

  getCurrentRace() {
    if (!this.currentProgram || !this.currentProgram.races) return null;
    return this.currentProgram.races[this.activeRaceIndex] || null;
  }

  renderCurrentRace() {
    const race = this.getCurrentRace();
    if (!race) return;

    this.renderRaceBanner(race);
    this.renderActiveView(race);
  }

  renderRaceBanner(race) {
    if (!this.raceBanner) return;
    const pace = race.pace_overview || {};
    const winner = race.winner_prediction || {};
    const surfClass = `surface-${(race.surface || 'cim').toLowerCase().replace('ç', 'c')}`;

    this.raceBanner.innerHTML = `
      <div class="banner-grid">
        <div class="banner-info-section">
          <div style="font-size:0.8rem; font-weight:700; color:var(--emerald-400); text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.2rem;">
            ${this.currentCity} Hipodromu • ${race.time}
          </div>
          <h1>${race.name} - ${race.race_type || 'Şartlı Koşu'}</h1>
          <p style="font-size:0.88rem; color:var(--text-secondary);">${race.age_group || 'Genel Katılım'} | Sıklet Bazı: ${race.base_weight || '57kg'}</p>

          <div class="banner-meta-chips">
            <div class="meta-chip ${surfClass}">
              <strong>Pist:</strong> ${race.distance}m ${race.surface}
            </div>
            <div class="meta-chip">
              <strong>Pist Rekoru:</strong> ${race.record_time || '1.29.33'}
            </div>
            <div class="meta-chip" style="border-color:var(--border-gold); background:rgba(245,158,11,0.08); color:var(--gold-400);">
              ⭐ <strong>Favori Adayı:</strong> #${winner.number} ${winner.name} (%${winner.win_probability || 0})
            </div>
          </div>
        </div>

        <div class="pace-box">
          <div class="pace-box-header">
            <span class="pace-title">Taktik Tempo Analizi</span>
            <span class="pace-badge">${pace.tempo || 'Dengeli'}</span>
          </div>
          <div class="pace-desc">${pace.tempo_description || 'Yarış dengeli bir tempoda cereyan edecek.'}</div>
          <div class="pace-runners-row">
            ${pace.front_runners && pace.front_runners.length ? `<div class="pace-tag">Öncüler: <span>${pace.front_runners.join(', ')}</span></div>` : ''}
            ${pace.closers && pace.closers.length ? `<div class="pace-tag">Sprinterler: <span>${pace.closers.join(', ')}</span></div>` : ''}
          </div>
        </div>
      </div>
    `;
  }

  switchView(viewName) {
    const changed = this.activeView !== viewName;
    this.activeView = viewName;
    document.querySelectorAll(".view-tab").forEach(tab => {
      tab.classList.toggle("active", tab.getAttribute("data-view") === viewName);
    });
    this.moveTabIndicator();
    const race = this.getCurrentRace();
    const container = this.viewsContainer;
    if (!race) return;
    if (!changed || !container || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      this.renderActiveView(race);
      this.playViewEnter();
      return;
    }
    clearTimeout(this._viewTimer);
    container.classList.remove("view-enter");
    container.classList.add("view-exit");
    this._viewTimer = setTimeout(() => {
      this.renderActiveView(race);
      container.classList.remove("view-exit");
      this.playViewEnter();
    }, 220);
  }

  playViewEnter() {
    const container = this.viewsContainer;
    if (!container) return;
    container.classList.remove("view-enter");
    void container.offsetWidth; // restart animation
    container.classList.add("view-enter");
    // Stagger direct children for a cascading reveal
    Array.from(container.querySelectorAll(":scope > *, :scope > * > .card, :scope .runner-card")).slice(0, 24)
      .forEach((el, i) => el.style.setProperty("--stagger", `${i * 45}ms`));
  }

  moveTabIndicator() {
    const nav = document.querySelector(".view-tabs");
    const active = nav && nav.querySelector(".view-tab.active");
    if (!nav || !active) return;
    let ind = nav.querySelector(".tab-indicator");
    if (!ind) {
      ind = document.createElement("span");
      ind.className = "tab-indicator";
      nav.appendChild(ind);
      window.addEventListener("resize", () => this.moveTabIndicator());
    }
    ind.style.width = `${active.offsetWidth}px`;
    ind.style.height = `${active.offsetHeight}px`;
    ind.style.transform = `translate(${active.offsetLeft}px, ${active.offsetTop}px)`;
    if (nav.scrollWidth > nav.clientWidth) {
      nav.scrollTo({ left: active.offsetLeft - (nav.clientWidth - active.offsetWidth) / 2, behavior: "smooth" });
    }
  }

  renderActiveView(race) {
    const container = this.viewsContainer;
    if (!container) return;

    if (this.activeView === "predictions") {
      this.renderPredictionsView(race, container);
    } else if (this.activeView === "allbets") {
      this.renderAllBetsView(race, container);
    } else if (this.activeView === "matrix") {
      this.renderMatrixView(race, container);
    } else if (this.activeView === "gallops") {
      this.renderGallopsView(race, container);
    } else if (this.activeView === "simulator") {
      this.renderSimulatorView(race, container);
    } else if (this.activeView === "coupon") {
      this.renderCouponView(container);
    } else if (this.activeView === "results") {
      this.renderResultsView(race, container);
    }
  }

  /* ----------------------------------------------------------------------
     VIEW 1: RANKED PREDICTIONS FEED (Detailed Rationale & Metrics)
     ---------------------------------------------------------------------- */
  renderPredictionsView(race, container) {
    const runners = race.runners || [];

    let html = `<div class="predictions-feed">`;

    runners.forEach((r) => {
      const ta = r.time_analysis || {};
      const ga = r.gallop_analysis || {};
      const sa = r.surface_affinity || {};
      const pa = r.pedigree_analysis || {};
      const ca = r.condition_analysis || {};
      const syn = r.synergy_analysis || {};
      const mat = r.maturity_analysis || {};
      const rankClass = `rank-${r.rank}`;

      html += `
        <div class="runner-card ${rankClass}">
          <div class="runner-header">
            <div class="runner-id-block">
              <div class="rank-badge">${r.rank}</div>
              <div class="runner-number-gate">
                <span>${r.number}</span>
                <span class="runner-gate-sub">St:${r.gate || r.number}</span>
              </div>
              <div class="runner-title-group">
                <div class="runner-name-row" style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                  <h3 class="runner-name">${r.name}</h3>
                  ${r.equipment ? `<span class="equipment-badge" style="background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.22); border-radius:4px; padding:1px 6px; font-size:0.75rem; color:#f8fafc; font-weight:700;" title="Resmi Teçhizat / Aksesuar">${r.equipment}</span>` : ''}
                  ${r.is_scratched ? `<span style="background:rgba(239,68,68,0.25); border:1px solid #ef4444; border-radius:4px; padding:1px 6px; font-size:0.75rem; color:#ef4444; font-weight:800;">🚫 KOŞMAZ</span>` : ''}
                  <span class="horse-equipment">${r.age || '3y'} • ${r.sire || 'Baba'} / ${r.dam || 'Anne'}</span>
                </div>
                <div class="runner-subline">
                  <span>Jokey: <strong>${r.jockey || '-'}</strong></span>
                  <span>Sıklet: <strong>${r.weight} kg</strong></span>
                  <span>KGS: <strong>${r.kgs} gün</strong></span>
                  <span>Handikap: <strong>${r.handicap}</strong></span>
                  <span>Son 6: <strong>${r.last_6 || '-'}</strong></span>
                </div>
              </div>
            </div>

            <div class="runner-prob-block">
              <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                ${r.is_scratched ? `
                  <span style="color:#ef4444; font-weight:700; font-size:0.8rem; padding:6px 10px; background:rgba(239,68,68,0.1); border-radius:6px; border:1px dashed #ef4444;">🚫 Yarış Dışı</span>
                ` : `
                  <button class="btn-runner-select ${window.couponApp?.isHorseBanko(race.race_number, r.number) ? 'is-banko' : (window.couponApp?.isHorseSelected(race.race_number, r.number) ? 'selected' : '')}" 
                          onclick="window.couponApp.toggleHorseCurrentRace(${r.number})"
                          title="Bu atı kupona ekle / çıkar">
                    ${window.couponApp?.isHorseBanko(race.race_number, r.number) ? '⭐ Bankonuz' : (window.couponApp?.isHorseSelected(race.race_number, r.number) ? '✓ Kuponda' : '➕ Kupona Ekle')}
                  </button>
                `}
                <div class="prob-score-pill" style="${r.is_scratched ? 'opacity:0.4;' : ''}">
                  <span>%${r.win_probability}</span>
                  <small>Kazanma İhtimali</small>
                </div>
              </div>
              <div style="display:flex; align-items:center; gap:0.4rem;">
                <span class="prob-tag-badge ${r.is_value_bet ? 'value-bet' : ''}">
                  ${r.value_tag || (r.rank === 1 ? 'Favori' : 'Plase')}
                </span>
                ${r.agf > 0 ? `<span style="font-size:0.72rem; color:var(--text-muted);">AGF: %${r.agf}</span>` : ''}
              </div>
            </div>
          </div>

          <!-- Advanced Breeding, Wet/Dry & Jockey Synergy Badges -->
          <div style="display:flex; flex-wrap:wrap; gap:0.5rem; margin:0.75rem 0 0.5rem 0;">
            <div class="meta-chip" style="font-size:0.75rem; background:rgba(212,175,55,0.1); border-color:var(--border-gold); color:var(--gold-400);">
              🧬 <strong>Orijin (${r.sire || 'Baba'}):</strong> ${pa.surface_match || 'Dengeli'} (%${pa.score || 75})
            </div>
            <div class="meta-chip" style="font-size:0.75rem; background:rgba(245,158,11,0.1); border-color:rgba(245,158,11,0.3); color:var(--gold-400);">
              🏢 <strong>Antrenör (${r.trainer || '-'}):</strong> %${r.trainer_score || 74} Ahır Gücü
            </div>
            <div class="meta-chip" style="font-size:0.75rem; background:rgba(6,182,212,0.1); border-color:rgba(6,182,212,0.3); color:var(--cyan-400);">
              🌧️ <strong>Pist/Zemin:</strong> ${ca.condition || 'Normal Zemin'}
            </div>
            <div class="meta-chip" style="font-size:0.75rem; background:rgba(139,92,246,0.1); border-color:rgba(139,92,246,0.3); color:var(--purple-400);">
              🏆 <strong>Kariyer:</strong> ${mat.stage || 'Form Zirvesi'}
            </div>
            <div class="meta-chip" style="font-size:0.75rem; background:rgba(16,185,129,0.1); border-color:rgba(16,185,129,0.3); color:var(--emerald-400);">
              ⭐ <strong>Jokey Sinerjisi:</strong> ${syn.is_master ? 'Usta Jokey' : 'Dengeli Biniş'} (%${syn.jockey_score || 80})
            </div>
            <div class="meta-chip" style="font-size:0.75rem; background:rgba(59,130,246,0.1); border-color:rgba(59,130,246,0.3); color:var(--blue-400);">
              🔋 <strong>Dinlenme (${r.kgs || 20} gün):</strong> ${r.kgs_bonus >= 0 ? 'İdeal Form Döngüsü' : 'Riskli Periyot'}
            </div>
          </div>

          <!-- 5 Key Metrics Grid -->
          <div class="runner-metrics-grid">
            <div class="metric-item">
              <span class="metric-label">Düzeltilmiş Derece</span>
              <span class="metric-value" style="color:var(--emerald-400);">
                ${ta.adjusted_time_str || '-'}
              </span>
              <span class="metric-sub">${ta.is_exact_match ? 'Bu mesafedeki rekoru' : 'Uyarlanmış tempo'}</span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Beyer Hız Endeksi</span>
              <span class="metric-value">
                ${ta.speed_figure || 70} <small style="font-size:0.7rem; color:var(--text-muted);">/100</small>
              </span>
              <span class="metric-sub">Pist rekoruna oranı</span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Pist & Yüzey Uyumu</span>
              <span class="metric-value">
                %${sa.score || 60}
              </span>
              <span class="metric-sub">${sa.podium_count || 0} tabela (${race.surface})</span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Galop Sprint Skoru</span>
              <span class="metric-value">
                ${ga.mean_400_pace || '25.5'}s
              </span>
              <span class="metric-sub ${ga.outlier_count > 0 ? 'metric-badge-warn' : 'metric-badge-ok'}">
                ● ${ga.status_badge || 'İstikrarlı'}
              </span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Sıklet / Jokey Katkısı</span>
              <span class="metric-value">
                ${r.weight} kg
              </span>
              <span class="metric-sub">${r.jockey_score >= 90 ? '⭐ Usta Jokey' : 'Dengeli Biniş'}</span>
            </div>
          </div>

          <!-- 18-Factor Transparent Winning Drivers & Risks Box -->
          ${(r.winning_factors && ((r.winning_factors.dominant_factors && r.winning_factors.dominant_factors.length > 0) || (r.winning_factors.risk_factors && r.winning_factors.risk_factors.length > 0))) ? `
            <div class="winning-factors-box">
              <div class="winning-factors-header">
                <div class="winning-factors-title">
                  <span>🏆 Neden Kazanır? / Kazandıran Faktörler (18 Kriter Analizi)</span>
                </div>
                <span style="font-size:0.7rem; color:var(--gold-400); font-weight:700;">1.207 Koşu Empirik Modeli</span>
              </div>
              
              <div class="factor-chips-container">
                ${(r.winning_factors.dominant_factors || []).map(df => `
                  <div class="factor-chip" title="${df.desc}">
                    <span>${df.icon || '⭐'}</span>
                    <span>${df.factor}</span>
                    <span class="factor-chip-impact">${df.impact}</span>
                  </div>
                `).join('')}
                ${(r.winning_factors.risk_factors || []).map(rf => `
                  <div class="factor-chip factor-chip-risk" title="${rf.desc}">
                    <span>${rf.icon || '⚠️'}</span>
                    <span>${rf.factor}</span>
                    <span class="factor-chip-impact" style="color:#f87171;">${rf.impact}</span>
                  </div>
                `).join('')}
              </div>

              ${r.winning_factors.factor_summary ? `
                <div class="factor-summary-text">
                  <strong style="color:var(--text-main);">📌 Analiz Özeti:</strong> ${r.winning_factors.factor_summary}
                </div>
              ` : ''}
            </div>
          ` : ''}

          <!-- Explainable AI Rationale Box -->
          <div class="rationale-box">
            <div class="rationale-title">
              💡 Neden ${r.rank}. Sırada? (Yapay Zeka Analiz Kararı)
            </div>
            ${r.rationale || 'Detaylı analiz oluşturuldu.'}
          </div>

          <!-- Footer Action Buttons -->
          <div class="runner-card-footer">
            <button class="btn-glass" onclick="window.app.openGallopModal('${r.name.replace(/'/g, "\\'")}', ${r.handicap})">
              📋 Galop Detayı & İdman Kayıtları
            </button>
            <button class="btn-glass" onclick="window.app.openH2HModal(${r.number})">
              ⚔️ Başka Atla Kıyasla (H2H)
            </button>
            <button class="btn-glass" style="color:var(--gold-400); font-weight:700;" onclick="window.couponApp.setBanko(${race.race_number}, ${r.number})">
              ⭐ Tek Banko Yap
            </button>
            <button class="btn-primary" onclick="window.couponApp.toggleHorseCurrentRace(${r.number})">
              ${window.couponApp?.isHorseSelected(race.race_number, r.number) ? '✓ Kupondan Çıkar' : '➕ Kupona Ekle'}
            </button>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  }

  /* ----------------------------------------------------------------------
     VIEW 2: DISTANCE & TIME COMPARISON MATRIX
     ---------------------------------------------------------------------- */
  renderMatrixView(race, container) {
    const runners = [...(race.runners || [])].sort((a, b) => {
      const t1 = a.time_analysis?.adjusted_time_sec || 999;
      const t2 = b.time_analysis?.adjusted_time_sec || 999;
      return t1 - t2;
    });

    const bestTimeSec = runners[0]?.time_analysis?.adjusted_time_sec || 80;
    const worstTimeSec = runners[runners.length - 1]?.time_analysis?.adjusted_time_sec || (bestTimeSec + 5);

    let html = `
      <div class="matrix-container">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem;">
          <div>
            <h3 style="font-family:var(--font-heading); font-size:1.2rem; font-weight:700;">
              ⏱️ ${race.distance}m ${race.surface} Süre ve Derece Kıyaslama Tablosu
            </h3>
            <p style="font-size:0.8rem; color:var(--text-secondary);">
              Atların bu mesafedeki resmi en iyi dereceleri, yakın mesafe tempo dönüşümleri ve sıklet cezaları karşılaştırılmıştır.
            </p>
          </div>
        </div>

        <table class="matrix-table">
          <thead>
            <tr>
              <th>Sıra</th>
              <th>At İsmi</th>
              <th>Resmi En İyi</th>
              <th>Hesaplanan Düzeltilmiş Derece</th>
              <th>100m Temposu</th>
              <th>Sıklet Farkı</th>
              <th>Mesafe Projeksiyon Barı</th>
              <th>Hız Puanı</th>
            </tr>
          </thead>
          <tbody>
            ${runners.map((r, i) => {
              const ta = r.time_analysis || {};
              const diffSec = ((ta.adjusted_time_sec || bestTimeSec) - bestTimeSec).toFixed(2);
              const barPercent = Math.max(15, 100 - (((ta.adjusted_time_sec || bestTimeSec) - bestTimeSec) / Math.max(1, worstTimeSec - bestTimeSec)) * 85);

              return `
                <tr>
                  <td><strong style="color:var(--gold-400);">${i + 1}.</strong></td>
                  <td>
                    <strong>#${r.number} ${r.name}</strong>
                    <div style="font-size:0.74rem; color:var(--text-secondary);">${r.jockey} (${r.weight}kg)</div>
                  </td>
                  <td>${r.best_time || '<span style="color:var(--text-muted);">-</span>'}</td>
                  <td>
                    <strong style="color:var(--emerald-400); font-size:0.95rem;">${ta.adjusted_time_str}</strong>
                    ${i === 0 ? '<span style="font-size:0.68rem; background:rgba(16,185,129,0.2); color:var(--emerald-400); padding:0.1rem 0.35rem; border-radius:4px; margin-left:0.3rem;">En Hızlı</span>' : `<span style="font-size:0.75rem; color:var(--rose-500); margin-left:0.3rem;">+${diffSec}s</span>`}
                  </td>
                  <td>${ta.pace_100m} sn/100m</td>
                  <td>${ta.weight_penalty_sec > 0 ? `+${ta.weight_penalty_sec}s` : (ta.weight_penalty_sec < 0 ? `${ta.weight_penalty_sec}s` : '0.0s')}</td>
                  <td style="min-width:180px;">
                    <div class="time-bar-wrapper">
                      <div class="time-bar-bg">
                        <div class="time-bar-fill" style="width:${barPercent}%;"></div>
                      </div>
                      <span style="font-size:0.75rem; font-weight:700;">${barPercent.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td><strong>${ta.speed_figure}</strong></td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;

    container.innerHTML = html;
  }

  /* ----------------------------------------------------------------------
     VIEW 3: GALLOP & WORKOUT LAB (Outlier detection breakdown)
     ---------------------------------------------------------------------- */
  renderGallopsView(race, container) {
    const runners = race.runners || [];

    let html = `
      <div class="gallop-lab-grid">
        <div style="background:rgba(22,32,56,0.5); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); padding:1.25rem;">
          <h3 style="font-family:var(--font-heading); font-size:1.2rem; font-weight:700; margin-bottom:0.4rem;">
            🏇 İdman Pisti ve Galop Analiz Laboratuvarı
          </h3>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:1rem;">
            TJK standart sprint kriterlerine (400m / 600m / 800m) göre aşırı dalgalanma gösteren (örn. 400m 40sn kenter/gezinti) çalışmalar
            <strong>otomatik olarak ayıklanmış</strong>, sadece tutarlı idmanların gerçek sprint temposu hesaplamaya dahil edilmiştir.
          </p>

          <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(360px, 1fr)); gap:1.2rem;">
            ${runners.map(r => {
              const ga = r.gallop_analysis || {};
              const gallops = ga.gallops || [];

              return `
                <div class="gallop-card">
                  <div class="gallop-card-header">
                    <div>
                      <h4 style="font-size:1.05rem; font-weight:700;">#${r.number} ${r.name}</h4>
                      <span style="font-size:0.75rem; color:var(--text-secondary);">${r.jockey} • Handikap: ${r.handicap}</span>
                    </div>
                    <div style="text-align:right;">
                      <span style="font-family:var(--font-heading); font-size:1.2rem; font-weight:800; color:var(--emerald-400);">
                        ${ga.gallop_score} <small style="font-size:0.7rem; color:var(--text-muted);">Puan</small>
                      </span>
                      <div style="font-size:0.72rem; font-weight:700; color:${ga.outlier_count > 0 ? 'var(--gold-400)' : 'var(--emerald-400)'};">
                        ● ${ga.status_badge}
                      </div>
                    </div>
                  </div>

                  ${ga.outlier_count > 0 ? `
                    <div class="outlier-alert-banner">
                      ⚠️ <strong>Filtre Devrede:</strong> ${ga.outlier_count} adet aşırı dalgalı/ölçü dışı çalışma ortalamadan çıkarıldı.
                    </div>
                  ` : ''}

                  <table class="gallop-log-table">
                    <thead>
                      <tr>
                        <th>Tarih</th>
                        <th>Mesafe</th>
                        <th>Derece</th>
                        <th>400m Eşdeğeri</th>
                        <th>Durum</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${gallops.map(g => `
                        <tr class="${g.is_outlier ? 'gallop-row-outlier' : ''}">
                          <td>${g.date}</td>
                          <td>${g.distance}m</td>
                          <td><strong>${g.time_str}</strong></td>
                          <td>${g.pace_400}s</td>
                          <td>
                            ${g.is_outlier ? `<span class="badge-outlier" title="${g.outlier_reason}">Dalgalı (Çıkarıldı)</span>` : '<span style="color:var(--emerald-400); font-size:0.75rem; font-weight:600;">Geçerli</span>'}
                          </td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  /* ----------------------------------------------------------------------
     VIEW 4: 2D INTERACTIVE CANVAS RACE SIMULATOR
     ---------------------------------------------------------------------- */
  renderSimulatorView(race, container) {
    let html = `
      <div class="simulator-container">
        <div class="simulator-controls">
          <div>
            <h3 style="font-family:var(--font-heading); font-size:1.2rem; font-weight:700;">
              🎮 2D Canlı Koşu ve Taktik Tempo Simülatörü
            </h3>
            <p style="font-size:0.8rem; color:var(--text-secondary);">
              Atların öncü/sprinter taktikleri, ivmelenme eğrileri ve son 400m sprint potansiyelleri gerçek zamanlı canlandırılır.
            </p>
          </div>

          <div class="sim-buttons">
            <button class="btn-primary" id="btnSimPlay">▶️ Başlat</button>
            <button class="btn-glass" id="btnSimPause">⏸️ Duraklat</button>
            <button class="btn-glass" id="btnSimReset">🔄 Sıfırla</button>
            <select id="simSpeedSelect" style="background:#1e293b; color:#fff; border:1px solid rgba(255,255,255,0.1); padding:0.45rem; border-radius:6px; font-size:0.82rem;">
              <option value="1">Hız: 1x</option>
              <option value="2" selected>Hız: 2x</option>
              <option value="4">Hız: 4x</option>
            </select>
          </div>
        </div>

        <div class="sim-ticker" id="simTicker">
          <span>🎙️ <strong>Spiker:</strong> Atlar start boxlarına yerleşiyor.</span>
        </div>

        <div class="sim-canvas-wrapper">
          <canvas id="raceCanvas"></canvas>
        </div>
      </div>
    `;

    container.innerHTML = html;

    // Reconnect simulator to the new canvas element
    setTimeout(() => {
      this.simulator = new window.RaceSimulator("raceCanvas", "simTicker");
      this.simulator.loadRace(race);

      document.getElementById("btnSimPlay")?.addEventListener("click", () => this.simulator.start());
      document.getElementById("btnSimPause")?.addEventListener("click", () => this.simulator.pause());
      document.getElementById("btnSimReset")?.addEventListener("click", () => this.simulator.stop());
      document.getElementById("simSpeedSelect")?.addEventListener("change", (e) => {
        this.simulator.setSpeed(parseFloat(e.target.value));
      });
    }, 50);
  }

  /* ----------------------------------------------------------------------
     VIEW 5: BET TICKET & COUPON BUILDER
     ---------------------------------------------------------------------- */
  renderCouponView(container) {
    let html = `
      <div class="coupon-container">
        <div id="couponRacesContainer" class="coupon-races-card"></div>
        <div id="couponSummaryContainer" class="coupon-summary-card"></div>
      </div>
    `;
    container.innerHTML = html;
    this.couponBuilder.container = document.getElementById("couponRacesContainer");
    this.couponBuilder.summary = document.getElementById("couponSummaryContainer");
    if (!this.couponBuilder.programData) {
      this.couponBuilder.loadProgram(this.currentProgram);
    } else {
      this.couponBuilder.render();
      this.couponBuilder.updateFloatingBar();
    }
  }

  /* ----------------------------------------------------------------------
     VIEW 6: ALL BET TYPES & ANALYSIS (2li, 3lü, Tabela, vs.)
     ---------------------------------------------------------------------- */
  renderAllBetsView(race, container) {
    if (!race.all_bets) {
      container.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: var(--text-secondary);">
          <h3>📊 Bu koşu için detaylı bahis analizleri (ikili, tabela vb.) hesaplanıyor...</h3>
        </div>
      `;
      return;
    }
    
    let html = `
      <div class="all-bets-container" style="display: grid; gap: 1.5rem; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));">
        <div style="grid-column: 1 / -1;">
          <h3 style="font-family:var(--font-heading); font-size:1.3rem; font-weight:700; color:var(--emerald-400);">🎯 ${race.name} TJK Bahis Türleri Analizi</h3>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Yapay zeka modelimizin İkili, 3'lü, Tabela ve 5'li bahis kombinasyonları için ürettiği potansiyel sonuçlar.</p>
        </div>
    `;

    Object.entries(race.all_bets).forEach(([betType, analysis]) => {
      html += `
        <div class="bet-card" style="background: var(--bg-surface-elevated); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
            <h4 style="font-size:1.1rem; color:var(--gold-400); margin:0; text-transform:uppercase;">${betType.replace(/_/g, ' ')}</h4>
            <span class="badge" style="background:rgba(245,158,11,0.2); color:var(--gold-400); padding: 0.2rem 0.5rem; border-radius:4px; font-size:0.75rem; font-weight:bold;">Güven: %${analysis.confidence || 75}</span>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1rem;">${analysis.description || 'Yapay zeka değerlendirmesi'}</p>
          <div style="display:flex; flex-direction:column; gap:0.5rem;">
            ${(analysis.combinations || []).map((combo, idx) => `
              <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px;">
                <span style="font-weight:bold; font-size: 0.95rem; letter-spacing: 1px; color:var(--text-main);">${combo.combo}</span>
                <span style="font-size:0.75rem; color: ${idx === 0 ? 'var(--emerald-400)' : 'var(--text-muted)'};">${idx === 0 ? 'Öncelikli' : 'Alternatif'}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  }

  /* ----------------------------------------------------------------------
     VIEW 7: RACE RESULTS
     ---------------------------------------------------------------------- */
  renderResultsView(race, container) {
    if (!race.results || (!race.results.standings && Object.keys(race.results).length === 0)) {
      container.innerHTML = `
        <div style="padding: 3rem 1.5rem; text-align: center; color: var(--text-secondary); background: var(--bg-surface-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-subtle);">
          <div style="font-size: 2.5rem; margin-bottom: 0.8rem;">🏁</div>
          <h3 style="margin-bottom:0.5rem; font-family:var(--font-heading); color:var(--text-main);">Bu Koşunun Resmi Sonuçları Henüz Açıklanmadı</h3>
          <p style="max-width: 500px; margin: 0 auto 1.5rem auto; font-size: 0.88rem;">Yarış tamamlandığında TJK resmi sonuçları, bitiriş dereceleri, ganyan oranları ve ikramiyeler anlık olarak burada görüntülenecektir.</p>
          <button class="btn-primary" onclick="window.app.refreshRaceResults()" style="display:inline-flex; align-items:center; gap:0.4rem; padding:0.6rem 1.4rem;">
            🔄 Sonuçları TJK'dan Şimdi Sorgula
          </button>
        </div>
      `;
      return;
    }

    const res = race.results;
    const standings = res.standings || [];
    const dividends = res.dividends || {};
    const acc = race.accuracy_report || {};

    let html = `<div class="results-container">`;

    // 1. AI Accuracy & Performance Report
    if (acc.badges && acc.badges.length > 0) {
      html += `
        <div class="accuracy-banner">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
            <div style="display:flex; align-items:center; gap:0.5rem;">
              <span style="font-size:1.4rem;">🎯</span>
              <strong style="font-family:var(--font-heading); color:#fff; font-size:1rem;">Yapay Zeka Tahmin Başarı Karnesi - ${race.name}</strong>
            </div>
            <button class="btn-glass" onclick="window.app.refreshRaceResults()" style="padding:0.25rem 0.65rem; font-size:0.75rem;">
              🔄 Yenile
            </button>
          </div>
          <div class="accuracy-badges-row">
            ${acc.badges.map(b => `<span class="accuracy-badge-item">${b}</span>`).join('')}
          </div>
        </div>
      `;
    }

    // 2. Official Standings Table (Finish Order)
    if (standings.length > 0) {
      // Create quick lookup for predicted rank
      const predRankMap = {};
      (race.runners || []).forEach(rn => {
        predRankMap[rn.number] = rn.rank;
      });

      html += `
        <div class="standings-table-wrapper">
          <div style="padding:1rem 1.2rem; background:rgba(14,21,38,0.9); border-bottom:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0; font-family:var(--font-heading); color:var(--emerald-400); font-size:0.95rem;">
              🏆 Resmi Varış Sıralaması & Dereceler (${race.distance}m ${race.surface})
            </h4>
            <span style="font-size:0.78rem; color:var(--text-muted);">${standings.length} At Koştu</span>
          </div>
          <div style="overflow-x:auto;">
            <table class="standings-table">
              <thead>
                <tr>
                  <th style="width:70px; text-align:center;">Sıra</th>
                  <th>At No & İsmi</th>
                  <th>Jokey</th>
                  <th style="text-align:center;">Kilo</th>
                  <th style="text-align:center;">Derece</th>
                  <th style="text-align:right;">Ganyan</th>
                  <th style="text-align:center;">Fark</th>
                  <th style="text-align:center;">Yapay Zeka Tahmini</th>
                </tr>
              </thead>
              <tbody>
      `;

      standings.forEach(s => {
        let orderBadgeClass = "order-badge-standard";
        if (s.order === 1) orderBadgeClass = "order-badge-gold";
        else if (s.order === 2) orderBadgeClass = "order-badge-silver";
        else if (s.order === 3) orderBadgeClass = "order-badge-bronze";

        const hNo = s.horse_number || s.gate || s.order;
        const predRank = predRankMap[hNo];
        let predBadge = `<span style="color:var(--text-muted); font-size:0.78rem;">#${predRank || '-'}</span>`;
        if (predRank === 1) {
          predBadge = `<span style="background:rgba(245,158,11,0.2); color:var(--gold-400); padding:0.15rem 0.5rem; border-radius:4px; font-weight:800; font-size:0.75rem; border:1px solid var(--gold-400);">1. Banko</span>`;
        } else if (predRank <= 3) {
          predBadge = `<span style="background:rgba(16,185,129,0.15); color:var(--emerald-400); padding:0.15rem 0.5rem; border-radius:4px; font-weight:700; font-size:0.75rem;">${predRank}. Plase</span>`;
        }

        html += `
          <tr>
            <td style="text-align:center;">
              <span class="${orderBadgeClass}">${s.order}.</span>
            </td>
            <td>
              <div style="display:flex; align-items:center; gap:0.5rem;">
                <span class="horse-pill-num">${hNo}</span>
                <strong style="color:#fff;">${s.name}</strong>
              </div>
            </td>
            <td style="color:var(--text-secondary); font-size:0.82rem;">${s.jockey}</td>
            <td style="text-align:center; color:var(--text-muted); font-size:0.82rem;">${s.weight} kg</td>
            <td style="text-align:center; font-family:var(--font-mono); font-weight:700; color:var(--gold-400);">${s.time || '-'}</td>
            <td style="text-align:right; font-weight:800; color:var(--emerald-400);">${s.ganyan ? s.ganyan + ' TL' : '-'}</td>
            <td style="text-align:center; color:var(--text-muted); font-size:0.8rem;">${s.margin || '-'}</td>
            <td style="text-align:center;">${predBadge}</td>
          </tr>
        `;
      });

      html += `
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    // 3. Official Payout Dividends
    if (Object.keys(dividends).length > 0) {
      html += `
        <div style="background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); padding:1.2rem 1.5rem;">
          <h4 style="margin:0 0 0.8rem 0; font-family:var(--font-heading); color:var(--gold-400); font-size:0.95rem;">
            💰 Resmi Bahis İkramiyeleri & Kazanç Dağılımı
          </h4>
          <div class="dividends-grid">
      `;

      Object.entries(dividends).forEach(([betName, prize]) => {
        html += `
          <div class="dividend-card">
            <span class="dividend-name">${betName}</span>
            <span class="dividend-val">${prize}</span>
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;
    }

    html += `</div>`;
    container.innerHTML = html;
  }

  /* ----------------------------------------------------------------------
     TJK TV PIP CONTROLS
     ---------------------------------------------------------------------- */
  toggleTjkTv(forceState = null) {
    const pip = document.getElementById("tjkTvPip");
    if (!pip) return;
    
    const isHidden = pip.classList.contains("hidden");
    const willShow = forceState !== null ? forceState : isHidden;
    
    if (willShow) {
      pip.classList.remove("hidden");
      pip.classList.remove("minimized");
    } else {
      pip.classList.add("hidden");
    }
  }

  toggleTjkTvMinimize() {
    const pip = document.getElementById("tjkTvPip");
    if (pip) {
      pip.classList.toggle("minimized");
    }
  }

  /* ----------------------------------------------------------------------
     MODAL CONTROLS
     ---------------------------------------------------------------------- */
  async openGallopModal(horseName, rating) {
    if (!this.gallopModal || !this.gallopModalBody) return;
    this.gallopModalBody.innerHTML = `<div class="spinner"></div>`;
    this.gallopModal.classList.add("open");

    try {
      const res = await fetch(`/api/gallops?horse=${encodeURIComponent(horseName)}&rating=${rating || 40}`);
      const json = await res.json();
      if (json.success && json.analysis) {
        const ga = json.analysis;
        this.gallopModalBody.innerHTML = `
          <h3 style="font-family:var(--font-heading); font-size:1.3rem; margin-bottom:0.5rem;">${horseName} İdman Raporu</h3>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:1rem;">${ga.summary}</p>
          <table class="gallop-log-table">
            <thead>
              <tr><th>Tarih</th><th>Mesafe</th><th>Derece</th><th>400m Eşdeğeri</th><th>Pist</th><th>Durum</th></tr>
            </thead>
            <tbody>
              ${(ga.gallops || []).map(g => `
                <tr class="${g.is_outlier ? 'gallop-row-outlier' : ''}">
                  <td>${g.date}</td>
                  <td>${g.distance}m</td>
                  <td><strong>${g.time_str}</strong></td>
                  <td>${g.pace_400}s</td>
                  <td>${g.track}</td>
                  <td>${g.is_outlier ? `<span class="badge-outlier">${g.outlier_reason}</span>` : '<span style="color:var(--emerald-400);">Standart Uyumlu</span>'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }
    } catch (err) {
      this.gallopModalBody.innerHTML = `<p style="color:var(--rose-500);">Galop verisi çekilemedi.</p>`;
    }
  }

  closeGallopModal() {
    if (this.gallopModal) this.gallopModal.classList.remove("open");
  }

  openH2HModal(horseNumber) {
    const race = this.getCurrentRace();
    if (!race) return;
    const h1 = horseNumber;
    const h2 = (race.runners || []).find(r => r.number !== horseNumber)?.number || 2;
    this.h2hComparator.open(race.runners, h1, h2);
  }

  closeH2HModal() {
    this.h2hComparator.close();
  }

  openPwaModal() {
    if (this.pwaModal) this.pwaModal.classList.add("open");
  }

  closePwaModal() {
    if (this.pwaModal) this.pwaModal.classList.remove("open");
  }

  refreshData() {
    this.selectCity(this.currentCity);
  }

  /* ----------------------------------------------------------------------
     TJK / TAY TV LIVE STREAM & PIP CONTROLLER
     ---------------------------------------------------------------------- */
  /* ----------------------------------------------------------------------
     TAY TV & E-BAYİ LIVE STREAM & PIP CONTROLLER
     ---------------------------------------------------------------------- */
  initTjkTv() {
    this.tjkTvPip = document.getElementById("tjkTvPip");
    this.tjkTvFrame = document.getElementById("tjkTvFrame");
    this.tayTvVideo = document.getElementById("tayTvVideo");
    this.raceAlertToast = document.getElementById("raceAlertToast");
    this.isTvPipOpen = false;
    this.isTvMinimized = false;
    this.currentTvSourceIdx = 0; // 0 = TAY TV, 1 = e-Bayi, 2 = YouTube
    this.hlsInstance = null;

    this.tvSources = [
      {
        name: "TAY TV (TJK Resmi HLS)",
        type: "hls",
        url: "https://tjktv-live.tjk.org/taytv/taytv.m3u8"
      },
      {
        name: "e-Bayi Canlı (ebayi.org HLS)",
        type: "hls",
        url: "https://tjktv.ercdn.net/tjktvmobil.m3u8"
      },
      {
        name: "YouTube Canlı Aktif Yayın",
        type: "iframe",
        url: "https://www.youtube.com/embed/hnZK5wXzQDk?autoplay=1&mute=0"
      }
    ];

    this.makePipDraggable();
    this.resolveLiveVideo();

    // Start stream immediately on page load
    if (this.tjkTvPip && !this.tjkTvPip.classList.contains("hidden")) {
      this.isTvPipOpen = true;
      setTimeout(() => this.applyCurrentTvSource(), 300);
      const toggleBtn = document.getElementById("btnToggleTjkTv");
      if (toggleBtn) {
        toggleBtn.innerHTML = `<span class="live-badge-glow" style="background:#10b981; box-shadow:0 0 10px #10b981;">YAYINDA</span> 📺 TJK TV Açık`;
        toggleBtn.style.borderColor = "var(--emerald-500)";
      }
    }
  }

  selectStreamSource(idx) {
    this.currentTvSourceIdx = idx % this.tvSources.length;
    this.applyCurrentTvSource();

    const btns = [
      document.getElementById("btnStreamTayTv"),
      document.getElementById("btnStreamEbayi"),
      document.getElementById("btnStreamYoutube")
    ];
    btns.forEach((b, i) => {
      if (b) b.classList.toggle("active", i === this.currentTvSourceIdx);
    });

    const title = document.getElementById("pipStreamTitle");
    if (title) {
      title.textContent = idx === 0 ? "🏇 TAY TV Canlı" : (idx === 1 ? "🐎 e-Bayi Canlı" : "🔴 YouTube Canlı");
    }
  }

  playHlsStream(hlsUrl) {
    const video = this.tayTvVideo || document.getElementById("tayTvVideo");
    const iframe = this.tjkTvFrame || document.getElementById("tjkTvFrame");
    if (!video) return;

    if (iframe) {
      iframe.classList.add("hidden");
      iframe.src = "about:blank";
    }
    video.classList.remove("hidden");

    if (this.hlsInstance) {
      this.hlsInstance.destroy();
      this.hlsInstance = null;
    }

    if (window.Hls && window.Hls.isSupported()) {
      this.hlsInstance = new window.Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 60,
        maxBufferLength: 30,
        liveSyncDurationCount: 3
      });
      this.hlsInstance.attachMedia(video);
      this.hlsInstance.on(window.Hls.Events.MEDIA_ATTACHED, () => {
        this.hlsInstance.loadSource(hlsUrl);
      });
      this.hlsInstance.on(window.Hls.Events.MANIFEST_PARSED, () => {
        video.muted = true;
        video.play().then(() => {
          const muteBtn = document.getElementById("btnPipMute");
          if (muteBtn) muteBtn.textContent = "🔇";
        }).catch(() => {});
      });
      this.hlsInstance.on(window.Hls.Events.ERROR, (event, data) => {
        if (data && data.fatal) {
          console.warn("HLS fatal error:", data.type, data.details);
          switch (data.type) {
            case window.Hls.ErrorTypes.NETWORK_ERROR:
              try { this.hlsInstance.startLoad(); } catch (e) {}
              break;
            case window.Hls.ErrorTypes.MEDIA_ERROR:
              try { this.hlsInstance.recoverMediaError(); } catch (e) {}
              break;
            default:
              try { this.hlsInstance.destroy(); } catch (e) {}
              this.hlsInstance = null;
              if (this.currentTvSourceIdx === 0) {
                this.selectStreamSource(1);
              } else if (this.currentTvSourceIdx === 1) {
                this.selectStreamSource(2);
              }
              break;
          }
        }
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = hlsUrl;
      video.muted = true;
      video.play().catch(() => {});
    } else {
      console.warn("HLS not supported in this browser, switching to YouTube");
      this.selectStreamSource(2);
    }
  }

  async resolveLiveVideo() {
    try {
      const res = await fetch("/api/tjktv");
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.video_id) {
          this.tvSources[2].url = `https://www.youtube.com/embed/${json.video_id}?autoplay=1&mute=0`;
        }
      }
    } catch (e) {
      // offline / static fallback
    }
  }

  toggleTjkTv(forceOpen) {
    if (!this.tjkTvPip) return;
    const isCurrentlyHidden = this.tjkTvPip.classList.contains("hidden");
    const shouldOpen = forceOpen !== undefined ? forceOpen : isCurrentlyHidden;

    if (shouldOpen) {
      this.tjkTvPip.classList.remove("hidden");
      this.isTvPipOpen = true;
      this.applyCurrentTvSource();
    } else {
      this.tjkTvPip.classList.add("hidden");
      this.isTvPipOpen = false;
      if (this.tayTvVideo) {
        this.tayTvVideo.pause();
      }
      if (this.hlsInstance) {
        this.hlsInstance.destroy();
        this.hlsInstance = null;
      }
      if (this.tjkTvFrame) {
        this.tjkTvFrame.src = "about:blank";
      }
    }

    const toggleBtn = document.getElementById("btnToggleTjkTv");
    if (toggleBtn) {
      if (this.isTvPipOpen) {
        toggleBtn.innerHTML = `<span class="live-badge-glow" style="background:#10b981; box-shadow:0 0 10px #10b981;">YAYINDA</span> 📺 TJK TV Açık`;
        toggleBtn.style.borderColor = "var(--emerald-500)";
      } else {
        toggleBtn.innerHTML = `<span class="live-badge-glow">CANLI</span> 📺 TJK TV (PiP)`;
        toggleBtn.style.borderColor = "";
      }
    }
  }

  applyCurrentTvSource() {
    const src = this.tvSources[this.currentTvSourceIdx];
    const video = this.tayTvVideo || document.getElementById("tayTvVideo");
    const iframe = this.tjkTvFrame || document.getElementById("tjkTvFrame");

    if (src.type === "hls") {
      this.playHlsStream(src.url);
    } else {
      if (video) {
        video.pause();
        video.classList.add("hidden");
      }
      if (this.hlsInstance) {
        this.hlsInstance.destroy();
        this.hlsInstance = null;
      }
      if (iframe) {
        iframe.classList.remove("hidden");
        iframe.src = src.url;
      }
    }
  }

  toggleTjkTvMinimize() {
    if (!this.tjkTvPip) return;
    this.isTvMinimized = !this.isTvMinimized;
    this.tjkTvPip.classList.toggle("minimized", this.isTvMinimized);
    const minBtn = document.getElementById("btnPipMin");
    if (minBtn) minBtn.textContent = this.isTvMinimized ? "◻" : "_";
  }

  togglePipMute() {
    const video = this.tayTvVideo || document.getElementById("tayTvVideo");
    const btn = document.getElementById("btnPipMute");
    if (!video) return;
    video.muted = !video.muted;
    if (btn) btn.textContent = video.muted ? "🔇" : "🔊";
  }

  requestNativePip() {
    const video = this.tayTvVideo || document.getElementById("tayTvVideo");
    if (video && document.pictureInPictureEnabled) {
      if (document.pictureInPictureElement) {
        document.exitPictureInPicture();
      } else {
        video.requestPictureInPicture().catch(err => {
          console.warn("Native PiP error:", err);
        });
      }
    }
  }

  requestFullscreenVideo() {
    const pip = this.tjkTvPip || document.getElementById("tjkTvPip");
    const video = this.tayTvVideo || document.getElementById("tayTvVideo");
    const target = video && !video.classList.contains("hidden") ? video : pip;
    if (target) {
      if (!document.fullscreenElement) {
        target.requestFullscreen().catch(err => {
          console.warn("Fullscreen error:", err);
        });
      } else {
        document.exitFullscreen();
      }
    }
  }

  cyclePipSize() {
    if (!this.tjkTvPip) return;
    const sizes = ["pip-compact", "pip-standard", "pip-wide"];
    let curr = sizes.findIndex(s => this.tjkTvPip.classList.contains(s));
    if (curr === -1) curr = 1;
    const next = (curr + 1) % sizes.length;
    sizes.forEach(s => this.tjkTvPip.classList.remove(s));
    this.tjkTvPip.classList.add(sizes[next]);
  }

  openTayTvOfficial() {
    const popout = window.open(
      "https://www.tjk.org/TR/YarisSever/Static/Canli", 
      "TayTvOfficialWindow", 
      "width=1040,height=680,menubar=no,toolbar=no,location=no,status=no,resizable=yes"
    );
    if (popout) popout.focus();
  }

  openEbayiOfficial() {
    const popout = window.open(
      "https://ebayi.org/canli-yayin", 
      "EbayiOfficialWindow", 
      "width=1040,height=680,menubar=no,toolbar=no,location=no,status=no,resizable=yes"
    );
    if (popout) popout.focus();
  }

  openTjkTvExternal() {
    this.openTayTvOfficial();
  }

  async refreshRaceResults() {
    if (!this.currentCity) return;
    try {
      const res = await fetch(`/api/program?city=${encodeURIComponent(this.currentCity)}&t=${Date.now()}`);
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.data) {
          this.currentProgram = json.data;
          this.renderRaceRibbon();
          this.renderCurrentRace();
          const refreshBtn = document.getElementById("btnRefresh");
          if (refreshBtn) {
            refreshBtn.textContent = "✓ Güncellendi";
            setTimeout(() => { if (refreshBtn) refreshBtn.textContent = "🔄 Yenile"; }, 2000);
          }
          return;
        }
      }
    } catch (e) {
      console.warn("Live results refresh error:", e);
    }
  }

  showRaceAlert(race, minsLeft) {
    if (!this.raceAlertToast) return;
    const title = document.getElementById("raceAlertTitle");
    const desc = document.getElementById("raceAlertDesc");
    if (title) title.textContent = `🏇 ${race.name || 'Koşu'} Başlamak Üzere! (${race.time || ''})`;
    if (desc) {
      desc.textContent = minsLeft > 0 
        ? `${race.distance}m ${race.surface} koşusuna yaklaşık ${minsLeft} dakika kaldı. TJK TV canlı yayını açıldı.`
        : `${race.distance}m ${race.surface} koşusu başladı! TJK TV canlı yayını bağlandı.`;
    }

    this.raceAlertToast.classList.remove("hidden");
    this.playRaceChime();

    clearTimeout(this._alertToastTimer);
    this._alertToastTimer = setTimeout(() => {
      this.closeRaceAlert();
    }, 8500);
  }

  closeRaceAlert() {
    if (this.raceAlertToast) this.raceAlertToast.classList.add("hidden");
  }

  playRaceChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(587.33, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.18);
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.5);
    } catch (e) {
      // Audio autoplay restrictions
    }
  }

  makePipDraggable() {
    const pip = this.tjkTvPip;
    const header = document.getElementById("tjkTvHeader");
    if (!pip || !header) return;

    let isDragging = false;
    let startX, startY, origLeft, origTop;

    const onPointerDown = (e) => {
      if (e.target.closest(".tjk-tv-btn")) return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      const rect = pip.getBoundingClientRect();
      origLeft = rect.left;
      origTop = rect.top;
      pip.style.bottom = "auto";
      pip.style.right = "auto";
      pip.style.left = `${origLeft}px`;
      pip.style.top = `${origTop}px`;
      document.addEventListener("pointermove", onPointerMove);
      document.addEventListener("pointerup", onPointerUp);
    };

    const onPointerMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      pip.style.left = `${Math.max(10, Math.min(window.innerWidth - pip.offsetWidth - 10, origLeft + dx))}px`;
      pip.style.top = `${Math.max(10, Math.min(window.innerHeight - 50, origTop + dy))}px`;
    };

    const onPointerUp = () => {
      isDragging = false;
      document.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("pointerup", onPointerUp);
    };

    header.addEventListener("pointerdown", onPointerDown);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.app = new TJKApp();
});
