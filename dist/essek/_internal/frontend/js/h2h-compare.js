/**
 * Head-to-Head (Kafa Kafaya) Runner Comparison.
 * Compares two horses across adjusted times, speed ratings, surface affinity, and gallops.
 */

class H2HComparator {
  constructor(modalId, bodyId) {
    this.modal = document.getElementById(modalId);
    this.body = document.getElementById(bodyId);
    this.runners = [];
  }

  open(runners, horse1Number, horse2Number) {
    this.runners = runners || [];
    if (!this.modal || !this.body) return;

    const h1 = this.runners.find(r => r.number === horse1Number) || this.runners[0];
    const h2 = this.runners.find(r => r.number === horse2Number) || this.runners[1] || this.runners[0];

    this.render(h1, h2);
    this.modal.classList.add('open');
  }

  close() {
    if (this.modal) this.modal.classList.remove('open');
  }

  render(h1, h2) {
    if (!h1 || !h2) return;

    const t1 = h1.time_analysis || {};
    const t2 = h2.time_analysis || {};
    const g1 = h1.gallop_analysis || {};
    const g2 = h2.gallop_analysis || {};
    const s1 = h1.surface_affinity || {};
    const s2 = h2.surface_affinity || {};

    const h1Advantage = h1.composite_rating > h2.composite_rating;
    const diffTime = Math.abs((t1.adjusted_time_sec || 0) - (t2.adjusted_time_sec || 0)).toFixed(2);

    this.body.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem;">
        <select id="h2hSelect1" style="background:#1e293b; color:#fff; border:1px solid rgba(255,255,255,0.1); padding:0.5rem; border-radius:6px; font-weight:600; font-size:0.9rem;"
                onchange="window.h2hApp.onChangeSelection()">
          ${this.runners.map(r => `<option value="${r.number}" ${r.number === h1.number ? 'selected' : ''}>#${r.number} ${r.name} (${r.win_probability}%)</option>`).join('')}
        </select>

        <span style="font-weight:800; font-size:1.1rem; color:var(--gold-400); padding:0 0.5rem;">VS</span>

        <select id="h2hSelect2" style="background:#1e293b; color:#fff; border:1px solid rgba(255,255,255,0.1); padding:0.5rem; border-radius:6px; font-weight:600; font-size:0.9rem;"
                onchange="window.h2hApp.onChangeSelection()">
          ${this.runners.map(r => `<option value="${r.number}" ${r.number === h2.number ? 'selected' : ''}>#${r.number} ${r.name} (${r.win_probability}%)</option>`).join('')}
        </select>
      </div>

      <!-- Verdict Banner -->
      <div style="background:linear-gradient(135deg, rgba(16,185,129,0.15), rgba(6,95,70,0.25)); border:1px solid var(--emerald-400); border-radius:10px; padding:1rem; margin-bottom:1.25rem; font-size:0.86rem; line-height:1.4;">
        🏆 <strong>AI Karşılaştırma Kararı:</strong> 
        <span style="color:var(--emerald-400); font-weight:700;">#${h1Advantage ? h1.number : h2.number} ${h1Advantage ? h1.name : h2.name}</span>,
        rakibine göre düzeltilmiş derecede <strong style="color:#fff;">${diffTime} saniye</strong> ve hız endeksinde 
        <strong style="color:#fff;">${Math.abs(t1.speed_figure - t2.speed_figure).toFixed(1)} puan</strong> avantaj sağlayarak bu eşleşmede önde görünüyor.
      </div>

      <!-- Comparison Metrics Table -->
      <table style="width:100%; border-collapse:collapse; font-size:0.85rem; text-align:center;">
        <thead>
          <tr style="border-bottom:1px solid rgba(255,255,255,0.1); color:var(--text-muted);">
            <th style="padding:0.6rem; text-align:left;">#${h1.number} ${h1.name.split(' ')[0]}</th>
            <th style="padding:0.6rem;">Ölçüt</th>
            <th style="padding:0.6rem; text-align:right;">#${h2.number} ${h2.name.split(' ')[0]}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:0.75rem; text-align:left; font-weight:700; color:${t1.adjusted_time_sec <= t2.adjusted_time_sec ? 'var(--emerald-400)' : 'var(--text-main)'};">
              ${t1.adjusted_time_str || '-'}
            </td>
            <td style="color:var(--text-secondary); font-size:0.78rem;">Düzeltilmiş Derece</td>
            <td style="padding:0.75rem; text-align:right; font-weight:700; color:${t2.adjusted_time_sec <= t1.adjusted_time_sec ? 'var(--emerald-400)' : 'var(--text-main)'};">
              ${t2.adjusted_time_str || '-'}
            </td>
          </tr>
          <tr>
            <td style="padding:0.75rem; text-align:left; font-weight:700; color:${t1.speed_figure >= t2.speed_figure ? 'var(--emerald-400)' : 'var(--text-main)'};">
              ${t1.speed_figure}
            </td>
            <td style="color:var(--text-secondary); font-size:0.78rem;">Hız Endeksi (Beyer)</td>
            <td style="padding:0.75rem; text-align:right; font-weight:700; color:${t2.speed_figure >= t1.speed_figure ? 'var(--emerald-400)' : 'var(--text-main)'};">
              ${t2.speed_figure}
            </td>
          </tr>
          <tr>
            <td style="padding:0.75rem; text-align:left; font-weight:700; color:${s1.score >= s2.score ? 'var(--emerald-400)' : 'var(--text-main)'};">
              %${s1.score}
            </td>
            <td style="color:var(--text-secondary); font-size:0.78rem;">Pist Uyumu</td>
            <td style="padding:0.75rem; text-align:right; font-weight:700; color:${s2.score >= s1.score ? 'var(--emerald-400)' : 'var(--text-main)'};">
              %${s2.score}
            </td>
          </tr>
          <tr>
            <td style="padding:0.75rem; text-align:left; font-weight:700;">
              ${g1.mean_400_pace}s <small style="display:block; font-size:0.7rem; color:${g1.is_consistent ? 'var(--emerald-400)' : 'var(--gold-400)'};">${g1.status_badge}</small>
            </td>
            <td style="color:var(--text-secondary); font-size:0.78rem;">Galop 400m Temposu</td>
            <td style="padding:0.75rem; text-align:right; font-weight:700;">
              ${g2.mean_400_pace}s <small style="display:block; font-size:0.7rem; color:${g2.is_consistent ? 'var(--emerald-400)' : 'var(--gold-400)'};">${g2.status_badge}</small>
            </td>
          </tr>
          <tr>
            <td style="padding:0.75rem; text-align:left; font-weight:600;">${h1.weight} kg</td>
            <td style="color:var(--text-secondary); font-size:0.78rem;">Taşınan Sıklet</td>
            <td style="padding:0.75rem; text-align:right; font-weight:600;">${h2.weight} kg</td>
          </tr>
          <tr>
            <td style="padding:0.75rem; text-align:left; font-weight:600;">${h1.jockey}</td>
            <td style="color:var(--text-secondary); font-size:0.78rem;">Jokey</td>
            <td style="padding:0.75rem; text-align:right; font-weight:600;">${h2.jockey}</td>
          </tr>
          <tr>
            <td style="padding:0.75rem; text-align:left; font-weight:800; color:var(--emerald-400); font-size:1.1rem;">
              %${h1.win_probability}
            </td>
            <td style="color:var(--text-secondary); font-size:0.78rem;">Model Kazanma İhtimali</td>
            <td style="padding:0.75rem; text-align:right; font-weight:800; color:var(--emerald-400); font-size:1.1rem;">
              %${h2.win_probability}
            </td>
          </tr>
        </tbody>
      </table>
    `;
  }

  onChangeSelection() {
    const s1 = parseInt(document.getElementById('h2hSelect1')?.value || 1);
    const s2 = parseInt(document.getElementById('h2hSelect2')?.value || 2);
    const h1 = this.runners.find(r => r.number === s1);
    const h2 = this.runners.find(r => r.number === s2);
    this.render(h1, h2);
  }
}

window.H2HComparator = H2HComparator;
