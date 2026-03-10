import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. SETTINGS & DARK UI ---
st.set_page_config(page_title="Swiss Investor Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    
    /* Metrik Boxen */
    div[data-testid="stMetric"] {
        background-color: #1c2128;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }
    div[data-testid="stMetricValue"] > div { color: #58a6ff !important; font-family: 'JetBrains Mono', monospace; }
    div[data-testid="stMetricLabel"] > div > p { color: #8b949e !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=3600)
def get_cached_data(tickers, years):
    period = f"{years}y"
    all_tickers = list(set(tickers + ["CHF=X", "EURCHF=X"]))
    try:
        data = yf.download(all_tickers, period=period)['Close']
        return data
    except Exception:
        return pd.DataFrame()

# --- 3. SIDEBAR: STRATEGIE-PANEL ---
with st.sidebar:
    st.title("🛡️ Strategie-Zentrale")
    lookback = st.select_slider("Analyse-Zeitraum (Jahre)", options=[1, 5, 10, 15, 20], value=10)
    
    st.divider()
    st.subheader("🏦 Zins-Dashboard (März 2026)")
    snb_rate = st.number_input("SNB (CH) %", value=0.00, step=0.25)
    fed_rate = st.number_input("Fed (USA) %", value=3.75, step=0.25)
    ecb_rate = st.number_input("EZB (EU) %", value=2.00, step=0.25)
    bank_fee = st.slider("Bank-Marge %", 0.0, 0.50, 0.15, 0.05)
    
    # Zentrale Definition der Hedging-Kosten
    usd_hedge_total = (fed_rate - snb_rate) + bank_fee
    eur_hedge_total = (ecb_rate - snb_rate) + bank_fee
    total_hedge_cost = usd_hedge_total  # Standardwert für den Rechner

    st.divider()
    st.subheader("📈 Assets")
    ticker_input = st.text_input("Ticker Symbole (Yahoo)", value="CSSP.SW, SWDA.SW, EIMI.SW, IWDC.SW, IUSE.SW")
    user_tickers = [t.strip() for t in ticker_input.split(",")]

# --- 4. HAUPTBEREICH: PERFORMANCE ANALYSE ---
st.title("Swiss Investor Intelligence Pro")
st.caption("Fokus: Vermögensaufbau für Einwohner der Schweiz (CHF)")

# --- START TRY BLOCK ---
try:
    df = get_cached_data(user_tickers, lookback)
    
    if df.empty:
        st.error("Warte auf Daten von Yahoo Finance...")
    else:
        # Metriken Zeile
        m1, m2, m3, m4 = st.columns(4)
        
        # USD Metrik
        usd_pct = 0.0
        if "CHF=X" in df.columns:
            usd_s = df["CHF=X"].dropna()
            if not usd_s.empty:
                usd_now = usd_s.iloc[-1]
                usd_pct = (usd_now / usd_s.iloc[0] - 1) * 100
                m1.metric("USD / CHF", f"{usd_now:.3f}", f"{usd_pct:.1f}%", delta_color="inverse")
        
        # EUR Metrik
        if "EURCHF=X" in df.columns:
            eur_s = df["EURCHF=X"].dropna()
            if not eur_s.empty:
                eur_now = eur_s.iloc[-1]
                eur_pct = (eur_now / eur_s.iloc[0] - 1) * 100
                m2.metric("EUR / CHF", f"{eur_now:.3f}", f"{eur_pct:.1f}%", delta_color="inverse")
        
        m3.metric("Hedge Kosten USD", f"{usd_hedge_total:.2f}%", "p.a.")
        m4.metric("Hedge Kosten EUR", f"{eur_hedge_total:.2f}%", "p.a.")

        st.divider()

        # Charts Bereich
        col_chart, col_fact = st.columns([2, 1])

        with col_chart:
            st.subheader("Aktien-Performance (Normiert auf 100)")
            valid_stocks = [t for t in user_tickers if t in df.columns and not df[t].dropna().empty]
            if valid_stocks:
                stock_data = df[valid_stocks].dropna()
                stock_norm = (stock_data / stock_data.iloc[0]) * 100
                st.line_chart(stock_norm)
            
            st.subheader("Währungs-Entwertung (Kaufkraft)")
            curr_cols = [c for c in ["CHF=X", "EURCHF=X"] if c in df.columns]
            if curr_cols:
                curr_data = df[curr_cols].dropna()
                curr_norm = (curr_data / curr_data.iloc[0]) * 100
                st.line_chart(curr_norm)

        with col_fact:
            st.subheader("🎯 Strategie-Check")
            if "CHF=X" in df.columns:
                annual_usd_drag = abs(usd_pct) / lookback
                st.write(f"**USD Verlust:** {annual_usd_drag:.2f}% p.a.")
                st.write(f"**Hedge Kosten:** {usd_hedge_total:.2f}% p.a.")
                
                if usd_hedge_total > annual_usd_drag:
                    st.error("Urteil: UNHEDGED ist besser. Kosten fressen Vorteil.")
                else:
                    st.success("Urteil: HEDGING lohnt sich.")

        # --- 5. ANLAGERECHNER (INHALT DES TRY BLOCKS) ---
        st.divider()
        st.header("Anlagerechner")
        st.markdown("Kalkulation nach Abzug von Inflation und Strategiekosten.")

        c1, c2 = st.columns(2)
        with c1:
            start_cap = st.number_input("Startkapital (CHF)", value=13000, step=1000)
            monthly = st.number_input("Monatliche Sparrate (CHF)", value=3000, step=100)
            years = st.number_input("Anlagezeitraum (Jahre)", value=20, step=1)
            ret_exp = st.slider("Erwartete Markt-Rendite %", 0.0, 12.0, 7.0, 0.5)
            inflation = st.slider("Geschätzte Inflation %", 0.0, 5.0, 1.2, 0.1)

        # Netto-Kalkulation
        net_ret = ret_exp - total_hedge_cost
        total_months = years * 12

        if net_ret == 0:
            fv = start_cap + (monthly * total_months)
        else:
            r = (1 + (net_ret/100))**(1/12) - 1
            fv = start_cap * (1+r)**total_months + monthly * (((1+r)**total_months - 1) / r)

        real_fv = fv / (1 + (inflation/100))**years

        with c2:
            st.metric("Endvermögen", f"CHF {fv:,.0f}")
            st.metric("Reale Kaufkraft", f"CHF {real_fv:,.0f}")
            st.write(f"**Eingezahlt:** CHF {start_cap + (monthly*total_months):,.0f}")
            st.caption(f"Basis: {net_ret:.2f}% Netto-Rendite.")

            history = [start_cap]
            curr_v = start_cap
            for _ in range(years):
                curr_v = curr_v * (1 + net_ret/100) + (monthly * 12)
                history.append(curr_v)
            st.area_chart(history)

# --- END TRY BLOCK ---
except Exception as e:
    st.error(f"Daten-Fehler: {e}")

st.divider()
st.caption("Swiss Investor Intelligence | Version 2026.1 | Keine Anlageberatung.")