let calcChart = null;

function calculateAndRender() {
  const startCap = parseFloat(document.getElementById("calc-start").value) || 0;
  const monthly = parseFloat(document.getElementById("calc-monthly").value) || 0;
  const years = parseInt(document.getElementById("calc-years").value) || 0;
  const retExp = parseFloat(document.getElementById("calc-return").value) || 0;
  const inflation = parseFloat(document.getElementById("calc-inflation").value) || 0;

  // Get hedge cost from sidebar
  const snb = parseFloat(document.getElementById("snb-rate").value) || 0;
  const fed = parseFloat(document.getElementById("fed-rate").value) || 0;
  const bankFee = parseFloat(document.getElementById("bank-margin").value) || 0;
  const hedgeCost = (fed - snb) + bankFee;

  const netRet = retExp - hedgeCost;
  const totalMonths = years * 12;

  let fv;
  if (netRet === 0) {
    fv = startCap + monthly * totalMonths;
  } else {
    const r = Math.pow(1 + netRet / 100, 1 / 12) - 1;
    fv = startCap * Math.pow(1 + r, totalMonths) + monthly * ((Math.pow(1 + r, totalMonths) - 1) / r);
  }

  const realFv = fv / Math.pow(1 + inflation / 100, years);
  const totalInvested = startCap + monthly * totalMonths;

  // Update result display
  document.getElementById("result-fv").textContent = `CHF ${Math.round(fv).toLocaleString("de-CH")}`;
  document.getElementById("result-real").textContent = `CHF ${Math.round(realFv).toLocaleString("de-CH")}`;
  document.getElementById("result-invested").textContent = `Eingezahlt: CHF ${Math.round(totalInvested).toLocaleString("de-CH")}`;
  document.getElementById("result-basis").textContent = `Basis: ${netRet.toFixed(2)}% Netto-Rendite`;

  // Build growth history
  const labels = [];
  const data = [];
  let curr = startCap;
  const r = netRet === 0 ? 0 : Math.pow(1 + netRet / 100, 1 / 12) - 1;
  labels.push("Jahr 0");
  data.push(Math.round(curr));
  for (let i = 1; i <= years; i++) {
    curr = r === 0
      ? curr + monthly * 12
      : curr * Math.pow(1 + r, 12) + monthly * ((Math.pow(1 + r, 12) - 1) / r);
    labels.push(`Jahr ${i}`);
    data.push(Math.round(curr));
  }

  renderCalcChart(labels, data);
}

function renderCalcChart(labels, data) {
  const ctx = document.getElementById("calc-chart").getContext("2d");

  if (calcChart) calcChart.destroy();

  calcChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Vermögen (CHF)",
        data,
        fill: true,
        backgroundColor: "rgba(88, 166, 255, 0.15)",
        borderColor: "#58a6ff",
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `CHF ${ctx.parsed.y.toLocaleString("de-CH")}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: "#8b949e" }, grid: { color: "#30363d" } },
        y: {
          ticks: {
            color: "#8b949e",
            callback: (v) => `${(v / 1000).toFixed(0)}k`,
          },
          grid: { color: "#30363d" },
        },
      },
    },
  });
}

function initCalculator() {
  const ids = ["calc-start", "calc-monthly", "calc-years", "calc-return", "calc-inflation"];
  ids.forEach((id) => {
    document.getElementById(id).addEventListener("input", calculateAndRender);
  });

  // Also recalculate when sidebar rate inputs change
  ["snb-rate", "fed-rate", "bank-margin"].forEach((id) => {
    document.getElementById(id).addEventListener("input", calculateAndRender);
  });

  // Show slider values
  document.getElementById("calc-return").addEventListener("input", (e) => {
    document.getElementById("calc-return-val").textContent = `${parseFloat(e.target.value).toFixed(1)}%`;
  });
  document.getElementById("calc-inflation").addEventListener("input", (e) => {
    document.getElementById("calc-inflation-val").textContent = `${parseFloat(e.target.value).toFixed(1)}%`;
  });

  calculateAndRender();
}
