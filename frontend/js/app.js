let debounceTimer = null;

async function fetchMarketData() {
  const tickers = document.getElementById("ticker-input").value;
  const years = document.getElementById("lookback").value;

  showLoading("stock-chart-box");
  showLoading("currency-chart-box");

  try {
    const resp = await fetch(`/api/market-data?tickers=${encodeURIComponent(tickers)}&years=${years}`);
    const data = await resp.json();

    // Render stock chart
    if (Object.keys(data.stocks).length > 0) {
      hideLoading("stock-chart-box");
      renderStockChart(data.stocks);
    }

    // Render currency chart + metrics
    if (Object.keys(data.currencies).length > 0) {
      hideLoading("currency-chart-box");
      renderCurrencyChart(data.currencies);
      updateCurrencyMetrics(data.currencies, data.years);
    }

    updateStrategy(data.currencies, data.years);
  } catch (err) {
    console.error("Fetch error:", err);
    hideLoading("stock-chart-box");
    hideLoading("currency-chart-box");
  }
}

function updateCurrencyMetrics(currencies, years) {
  const usd = currencies["CHF=X"];
  if (usd) {
    document.getElementById("metric-usd-val").textContent = usd.current.toFixed(3);
    const el = document.getElementById("metric-usd-delta");
    el.textContent = `${usd.pct_change > 0 ? "+" : ""}${usd.pct_change.toFixed(1)}%`;
    // Inverse: CHF strengthening (negative USD) is good for Swiss investor
    el.className = `delta ${usd.pct_change <= 0 ? "positive" : "negative"}`;
  }

  const eur = currencies["EURCHF=X"];
  if (eur) {
    document.getElementById("metric-eur-val").textContent = eur.current.toFixed(3);
    const el = document.getElementById("metric-eur-delta");
    el.textContent = `${eur.pct_change > 0 ? "+" : ""}${eur.pct_change.toFixed(1)}%`;
    el.className = `delta ${eur.pct_change <= 0 ? "positive" : "negative"}`;
  }
}

function updateHedgeCosts() {
  const snb = parseFloat(document.getElementById("snb-rate").value) || 0;
  const fed = parseFloat(document.getElementById("fed-rate").value) || 0;
  const ecb = parseFloat(document.getElementById("ecb-rate").value) || 0;
  const bankFee = parseFloat(document.getElementById("bank-margin").value) || 0;

  const usdHedge = (fed - snb) + bankFee;
  const eurHedge = (ecb - snb) + bankFee;

  document.getElementById("metric-hedge-usd-val").textContent = `${usdHedge.toFixed(2)}%`;
  document.getElementById("metric-hedge-eur-val").textContent = `${eurHedge.toFixed(2)}%`;

  document.getElementById("margin-val").textContent = `${bankFee.toFixed(2)}%`;

  return { usdHedge, eurHedge };
}

function updateStrategy(currencies, years) {
  const { usdHedge } = updateHedgeCosts();
  const usd = currencies?.["CHF=X"];
  const box = document.getElementById("verdict");

  if (!usd) {
    box.textContent = "Keine USD-Daten verfügbar.";
    box.className = "verdict-box";
    return;
  }

  const annualDrag = Math.abs(usd.pct_change) / years;

  document.getElementById("strategy-drag").textContent = `USD Verlust: ${annualDrag.toFixed(2)}% p.a.`;
  document.getElementById("strategy-cost").textContent = `Hedge Kosten: ${usdHedge.toFixed(2)}% p.a.`;

  if (usdHedge > annualDrag) {
    box.textContent = "Urteil: UNHEDGED ist besser. Kosten fressen Vorteil.";
    box.className = "verdict-box error";
  } else {
    box.textContent = "Urteil: HEDGING lohnt sich.";
    box.className = "verdict-box success";
  }
}

function showLoading(containerId) {
  const el = document.getElementById(containerId);
  if (!el.querySelector(".loading")) {
    const loader = document.createElement("div");
    loader.className = "loading";
    loader.innerHTML = '<div class="spinner"></div> Lade Daten...';
    el.appendChild(loader);
  }
}

function hideLoading(containerId) {
  const el = document.getElementById(containerId);
  const loader = el.querySelector(".loading");
  if (loader) loader.remove();
}

function debouncedFetch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fetchMarketData, 500);
}

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  // Rate input listeners
  ["snb-rate", "fed-rate", "ecb-rate", "bank-margin"].forEach((id) => {
    document.getElementById(id).addEventListener("input", () => {
      updateHedgeCosts();
      if (typeof calculateAndRender === "function") calculateAndRender();
    });
  });

  // Ticker + lookback listeners
  document.getElementById("ticker-input").addEventListener("input", debouncedFetch);
  document.getElementById("lookback").addEventListener("change", debouncedFetch);

  // Initial load
  updateHedgeCosts();
  fetchMarketData();
  initCalculator();
});
