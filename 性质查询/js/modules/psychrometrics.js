// js/modules/psychrometrics.js
export function init(container) {
  container.innerHTML = `
    <div class="module-container">
      <h2>焓湿图参数计算</h2>

      <div class="form-row">
        <label>干球温度 (℃):
          <input type="number" id="dryTemp" required step="0.1">
        </label>
        <label>相对湿度 (%):
          <input type="number" id="relHumidity" required step="0.1">
        </label>
      </div>

      <div class="form-actions">
        <button type="button" id="calcBtn">计算</button>
      </div>

      <table id="result-table">
        <thead>
          <tr><th>参数</th><th>数值</th></tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  `;

  const btn = container.querySelector('#calcBtn');
  const tbody = container.querySelector('#result-table tbody');

  const labels = [
    '环境压力 (kPa)',
    '含湿量 (g/kg)',
    '湿球温度 (℃)',
    '露点温度 (℃)',
    '饱和温度 (℃)',
    '焓 (kJ/kg)',
    '蒸汽压力 (kPa)',
    '比热 [kJ/(kg·K)]',
    '比容 (m³/kg)',
    '密度 (kg/m³)'
  ];

  btn.addEventListener('click', () => {
    const T_db = parseFloat(container.querySelector('#dryTemp').value);
    const RH   = parseFloat(container.querySelector('#relHumidity').value);

    if (isNaN(T_db) || T_db < -50 || T_db > 100) {
      return alert('干球温度需在 -50 ~ 100℃ 之间');
    }
    if (isNaN(RH)   || RH   < 0   || RH   > 100) {
      return alert('相对湿度需在 0 ~ 100% 之间');
    }

    // 计算
    const P = 101325;
    const rh = RH / 100;
    const Psat = 610.78 * Math.exp(T_db / (T_db + 238.3) * 17.2694);
    const Pv = rh * Psat;
    const W = 0.622 * Pv / (P - Pv);
    const h = 1.006 * T_db + W * (2501 + 1.86 * T_db);
    const T_wb = T_db - (1 - rh) * 5;
    const T_dp = T_db - (1 - rh) * 10;
    const v = 0.287 * (T_db + 273.15) * (1 + 1.6078 * W) / P;
    const rho = 1 / v;
    const cp = 1.006 + 1.86 * W;

    const values = [
      (P/1000).toFixed(3),
      (W*1000).toFixed(4),
      T_wb.toFixed(2),
      T_dp.toFixed(2),
      '100.00',
      h.toFixed(2),
      (Pv/1000).toFixed(3),
      cp.toFixed(4),
      v.toFixed(4),
      rho.toFixed(4)
    ];

    // 渲染结果表
    tbody.innerHTML = labels.map((lab, i) =>
      `<tr><td>${lab}</td><td>${values[i]}</td></tr>`
    ).join('');
  });
}
