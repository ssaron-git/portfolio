const CHART_COLORS = [
  "#58a6ff", "#3fb950", "#d29922", "#f778ba", "#bc8cff",
  "#ff7b72", "#79c0ff", "#7ee787",
];

const CHART_DEFAULTS = {
  responsive: true,
  plugins: {
    legend: {
      labels: { color: "#c9d1d9", font: { size: 12 } },
    },
  },
  scales: {
    x: {
      ticks: { color: "#8b949e", maxTicksLimit: 8 },
      grid: { color: "#30363d" },
    },
    y: {
      ticks: { color: "#8b949e" },
      grid: { color: "#30363d" },
    },
  },
};

let stockChart = null;
let currencyChart = null;

function renderStockChart(stocksData) {
  const ctx = document.getElementById("stock-chart").getContext("2d");
  if (stockChart) stockChart.destroy();

  const datasets = [];
  let i = 0;
  for (const [ticker, data] of Object.entries(stocksData)) {
    // Downsample for performance: show ~200 points max
    const step = Math.max(1, Math.floor(data.dates.length / 200));
    const dates = data.dates.filter((_, idx) => idx % step === 0);
    const prices = data.prices.filter((_, idx) => idx % step === 0);

    datasets.push({
      label: ticker,
      data: prices,
      borderColor: CHART_COLORS[i % CHART_COLORS.length],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.2,
      fill: false,
    });
    i++;
  }

  // Use dates from the first ticker for labels
  const firstTicker = Object.values(stocksData)[0];
  const step = Math.max(1, Math.floor(firstTicker.dates.length / 200));
  const labels = firstTicker.dates.filter((_, idx) => idx % step === 0);

  stockChart = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: CHART_DEFAULTS,
  });
}

function renderCurrencyChart(currencyData) {
  const ctx = document.getElementById("currency-chart").getContext("2d");
  if (currencyChart) currencyChart.destroy();

  const datasets = [];
  let i = 0;
  const nameMap = { "CHF=X": "USD/CHF", "EURCHF=X": "EUR/CHF" };

  for (const [symbol, data] of Object.entries(currencyData)) {
    const step = Math.max(1, Math.floor(data.dates.length / 200));
    datasets.push({
      label: nameMap[symbol] || symbol,
      data: data.prices.filter((_, idx) => idx % step === 0),
      borderColor: CHART_COLORS[i % CHART_COLORS.length],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.2,
      fill: false,
    });
    i++;
  }

  const firstCurr = Object.values(currencyData)[0];
  const step = Math.max(1, Math.floor(firstCurr.dates.length / 200));
  const labels = firstCurr.dates.filter((_, idx) => idx % step === 0);

  currencyChart = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: CHART_DEFAULTS,
  });
}
