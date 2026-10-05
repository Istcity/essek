/**
 * 2D Canvas Live Race Pace Simulator.
 * Simulates tactical pace, turn-of-foot acceleration, lane drift, and photo finish.
 */

class RaceSimulator {
  constructor(canvasId, tickerId) {
    this.canvas = document.getElementById(canvasId);
    this.ticker = document.getElementById(tickerId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.runners = [];
    this.raceData = null;
    this.isRunning = false;
    this.animationId = null;
    this.progress = 0; // 0 to 1
    this.speedMultiplier = 1;
    this.horsePositions = [];
    this.commentary = "Yarış başlamaya hazır. Atlar start boxlarına giriyor.";
    this.colors = [
      '#f59e0b', '#10b981', '#3b82f6', '#ec4899', '#8b5cf6',
      '#06b6d4', '#ef4444', '#14b8a6', '#f97316', '#a855f7',
      '#eab308', '#6366f1', '#84cc16', '#0ea5e9'
    ];
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * window.devicePixelRatio;
    this.canvas.height = (rect.height || 420) * window.devicePixelRatio;
    this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    this.draw();
  }

  loadRace(race) {
    this.stop();
    this.raceData = race;
    this.progress = 0;
    const runners = race.runners || [];

    // Initialize physical simulation state for each runner
    this.horsePositions = runners.map((r, i) => {
      const pace400 = r.gallop_analysis?.mean_400_pace || 25.5;
      const speedFig = r.time_analysis?.speed_figure || 75;
      const isFrontRunner = pace400 < 24.9 && (r.gate || i + 1) <= 5;
      const isCloser = pace400 > 26.0;

      return {
        number: r.number,
        name: r.name.split(' ')[0],
        jockey: r.jockey,
        color: this.colors[i % this.colors.length],
        gate: r.gate || i + 1,
        rank: r.rank,
        winProb: r.win_probability,
        baseSpeed: (speedFig / 80.0) * 1.0,
        earlySpeed: isFrontRunner ? 1.25 : (isCloser ? 0.85 : 1.05),
        lateKick: isCloser ? 1.35 : (isFrontRunner ? 0.90 : 1.1),
        currentDist: 0,
        laneY: 0,
        targetLaneY: 0,
        speed: 0
      };
    });

    this.commentary = `${race.name} (${race.distance}m ${race.surface}) startı için atlar hazır.`;
    this.updateTicker();
    this.draw();
  }

  start() {
    if (this.isRunning) return;
    if (this.progress >= 1) this.progress = 0;
    this.isRunning = true;
    this.lastTime = performance.now();
    this.loop();
  }

  pause() {
    this.isRunning = false;
    if (this.animationId) cancelAnimationFrame(this.animationId);
  }

  stop() {
    this.pause();
    this.progress = 0;
    if (this.horsePositions) {
      this.horsePositions.forEach(h => h.currentDist = 0);
    }
    this.draw();
  }

  setSpeed(mult) {
    this.speedMultiplier = mult;
  }

  loop() {
    if (!this.isRunning) return;
    const now = performance.now();
    const dt = (now - (this.lastTime || now)) / 1000;
    this.lastTime = now;

    // Advance race progress
    const raceDuration = Math.max(12, (this.raceData?.distance || 1400) / 100);
    this.progress += (dt / raceDuration) * this.speedMultiplier;

    if (this.progress >= 1) {
      this.progress = 1;
      this.isRunning = false;
      this.onFinish();
    } else {
      this.updatePhysics();
    }

    this.draw();
    if (this.isRunning) {
      this.animationId = requestAnimationFrame(() => this.loop());
    }
  }

  updatePhysics() {
    const p = this.progress;
    const dist = this.raceData?.distance || 1400;

    // Dynamic Commentary
    if (p < 0.15) {
      this.commentary = "Start verildi! Koşuya harika bir başlangıç yapıldı, ön grubun liderlik mücadelesi başladı.";
    } else if (p < 0.5) {
      const leader = [...this.horsePositions].sort((a, b) => b.currentDist - a.currentDist)[0];
      this.commentary = `Karşı düzlük geçiliyor. ${leader ? leader.name : 'Ön grup'} liderliği koruyor, tempo dengeli.`;
    } else if (p < 0.8) {
      this.commentary = "Son viraj dönülüyor! Dış kulvardan ataklar başladı, jokeyler teşviklere başladı!";
    } else if (p < 0.95) {
      const top2 = [...this.horsePositions].sort((a, b) => b.currentDist - a.currentDist).slice(0, 2);
      this.commentary = `Son 200 metre! ${top2[0]?.name} ve ${top2[1]?.name} başa baş mücadelede! Pota yaklaşıyor!`;
    }

    this.updateTicker();

    // Calculate current speed & position for each horse
    this.horsePositions.forEach((h) => {
      let speedFactor = h.baseSpeed;
      if (p < 0.3) {
        speedFactor *= h.earlySpeed;
      } else if (p > 0.7) {
        speedFactor *= h.lateKick;
      }

      // Small jitter for realism
      const jitter = (Math.sin(p * 50 + h.gate) * 0.04);
      h.speed = speedFactor + jitter;
      h.currentDist = p * dist * (h.speed / 1.0);
    });
  }

  onFinish() {
    const sorted = [...this.horsePositions].sort((a, b) => b.currentDist - a.currentDist);
    const winner = sorted[0];
    this.commentary = `🏁 FOTO FİNİŞ! ${winner.number} numara ${winner.name} fotoyu önde geçerek koşuyu kazandı!`;
    this.updateTicker();
  }

  updateTicker() {
    if (this.ticker) {
      this.ticker.innerHTML = `<span>🎙️ <strong>Spiker:</strong> ${this.commentary}</span>`;
    }
  }

  draw() {
    if (!this.canvas) return;
    const ctx = this.ctx;
    const rect = this.canvas.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height || 420;

    ctx.clearRect(0, 0, w, h);

    // Track surface background (Turf, Dirt, Synthetic)
    const surf = (this.raceData?.surface || "Çim").toLowerCase();
    let trackGrad;
    if (surf.includes("kum")) {
      trackGrad = ctx.createLinearGradient(0, 0, 0, h);
      trackGrad.addColorStop(0, '#382515');
      trackGrad.addColorStop(1, '#231508');
    } else if (surf.includes("sentetik")) {
      trackGrad = ctx.createLinearGradient(0, 0, 0, h);
      trackGrad.addColorStop(0, '#1e293b');
      trackGrad.addColorStop(1, '#0f172a');
    } else {
      // Çim (Turf)
      trackGrad = ctx.createLinearGradient(0, 0, 0, h);
      trackGrad.addColorStop(0, '#064e3b');
      trackGrad.addColorStop(1, '#022c22');
    }

    ctx.fillStyle = trackGrad;
    ctx.fillRect(0, 0, w, h);

    // Track Rails and lanes
    const margin = 24;
    const trackHeight = h - margin * 2;
    const totalRunners = Math.max(1, this.horsePositions.length);
    const laneHeight = Math.min(38, trackHeight / totalRunners);

    // Draw Starting Gate Line
    const startX = margin + 40;
    const finishX = w - margin - 50;

    // Finish Line Graphic
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 3;
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(finishX, margin);
    ctx.lineTo(finishX, h - margin);
    ctx.stroke();
    ctx.setLineDash([]);

    // Finish post label
    ctx.fillStyle = '#f59e0b';
    ctx.font = 'bold 11px Outfit, sans-serif';
    ctx.fillText('FINISH', finishX - 18, margin - 6);

    // Draw Lanes
    for (let i = 0; i <= totalRunners; i++) {
      const y = margin + i * laneHeight;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(margin, y);
      ctx.lineTo(w - margin, y);
      ctx.stroke();
    }

    // Distance progress markers (1000m, 600m, 400m, 200m)
    const markers = [0.25, 0.5, 0.75];
    markers.forEach(ratio => {
      const mx = startX + (finishX - startX) * ratio;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
      ctx.beginPath();
      ctx.moveTo(mx, margin);
      ctx.lineTo(mx, h - margin);
      ctx.stroke();
    });

    // Draw Horses
    const runSpan = finishX - startX;
    const maxDist = Math.max(...this.horsePositions.map(h => h.currentDist), 1);

    this.horsePositions.forEach((hItem, idx) => {
      const laneY = margin + idx * laneHeight + laneHeight / 2;
      const progressFraction = Math.min(1.02, hItem.currentDist / (this.raceData?.distance || 1400));
      const horseX = startX + progressFraction * runSpan;

      // Horse Shadow
      ctx.fillStyle = 'rgba(0,0,0,0.45)';
      ctx.beginPath();
      ctx.ellipse(horseX, laneY + 10, 14, 4, 0, 0, Math.PI * 2);
      ctx.fill();

      // Horse Body / Silk Badge Circle
      ctx.fillStyle = hItem.color;
      ctx.beginPath();
      ctx.arc(horseX, laneY, 11, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Runner Number
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 10px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(hItem.number, horseX, laneY);

      // Horse & Jockey Name Label
      ctx.textAlign = 'left';
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.font = '600 11px Inter, sans-serif';
      ctx.fillText(`${hItem.name}`, horseX + 16, laneY - 2);

      // Mini speed indicator
      ctx.fillStyle = 'rgba(148, 163, 184, 0.8)';
      ctx.font = '9px Inter, sans-serif';
      ctx.fillText(`J: ${hItem.jockey || '-'}`, horseX + 16, laneY + 9);
    });
  }
}

window.RaceSimulator = RaceSimulator;
