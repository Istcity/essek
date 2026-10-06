/**
 * Premium Procedural Galloping Horse Renderer
 * - drawHorse(): vector horse + jockey with real 4-beat gallop leg cycle
 * - GallopStrip: animated hero strip with running horses, dust & parallax rails
 * - Splash screen controller
 */
(function () {
  const COATS = ['#3b2314', '#5a3520', '#1c1512', '#7a4a2a', '#4a2c1a', '#2a1d16'];

  function seg(ctx, x1, y1, x2, y2, w) {
    ctx.lineWidth = w;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  /**
   * Draw a galloping horse facing right.
   * @param {CanvasRenderingContext2D} ctx
   * @param {number} x center x
   * @param {number} y ground-ish center y (body center)
   * @param {number} s scale (1 = ~56px long)
   * @param {number} phase gallop phase (radians, increase over time)
   * @param {object} o { coat, silk, cap, number, glow }
   */
  function drawHorse(ctx, x, y, s, phase, o = {}) {
    const coat = o.coat || COATS[0];
    const silk = o.silk || '#f59e0b';
    const cap = o.cap || '#ffffff';
    const bob = -Math.abs(Math.sin(phase)) * 2.2;

    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);

    // Ground shadow
    ctx.fillStyle = 'rgba(0,0,0,0.38)';
    ctx.beginPath();
    ctx.ellipse(0, 19, 22 - Math.abs(Math.sin(phase)) * 3, 3.2, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.translate(0, bob);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Legs (gallop: rear pair then front pair, slight offsets)
    const legs = [
      { hx: -11, off: 0.0, front: false, far: true },
      { hx: 11, off: 2.3, front: true, far: true },
      { hx: -9, off: 0.55, front: false, far: false },
      { hx: 13, off: 2.85, front: true, far: false }
    ];
    const drawLeg = (L) => {
      const t = phase + L.off;
      const a1 = Math.PI / 2 + Math.sin(t) * (L.front ? 0.75 : 0.6);
      const kx = L.hx + Math.cos(a1) * 8.5;
      const ky = 4 + Math.sin(a1) * 8.5;
      const bend = L.front ? -(0.2 + Math.max(0, Math.cos(t)) * 1.3) : (0.2 + Math.max(0, -Math.cos(t)) * 1.1);
      const a2 = a1 + bend;
      const fx = kx + Math.cos(a2) * 9;
      const fy = ky + Math.sin(a2) * 9;
      ctx.strokeStyle = L.far ? shade(coat, -25) : coat;
      seg(ctx, L.hx, 3, kx, ky, 4.2);
      seg(ctx, kx, ky, fx, fy, 2.8);
      ctx.fillStyle = '#0a0a0a';
      ctx.beginPath();
      ctx.arc(fx, fy, 1.7, 0, Math.PI * 2);
      ctx.fill();
    };
    legs.filter(l => l.far).forEach(drawLeg);

    // Tail
    const tailWave = Math.sin(phase * 1.0) * 4;
    ctx.strokeStyle = shade(coat, -35);
    ctx.lineWidth = 3.4;
    ctx.beginPath();
    ctx.moveTo(-16, -3);
    ctx.quadraticCurveTo(-25, -6 + tailWave * 0.4, -31, 2 + tailWave);
    ctx.stroke();

    // Body
    const bodyGrad = ctx.createLinearGradient(0, -8, 0, 8);
    bodyGrad.addColorStop(0, shade(coat, 28));
    bodyGrad.addColorStop(1, shade(coat, -18));
    ctx.fillStyle = bodyGrad;
    ctx.beginPath();
    ctx.ellipse(0, 0, 17, 7.5, -0.05, 0, Math.PI * 2);
    ctx.fill();

    // Neck + head (stretches with stride)
    const nod = Math.sin(phase) * 1.6;
    ctx.beginPath();
    ctx.moveTo(9, -5);
    ctx.lineTo(19, -15 + nod);
    ctx.lineTo(24, -13 + nod);
    ctx.lineTo(17, 2);
    ctx.closePath();
    ctx.fill();
    ctx.save();
    ctx.translate(26, -13 + nod);
    ctx.rotate(0.55);
    ctx.beginPath();
    ctx.ellipse(0, 0, 7, 3.4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    // Ear
    ctx.beginPath();
    ctx.moveTo(21, -16 + nod);
    ctx.lineTo(22.5, -20 + nod);
    ctx.lineTo(24, -16 + nod);
    ctx.fill();
    // Mane
    ctx.strokeStyle = shade(coat, -40);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(10, -7);
    ctx.quadraticCurveTo(15, -14 + nod, 20, -16 + nod);
    ctx.stroke();
    // Eye
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(25, -14.5 + nod, 0.9, 0, Math.PI * 2);
    ctx.fill();

    // Saddle cloth with number
    ctx.fillStyle = silk;
    roundRect(ctx, -6, -6.5, 11, 8, 1.5);
    ctx.fill();
    if (o.number !== undefined) {
      ctx.fillStyle = luminance(silk) > 0.6 ? '#000' : '#fff';
      ctx.font = 'bold 6px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(o.number), -0.5, -2.3);
    }

    // Jockey (crouched forward)
    const jb = Math.sin(phase * 2) * 0.6;
    ctx.fillStyle = shade(silk, -10);
    ctx.beginPath();
    ctx.moveTo(-3, -7);
    ctx.quadraticCurveTo(0, -17 + jb, 8, -16 + jb);
    ctx.lineTo(9, -12 + jb);
    ctx.quadraticCurveTo(3, -11, 3, -7);
    ctx.closePath();
    ctx.fill();
    // Arm to reins
    ctx.strokeStyle = shade(silk, -20);
    seg(ctx, 6, -14 + jb, 15, -10 + nod * 0.5, 2);
    // Reins
    ctx.strokeStyle = 'rgba(0,0,0,0.6)';
    seg(ctx, 15, -10 + nod * 0.5, 25, -12 + nod, 0.7);
    // Leg of jockey
    ctx.strokeStyle = '#f3f4f6';
    seg(ctx, 0, -8, 4, -3, 2.2);
    // Helmet
    ctx.fillStyle = cap;
    ctx.beginPath();
    ctx.arc(10, -18.5 + jb, 3, 0, Math.PI * 2);
    ctx.fill();

    legs.filter(l => !l.far).forEach(drawLeg);

    ctx.restore();
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function hexToRgb(hex) {
    const h = hex.replace('#', '');
    const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function shade(hex, amt) {
    const [r, g, b] = hexToRgb(hex);
    const c = v => Math.max(0, Math.min(255, v + amt));
    return `rgb(${c(r)},${c(g)},${c(b)})`;
  }
  function luminance(hex) {
    const [r, g, b] = hexToRgb(hex);
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  }

  window.HorseArt = { drawHorse, shade };

  document.addEventListener('DOMContentLoaded', () => {
    // Splash screen horse runner & auto-dismiss
    const splash = document.getElementById('premiumSplash');
    const splashCanvas = document.getElementById('splashHorse');
    if (splashCanvas) {
      splashCanvas.width = 260;
      splashCanvas.height = 110;
      const sCtx = splashCanvas.getContext('2d');
      let sPhase = 0;
      let sActive = true;
      function animSplash() {
        if (!sActive || !splash || splash.classList.contains('done')) return;
        sCtx.clearRect(0, 0, splashCanvas.width, splashCanvas.height);
        drawHorse(sCtx, 130, 65, 1.35, sPhase, {
          coat: '#2a1d16',
          silk: '#10b981',
          cap: '#f59e0b',
          number: 1
        });
        sPhase += 0.18;
        requestAnimationFrame(animSplash);
      }
      requestAnimationFrame(animSplash);

      setTimeout(() => {
        sActive = false;
        if (splash) {
          splash.classList.add('done');
          setTimeout(() => {
            if (splash.parentNode) splash.parentNode.removeChild(splash);
          }, 600);
        }
      }, 700);
    }

    // Global luxury ripple effect on click
    document.addEventListener('pointerdown', (e) => {
      const btn = e.target.closest('.btn-primary, .btn-glass, .btn-lux, .view-tab, .race-pill, .track-tab');
      if (!btn) return;
      const rect = btn.getBoundingClientRect();
      const circle = document.createElement('span');
      const diameter = Math.max(rect.width, rect.height);
      const radius = diameter / 2;
      circle.style.width = circle.style.height = `${diameter}px`;
      circle.style.left = `${e.clientX - rect.left - radius}px`;
      circle.style.top = `${e.clientY - rect.top - radius}px`;
      circle.classList.add('ripple');
      const existing = btn.querySelector('.ripple');
      if (existing) existing.remove();
      btn.appendChild(circle);
      setTimeout(() => circle.remove(), 700);
    });
  });
})();
