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
    try {
      if (this.statusText) this.statusText.textContent = "TJK Şehirleri Yükleniyor...";
      const res = await fetch(`/api/cities?date=${this.currentDateStr}`);
      const json = await res.json();
      if (json.success && json.cities.length) {
        this.cities = json.cities;
        this.renderCities();
        // Load first domestic city or Bursa
        const defaultCity = this.cities.find(c => !c.is_foreign) || this.cities[0];
        this.selectCity(defaultCity.name);
      }
    } catch (err) {
      console.error("Cities load error:", err);
      if (this.statusText) this.statusText.textContent = "Çevrimdışı / Örnek Veri";
      this.selectCity("Bursa");
    }
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
  }

  async selectCity(cityName) {
    this.currentCity = cityName;
    this.renderCities();
    if (this.statusText) this.statusText.textContent = `${cityName} Bülteni Çekiliyor...`;

    try {
      const res = await fetch(`/api/program?city=${encodeURIComponent(cityName)}&date=${this.currentDateStr}`);
      const json = await res.json();
      if (json.success && json.data) {
        this.currentProgram = json.data;
        this.activeRaceIndex = 0;
        if (this.statusText) this.statusText.textContent = `Canlı TJK: ${cityName} (${this.currentProgram.races.length} Koşu)`;
        this.renderRaceRibbon();
        this.renderCurrentRace();
        this.couponBuilder.loadProgram(this.currentProgram);
      }
    } catch (err) {
      console.error("Program load error:", err);
      if (this.statusText) this.statusText.textContent = "Veri Yükleme Hatası";
    }
  }

  renderRaceRibbon() {
    if (!this.raceRibbon || !this.currentProgram) return;
    const races = this.currentProgram.races || [];

    this.raceRibbon.innerHTML = races.map((r, idx) => `
      <div class="race-pill ${idx === this.activeRaceIndex ? 'active' : ''}" onclick="window.app.selectRace(${idx})">
        <div class="race-pill-header">
          <span class="race-pill-title">${r.name}</span>
          <span class="race-pill-time">${r.time}</span>
        </div>
        <div class="race-pill-meta">
          <span>${r.distance}m</span>
          <span>•</span>
          <span>${r.surface}</span>
          <span>•</span>
          <span>${(r.runners || []).length} At</span>
        </div>
      </div>
    `).join('');
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
    this.activeView = viewName;
    document.querySelectorAll(".view-tab").forEach(tab => {
      tab.classList.toggle("active", tab.getAttribute("data-view") === viewName);
    });
    const race = this.getCurrentRace();
    if (race) this.renderActiveView(race);
  }

  renderActiveView(race) {
    const container = this.viewsContainer;
    if (!container) return;

    if (this.activeView === "predictions") {
      this.renderPredictionsView(race, container);
    } else if (this.activeView === "matrix") {
      this.renderMatrixView(race, container);
    } else if (this.activeView === "gallops") {
      this.renderGallopsView(race, container);
    } else if (this.activeView === "simulator") {
      this.renderSimulatorView(race, container);
    } else if (this.activeView === "coupon") {
      this.renderCouponView(container);
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
                <div class="runner-name-row">
                  <h3 class="runner-name">${r.name}</h3>
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
                <button class="btn-runner-select ${window.couponApp?.isHorseBanko(race.race_number, r.number) ? 'is-banko' : (window.couponApp?.isHorseSelected(race.race_number, r.number) ? 'selected' : '')}" 
                        onclick="window.couponApp.toggleHorseCurrentRace(${r.number})"
                        title="Bu atı kupona ekle / çıkar">
                  ${window.couponApp?.isHorseBanko(race.race_number, r.number) ? '⭐ Bankonuz' : (window.couponApp?.isHorseSelected(race.race_number, r.number) ? '✓ Kuponda' : '➕ Kupona Ekle')}
                </button>
                <div class="prob-score-pill">
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
}

document.addEventListener("DOMContentLoaded", () => {
  window.app = new TJKApp();
});
