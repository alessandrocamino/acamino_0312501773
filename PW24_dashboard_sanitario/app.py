import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "monitoraggio_panflu_demo.csv"
DEMAND_FILE = ROOT / "data" / "domanda_storica.csv"
PARAMS_FILE = ROOT / "data" / "parametri_scorte.csv"
MONTH_NAMES = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

st.set_page_config(page_title="PW24 | Monitoraggio delle scorte pandemiche", page_icon="📦", layout="wide")
st.title("Monitoraggio delle scorte pandemiche")
st.caption("PW 24 · Pegaso L-31 · Sviluppo di una mini-dashboard Python per la previsione della domanda e la pianificazione delle scorte")
st.warning(
    "Prototipo didattico: tutti gli enti, i consumi, le giacenze, le quantità minime e le scorte scadute "
    "sono simulati. Non rappresentano dati reali di Regione Lombardia, ARIA, AREU o di enti sanitari."
)

# ---------------------------------------------------------------- validazione dei file CSV
def fail(msg):
    # Mostra un errore guidato in italiano e interrompe l'esecuzione dello script.
    st.error(msg)
    st.stop()

def first_rows(df, mask, col, limit=3):
    # Descrive le prime righe incriminate (numero di riga nel file, intestazione = riga 1).
    bad = df.loc[mask, col].head(limit)
    return "; ".join(f"riga {i + 2}: '{v}'" for i, v in bad.items())

def read_csv_checked(path, required):
    name = f"data/{path.name}"
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except FileNotFoundError:
        fail(f"File mancante: {name}. Verificare che sia nella cartella data/ dell'applicazione.")
    except pd.errors.EmptyDataError:
        fail(f"Il file {name} è vuoto: manca anche l'intestazione.")
    except (pd.errors.ParserError, UnicodeDecodeError):
        fail(f"Il file {name} non è leggibile come CSV in formato UTF-8.")
    missing = [c for c in required if c not in df.columns]
    if missing:
        fail(f"Colonne mancanti in {name}: {', '.join(missing)} (colonne attese: {', '.join(required)}).")
    if df.empty:
        fail(f"Il file {name} non contiene righe di dati (solo intestazione).")
    return df

def check_text(df, col, name):
    empty = df[col].isna() | (df[col].astype(str).str.strip() == "")
    if empty.any():
        fail(f"Valori mancanti nella colonna '{col}' di {name} ({first_rows(df, empty, col)}).")

def check_numeric(df, col, name, low=0.0, strict=False, high=None):
    vals = pd.to_numeric(df[col], errors="coerce")
    bad = ~np.isfinite(vals)
    if bad.any():
        fail(f"Valori non numerici o mancanti nella colonna '{col}' di {name} ({first_rows(df, bad, col)}).")
    out_low = vals <= low if strict else vals < low
    if out_low.any():
        cond = f"maggiore di {low:g}" if strict else f"maggiore o uguale a {low:g}"
        fail(f"Valori non validi nella colonna '{col}' di {name}: devono essere {cond} ({first_rows(df, out_low, col)}).")
    if high is not None and (vals >= high).any():
        fail(f"Valori non validi nella colonna '{col}' di {name}: devono essere minori di {high:g} ({first_rows(df, vals >= high, col)}).")
    df[col] = vals

def check_duplicates(df, keys, name):
    dup = df.duplicated(keys, keep=False)
    if dup.any():
        first = df.loc[dup, keys].iloc[0].astype(str).tolist()
        fail(f"Righe duplicate in {name} sulla chiave ({', '.join(keys)}): ad esempio {', '.join(first)}.")

def load_monitoring(path):
    name = f"data/{path.name}"
    num_cols = ["consumo_mensile_pezzi", "quantita_minima_richiesta", "giacenza_pezzi", "scorte_scadute_pezzi"]
    df = read_csv_checked(path, ["id_ente", "categoria_panflu", "mese_riferimento"] + num_cols)
    check_text(df, "id_ente", name)
    check_text(df, "categoria_panflu", name)
    check_text(df, "mese_riferimento", name)
    for col in num_cols:
        check_numeric(df, col, name)
    months = df["mese_riferimento"].astype(str).str.strip()
    parsed = pd.to_datetime(months + "-01", format="%Y-%m-%d", errors="coerce")
    bad = ~months.str.fullmatch(r"\d{4}-\d{2}") | parsed.isna()
    if bad.any():
        fail(f"Mese non valido nella colonna 'mese_riferimento' di {name}: atteso formato AAAA-MM con mese da 01 a 12 ({first_rows(df, bad, 'mese_riferimento')}).")
    df["mese_riferimento"] = parsed
    check_duplicates(df, ["id_ente", "categoria_panflu", "mese_riferimento"], name)
    return df

def load_demand(path):
    name = f"data/{path.name}"
    df = read_csv_checked(path, ["data", "articolo", "domanda"])
    check_text(df, "articolo", name)
    check_text(df, "data", name)
    check_numeric(df, "domanda", name)
    parsed = pd.to_datetime(df["data"].astype(str).str.strip(), format="%Y-%m-%d", errors="coerce")
    if parsed.isna().any():
        fail(f"Data non valida nella colonna 'data' di {name}: atteso formato AAAA-MM-GG ({first_rows(df, parsed.isna(), 'data')}).")
    df["data"] = parsed.dt.to_period("M").dt.to_timestamp()
    check_duplicates(df, ["articolo", "data"], name)
    df = df.sort_values(["articolo", "data"]).reset_index(drop=True)
    for art, grp in df.groupby("articolo"):
        if len(grp) < 12:
            fail(f"L'articolo '{art}' in {name} ha solo {len(grp)} mesi di storico: ne servono almeno 12.")
        steps = grp["data"].dt.year * 12 + grp["data"].dt.month
        gaps = steps.diff().dropna()
        if (gaps != 1).any():
            hole = grp["data"].loc[gaps[gaps != 1].index[0]].strftime("%Y-%m")
            fail(f"Serie storica non continua per l'articolo '{art}' in {name}: manca almeno un mese prima di {hole}.")
    return df

def load_params(path, articles):
    name = f"data/{path.name}"
    df = read_csv_checked(path, ["articolo", "scorta_attuale", "costo_unitario_eur", "lead_time_giorni",
                                 "livello_servizio", "periodo_riordino_giorni", "mesi_stagionali"])
    check_text(df, "articolo", name)
    check_duplicates(df, ["articolo"], name)
    check_numeric(df, "scorta_attuale", name)
    check_numeric(df, "costo_unitario_eur", name)
    check_numeric(df, "lead_time_giorni", name, strict=True)
    check_numeric(df, "livello_servizio", name, low=0.0, strict=True, high=1.0)
    check_numeric(df, "periodo_riordino_giorni", name, strict=True)
    check_numeric(df, "mesi_stagionali", name)
    missing = sorted(set(articles) - set(df["articolo"]))
    extra = sorted(set(df["articolo"]) - set(articles))
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"articoli senza parametri: {', '.join(missing)}")
        if extra:
            parts.append(f"articoli senza storico di domanda: {', '.join(extra)}")
        fail(f"Gli articoli di data/domanda_storica.csv e {name} non coincidono ({'; '.join(parts)}).")
    return df.set_index("articolo")

data = load_monitoring(DATA_FILE)
demand = load_demand(DEMAND_FILE)
ARTICLES = sorted(demand["articolo"].unique())
params = load_params(PARAMS_FILE, ARTICLES)
CATEGORIES = sorted(data["categoria_panflu"].unique())
MONTHS = sorted(data["mese_riferimento"].unique())
LATEST = max(MONTHS)

# ---------------------------------------------------------------- funzioni di calcolo
def moving_average_forecast(series, horizon=3, window=3):
    vals = list(np.asarray(series, dtype=float))
    out = []
    for _ in range(horizon):
        value = float(np.mean(vals[-window:])) if vals else 0.0
        out.append(max(0.0, value))
        vals.append(value)
    return np.asarray(out)

def linear_forecast(series, horizon=3):
    y = np.asarray(series, dtype=float)
    if len(y) < 2:
        return np.repeat(float(y[-1]) if len(y) else 0.0, horizon)
    x = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    xf = np.arange(len(y), len(y) + horizon, dtype=float)
    return np.maximum(0, slope * xf + intercept)

def error_metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mae = float(np.mean(np.abs(actual - predicted)))
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    nonzero = actual != 0
    mape = float(np.mean(np.abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])) * 100) if nonzero.any() else np.nan
    return {"MAE": mae, "RMSE": rmse, "MAPE (%)": mape}

def seasonal_indices(values, month_nums):
    # Indici mensili moltiplicativi: rapporto al trend lineare, media per mese di calendario, media 1.
    y = np.asarray(values, dtype=float)
    m = np.asarray(month_nums, dtype=int)
    if len(y) < 12:
        return np.ones(12)
    x = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    fit = slope * x + intercept
    ok = fit > 0
    ratio = np.where(ok, y / np.where(ok, fit, 1.0), np.nan)
    raw = np.ones(12)
    for k in range(1, 13):
        sel = (m == k) & np.isfinite(ratio)
        if sel.any():
            raw[k - 1] = ratio[sel].mean()
    return raw / raw.mean()

def seasonal_factor(indices, month_nums, intensity):
    # Con intensità 0 il fattore è esattamente 1,0 (stagionalità neutra).
    s = min(1.0, max(0.0, float(intensity)))
    return 1.0 + s * (np.asarray(indices, dtype=float)[np.asarray(month_nums, dtype=int) - 1] - 1.0)

def trend_series(y, trend_pct):
    # Rampa lineare: il primo mese non cambia, l'ultimo varia della percentuale piena.
    y = np.asarray(y, dtype=float)
    idx = np.arange(len(y))
    return np.maximum(0, y * (1 + (trend_pct / 100) * (idx / max(1, len(idx) - 1))))

def z_score(level):
    z = {0.90: 1.282, 0.95: 1.645, 0.975: 1.960, 0.99: 2.326}
    if level in z:
        return z[level]
    from statistics import NormalDist
    return NormalDist().inv_cdf(level)

def forecast_experiment(y, month_nums, future_month_nums, horizon, window,
                        variability, trend_pct, intensity, indices):
    # Domanda di scenario = serie con trend e variabilità, moltiplicata per il fattore stagionale del mese.
    # I metodi di previsione lavorano sulla serie senza stagionalità; il fattore del mese target si applica dopo.
    y_tr = trend_series(y, trend_pct)
    smooth = pd.Series(y_tr).rolling(3, min_periods=1).mean().to_numpy()
    y_var = np.maximum(0, smooth + (y_tr - smooth) * variability)
    f_hist = seasonal_factor(indices, month_nums, intensity)
    y_scen = y_var * f_hist
    test_n = min(4, max(2, len(y_var) // 5))
    train, test = y_var[:-test_n], y_scen[-test_n:]
    ma_test = moving_average_forecast(train, test_n, window) * f_hist[-test_n:]
    lin_test = linear_forecast(train, test_n) * f_hist[-test_n:]
    metrics = pd.DataFrame([
        {"Metodo": "Media mobile semplice", **error_metrics(test, ma_test)},
        {"Metodo": "Regressione lineare", **error_metrics(test, lin_test)}
    ])
    best = metrics.sort_values("RMSE").iloc[0]["Metodo"]
    base = moving_average_forecast(y_var, horizon, window) if best == "Media mobile semplice" else linear_forecast(y_var, horizon)
    future = base * seasonal_factor(indices, future_month_nums, intensity)
    return dict(y_scen=y_scen, metrics=metrics, best=best, future=future, test_n=test_n)

def stock_components(y, month_nums, future_month_nums, lead_days, service_level, variability,
                     horizon, window, trend_pct, intensity, indices, cycle_days=30):
    # Le componenti usano la stessa domanda di scenario (trend e stagionalità) delle previsioni.
    # La variabilità agisce solo sulla scorta di sicurezza.
    y = np.asarray(y, dtype=float)
    if len(y) == 0:
        return dict(Ciclica=0.0, Sicurezza=0.0, Anticipata=0.0, Pipeline=0.0, _daily_mean=0.0)
    y_tr = trend_series(y, trend_pct)
    ys = y_tr * seasonal_factor(indices, month_nums, intensity)
    ser = pd.Series(ys)
    daily_mean = float(ser.tail(6).mean() / 30.4375)
    daily_std = float(ser.tail(12).std(ddof=1) / 30.4375) if len(ys) > 1 else 0.0
    safety = z_score(service_level) * daily_std * variability * math.sqrt(lead_days)
    cycle = daily_mean * cycle_days / 2
    pipeline = daily_mean * lead_days
    last3 = float(ser.tail(3).mean())
    f_mean = float(np.mean(moving_average_forecast(y_tr, horizon, window)
                           * seasonal_factor(indices, future_month_nums, intensity)))
    anticipatory = max(0.0, f_mean - last3) * (lead_days / 30.4375)
    return dict(Ciclica=cycle, Sicurezza=safety, Anticipata=anticipatory, Pipeline=pipeline, _daily_mean=daily_mean)

with st.sidebar:
    st.header("Filtri di consultazione")
    selected_month = st.selectbox("Mese di riferimento", MONTHS, index=len(MONTHS)-1, format_func=lambda x: x.strftime("%Y-%m"))
    selected_entity = st.selectbox("Ente", ["Tutti"] + sorted(data["id_ente"].unique()))
    selected_category = st.selectbox("Tipologia dispositivo", ["Tutte"] + CATEGORIES)
    outcome = st.selectbox("Esito verifica", ["Tutti", "Sotto soglia", "Conforme"])
    st.divider()
    st.header("Scenario previsionale")
    horizon = st.slider("Orizzonte previsivo (mesi)", 1, 6, 3)
    window = st.slider("Finestra media mobile (mesi)", 2, 6, 3)
    variability = st.slider("Moltiplicatore variabilità", 0.5, 2.0, 1.0, 0.1)
    trend_change = st.slider("Variazione simulata della domanda (%)", -30, 30, 0, 5)
    lead_days = st.slider("Lead time ipotizzato (giorni)", 7, 120, 30, 7)
    season = st.slider(
        "Intensità stagionalità (0 = neutra)", 0.0, 1.0, 0.0, 0.1,
        help="Applica una volta in più il profilo stagionale mensile stimato dallo storico: "
             "fattore del mese = 1 + intensità × (indice stagionale − 1). Con 0 la stagionalità non modifica nulla.",
    )
    service_level = st.select_slider("Livello di servizio obiettivo", options=[0.90, 0.95, 0.975, 0.99], value=0.95)

current = data[data["mese_riferimento"] == pd.Timestamp(selected_month)].copy()
if selected_entity != "Tutti":
    current = current[current["id_ente"] == selected_entity]
if selected_category != "Tutte":
    current = current[current["categoria_panflu"] == selected_category]
current["esito"] = np.where(current["giacenza_pezzi"] >= current["quantita_minima_richiesta"], "Conforme", "Sotto soglia")
if outcome != "Tutti":
    current = current[current["esito"] == outcome]

# Top-level indicators are computed on the filtered records.
tot_stock = int(current["giacenza_pezzi"].sum())
tot_min = int(current["quantita_minima_richiesta"].sum())
tot_consumption = int(current["consumo_mensile_pezzi"].sum())
tot_expired = int(current["scorte_scadute_pezzi"].sum())
below = int((current["giacenza_pezzi"] < current["quantita_minima_richiesta"]).sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Giacenze rilevate", f"{tot_stock:,.0f} pezzi")
c2.metric("Quantità minima richiesta", f"{tot_min:,.0f} pezzi")
c3.metric("Righe sotto soglia", f"{below}")
c4.metric("Scorte scadute rilevate", f"{tot_expired:,.0f} pezzi")

tab1, tab2, tab3, tab4 = st.tabs(["Monitoraggio", "Analisi temporale e previsione", "Componenti di scorta", "Articoli e parametri"])

with tab1:
    st.subheader("Verifica delle giacenze rispetto ai quantitativi richiesti")
    if current.empty:
        st.info("Nessun record corrisponde ai filtri selezionati.")
    else:
        display = current[[
            "id_ente", "categoria_panflu", "mese_riferimento", "consumo_mensile_pezzi",
            "quantita_minima_richiesta", "giacenza_pezzi", "scorte_scadute_pezzi", "esito"
        ]].copy()
        display["mese_riferimento"] = display["mese_riferimento"].dt.strftime("%Y-%m")
        display = display.rename(columns={
            "id_ente": "Ente", "categoria_panflu": "Tipologia dispositivo",
            "mese_riferimento": "Mese/anno", "consumo_mensile_pezzi": "Consumo mensile (pezzi)",
            "quantita_minima_richiesta": "Quantità minima richiesta",
            "giacenza_pezzi": "Giacenza in magazzino", "scorte_scadute_pezzi": "Scorte scadute",
            "esito": "Esito verifica"
        })
        st.dataframe(display, width="stretch", hide_index=True)
        st.download_button(
            "Scarica i dati filtrati in CSV",
            data=display.to_csv(index=False).encode("utf-8-sig"),
            file_name="monitoraggio_scorte_panflu.csv",
            mime="text/csv"
        )

        st.markdown("##### Giacenze rispetto alla quantità minima per categoria")
        by_cat = current.groupby("categoria_panflu", as_index=False).agg({
            "giacenza_pezzi": "sum",
            "quantita_minima_richiesta": "sum",
            "scorte_scadute_pezzi": "sum",
        })
        cmp_long = by_cat.melt(
            id_vars="categoria_panflu",
            value_vars=["giacenza_pezzi", "quantita_minima_richiesta"],
            var_name="Misura", value_name="Pezzi",
        )
        cmp_long["Misura"] = cmp_long["Misura"].map({
            "giacenza_pezzi": "Giacenza",
            "quantita_minima_richiesta": "Quantità minima",
        })
        fig_cmp = px.bar(
            cmp_long, x="categoria_panflu", y="Pezzi", color="Misura", barmode="group",
            labels={"categoria_panflu": "Tipologia dispositivo"},
        )
        st.plotly_chart(fig_cmp, width="stretch")

        colg1, colg2 = st.columns(2)
        with colg1:
            st.markdown("##### Scorte scadute per categoria")
            fig_exp = px.bar(
                by_cat, x="categoria_panflu", y="scorte_scadute_pezzi",
                labels={"categoria_panflu": "Tipologia dispositivo", "scorte_scadute_pezzi": "Scorte scadute (pezzi)"},
            )
            st.plotly_chart(fig_exp, width="stretch")
        with colg2:
            st.markdown("##### Distribuzione per esito verifica")
            esito_counts = current["esito"].value_counts().reset_index()
            esito_counts.columns = ["Esito", "Righe"]
            fig_esito = px.pie(
                esito_counts, names="Esito", values="Righe", hole=0.45,
                color="Esito",
                color_discrete_map={"Conforme": "#2e7d32", "Sotto soglia": "#c62828"},
            )
            st.plotly_chart(fig_esito, width="stretch")
    st.caption("Nel processo descritto nei requisiti, la quantità minima è definita a livello regionale per ente e dispositivo e aggiornata annualmente. Nel prototipo è un parametro simulato, non un valore ufficiale.")

with tab2:
    st.subheader("Andamento di consumi, giacenze e scorte scadute")
    trend = data.copy()
    if selected_entity != "Tutti":
        trend = trend[trend["id_ente"] == selected_entity]
    if selected_category != "Tutte":
        trend = trend[trend["categoria_panflu"] == selected_category]
    monthly = trend.groupby("mese_riferimento", as_index=False).agg({
        "consumo_mensile_pezzi": "sum",
        "giacenza_pezzi": "sum",
        "scorte_scadute_pezzi": "sum",
        "quantita_minima_richiesta": "sum"
    })
    metric_choice = st.radio("Indicatore da visualizzare", ["Consumi", "Giacenze", "Scorte scadute", "Quantità minima richiesta"], horizontal=True)
    col_map = {
        "Consumi": ("consumo_mensile_pezzi", "Consumo mensile (pezzi)"),
        "Giacenze": ("giacenza_pezzi", "Giacenza (pezzi)"),
        "Scorte scadute": ("scorte_scadute_pezzi", "Scorte scadute (pezzi)"),
        "Quantità minima richiesta": ("quantita_minima_richiesta", "Quantità minima richiesta (pezzi)")
    }
    y_col, y_label = col_map[metric_choice]
    fig = px.line(monthly, x="mese_riferimento", y=y_col, markers=True, labels={"mese_riferimento":"Mese", y_col:y_label})
    st.plotly_chart(fig, width="stretch")

    st.markdown("##### Copertura: giacenza vs quantità minima nel tempo")
    coverage = monthly.melt(
        id_vars="mese_riferimento",
        value_vars=["giacenza_pezzi", "quantita_minima_richiesta"],
        var_name="Misura", value_name="Pezzi",
    )
    coverage["Misura"] = coverage["Misura"].map({
        "giacenza_pezzi": "Giacenza",
        "quantita_minima_richiesta": "Quantità minima",
    })
    fig_cov = px.area(
        coverage, x="mese_riferimento", y="Pezzi", color="Misura",
        labels={"mese_riferimento": "Mese"},
    )
    fig_cov.update_traces(selector=dict(name="Quantità minima"), fill="none")
    st.plotly_chart(fig_cov, width="stretch")

    st.subheader("Previsione dimostrativa dei consumi")
    if selected_category == "Tutte":
        forecast_category = st.selectbox("Categoria da prevedere", CATEGORIES)
    else:
        forecast_category = selected_category
    fdata = data[data["categoria_panflu"] == forecast_category].copy()
    if selected_entity != "Tutti":
        fdata = fdata[fdata["id_ente"] == selected_entity]
    hist = fdata.groupby("mese_riferimento", as_index=False)["consumo_mensile_pezzi"].sum().sort_values("mese_riferimento")
    y = hist["consumo_mensile_pezzi"].to_numpy(dtype=float)
    future_dates = pd.date_range(hist["mese_riferimento"].max() + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    hist_months = hist["mese_riferimento"].dt.month.to_numpy()
    indices = seasonal_indices(y, hist_months)
    # Lo scenario (variazione, variabilità, stagionalità) è ipotetico e vale per previsioni e componenti di scorta.
    fx = forecast_experiment(y, hist_months, future_dates.month.to_numpy(), horizon, window,
                             variability, trend_change, season, indices)
    metrics, best, future, y_scenario = fx["metrics"], fx["best"], fx["future"], fx["y_scen"]
    chart_hist = pd.DataFrame({"Mese": hist["mese_riferimento"], "Quantità": y_scenario, "Serie": "Storico (scenario)"})
    chart_future = pd.DataFrame({"Mese": future_dates, "Quantità": future, "Serie": "Previsione selezionata"})
    ffig = px.line(pd.concat([chart_hist, chart_future]), x="Mese", y="Quantità", color="Serie", markers=True)
    st.plotly_chart(ffig, width="stretch")
    st.write("Confronto dei metodi su un periodo cronologico di verifica:")
    st.dataframe(metrics.round(2), width="stretch", hide_index=True)
    st.success(f"Metodo selezionato in base all'RMSE più basso: {best}.")
    pred_table = pd.DataFrame({"Mese previsto": future_dates.strftime("%Y-%m"), "Consumo previsto (pezzi)": np.round(future).astype(int)})
    st.dataframe(pred_table, width="stretch", hide_index=True)
    with st.expander("Indici stagionali stimati"):
        season_table = pd.DataFrame({
            "Mese": MONTH_NAMES,
            "Indice stagionale stimato": np.round(indices, 3),
            "Fattore applicato (intensità)": np.round(seasonal_factor(indices, np.arange(1, 13), season), 3),
        })
        st.dataframe(season_table, width="stretch", hide_index=True)
        st.caption("Indice = rapporto medio tra consumo e trend lineare per mese di calendario, normalizzato a media 1. "
                   "Su dati sintetici il profilo è debole e puramente illustrativo.")
    st.caption("La previsione è una dimostrazione metodologica su dati simulati, non una previsione operativa né un quantitativo ufficiale di scorta minima.")

with tab3:
    st.subheader("Stima didattica delle componenti di scorta")
    cat_for_stock = selected_category if selected_category != "Tutte" else st.selectbox("Categoria per il calcolo delle componenti", CATEGORIES, key="stockcat")
    stock_hist = data[data["categoria_panflu"] == cat_for_stock].copy()
    if selected_entity != "Tutti":
        stock_hist = stock_hist[stock_hist["id_ente"] == selected_entity]
    by_month = stock_hist.groupby("mese_riferimento")["consumo_mensile_pezzi"].sum().sort_index()
    stock_dates = pd.date_range(by_month.index.max() + pd.offsets.MonthBegin(1), periods=horizon, freq="MS") if len(by_month) else pd.DatetimeIndex([])
    stock_months = np.asarray(by_month.index.month)
    stock_indices = seasonal_indices(by_month.to_numpy(dtype=float), stock_months)
    comp = stock_components(by_month.to_numpy(dtype=float), stock_months, stock_dates.month.to_numpy(), lead_days,
                            service_level, variability, horizon, window, trend_change, season, stock_indices)
    inv = pd.DataFrame([
        {"Componente": "Ciclica", "Quantità stimata (pezzi)": comp["Ciclica"], "Criterio dimostrativo": "Domanda giornaliera di scenario (media ultimi 6 mesi) × 30 giorni / 2"},
        {"Componente": "Sicurezza", "Quantità stimata (pezzi)": comp["Sicurezza"], "Criterio dimostrativo": "z × deviazione standard giornaliera di scenario × variabilità × √lead time"},
        {"Componente": "Anticipata", "Quantità stimata (pezzi)": comp["Anticipata"], "Criterio dimostrativo": "Previsione di scenario meno media recente di scenario (ultimi 3 mesi), × lead time in mesi"},
        {"Componente": "Pipeline", "Quantità stimata (pezzi)": comp["Pipeline"], "Criterio dimostrativo": "Domanda giornaliera di scenario × lead time"}
    ])
    st.dataframe(inv.round(1), width="stretch", hide_index=True)
    st.plotly_chart(px.bar(inv, x="Componente", y="Quantità stimata (pezzi)"), width="stretch")
    st.caption("Variazione simulata della domanda e intensità della stagionalità modificano la domanda di scenario su cui sono calcolate le componenti.")
    st.info("Queste componenti sono un'estensione didattica della traccia PW24. Non equivalgono alla quantità minima PANFLU definita a livello regionale e non devono essere sommate automaticamente: le definizioni possono sovrapporsi.")

with tab4:
    st.subheader("Articoli di magazzino e parametri di scorta")
    st.caption(
        "Dati da data/domanda_storica.csv (domanda mensile) e data/parametri_scorte.csv (parametri per articolo). "
        "Lead time e livello di servizio dello slider non si applicano a questa scheda: si usano quelli del file dei parametri; "
        "i filtri ente e categoria non si applicano. Orizzonte, finestra, variabilità, variazione e stagionalità sì."
    )
    art_results = {}
    for art in ARTICLES:
        sub = demand[demand["articolo"] == art].sort_values("data")
        ya = sub["domanda"].to_numpy(dtype=float)
        months_a = sub["data"].dt.month.to_numpy()
        dates_a = pd.date_range(sub["data"].max() + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
        idx_a = seasonal_indices(ya, months_a)
        # mesi_stagionali: moltiplicatore specifico dell'articolo applicato all'intensità dello slider.
        s_eff = float(np.clip(season * float(params.loc[art, "mesi_stagionali"]), 0.0, 1.0))
        fxa = forecast_experiment(ya, months_a, dates_a.month.to_numpy(), horizon, window,
                                  variability, trend_change, s_eff, idx_a)
        compa = stock_components(ya, months_a, dates_a.month.to_numpy(), float(params.loc[art, "lead_time_giorni"]),
                                 float(params.loc[art, "livello_servizio"]), variability, horizon, window,
                                 trend_change, s_eff, idx_a, cycle_days=float(params.loc[art, "periodo_riordino_giorni"]))
        art_results[art] = dict(dates=sub["data"], y=ya, dates_future=dates_a, fx=fxa, comp=compa)

    st.markdown("##### Parametri degli articoli")
    par_table = params.loc[ARTICLES].reset_index().rename(columns={
        "articolo": "Articolo", "scorta_attuale": "Scorta attuale", "costo_unitario_eur": "Costo unitario (EUR)",
        "lead_time_giorni": "Lead time (giorni)", "livello_servizio": "Livello di servizio",
        "periodo_riordino_giorni": "Periodo di riordino (giorni)", "mesi_stagionali": "Fattore stagionalità",
    })
    st.dataframe(par_table, width="stretch", hide_index=True)

    st.markdown("##### Domanda storica per articolo")
    hist_art = demand.rename(columns={"data": "Mese", "articolo": "Articolo", "domanda": "Domanda (pezzi)"})
    st.plotly_chart(px.line(hist_art, x="Mese", y="Domanda (pezzi)", color="Articolo", markers=True), width="stretch")

    st.markdown("##### Confronto dei metodi per articolo")
    rows = []
    for art in ARTICLES:
        fxa = art_results[art]["fx"]
        for _, r in fxa["metrics"].iterrows():
            rows.append({"Articolo": art, "Metodo": r["Metodo"], "MAE": r["MAE"], "RMSE": r["RMSE"],
                         "MAPE (%)": r["MAPE (%)"], "Selezionato": "sì" if r["Metodo"] == fxa["best"] else "no"})
    st.dataframe(pd.DataFrame(rows).round(2), width="stretch", hide_index=True)

    st.markdown("##### Componenti di scorta per articolo")
    rows = []
    for art in ARTICLES:
        ca = art_results[art]["comp"]
        daily = ca["_daily_mean"]
        rows.append({
            "Articolo": art, "Lead time (giorni)": float(params.loc[art, "lead_time_giorni"]),
            "Livello di servizio": float(params.loc[art, "livello_servizio"]),
            "Ciclica": ca["Ciclica"], "Sicurezza": ca["Sicurezza"], "Anticipata": ca["Anticipata"], "Pipeline": ca["Pipeline"],
            "Copertura (giorni)": float(params.loc[art, "scorta_attuale"]) / daily if daily > 0 else np.nan,
        })
    st.dataframe(pd.DataFrame(rows).round({"Ciclica": 1, "Sicurezza": 1, "Anticipata": 1, "Pipeline": 1, "Copertura (giorni)": 1}),
                 width="stretch", hide_index=True)

    st.markdown("##### Dettaglio articolo")
    detail = st.selectbox("Articolo di dettaglio", ARTICLES)
    dr = art_results[detail]
    chart_h = pd.DataFrame({"Mese": dr["dates"], "Quantità": dr["fx"]["y_scen"], "Serie": "Storico (scenario)"})
    chart_f = pd.DataFrame({"Mese": dr["dates_future"], "Quantità": dr["fx"]["future"], "Serie": "Previsione selezionata"})
    st.plotly_chart(px.line(pd.concat([chart_h, chart_f]), x="Mese", y="Quantità", color="Serie", markers=True), width="stretch")
    comp_detail = pd.DataFrame({
        "Tipo di scorta": ["Ciclica", "Sicurezza", "Anticipata", "Pipeline"],
        "Quantità (pezzi)": [dr["comp"][k] for k in ("Ciclica", "Sicurezza", "Anticipata", "Pipeline")],
    })
    st.plotly_chart(px.bar(comp_detail, x="Tipo di scorta", y="Quantità (pezzi)"), width="stretch")
    st.dataframe(pd.DataFrame({
        "Mese (articolo)": dr["dates_future"].strftime("%Y-%m"),
        "Domanda prevista (pezzi)": np.round(dr["fx"]["future"]).astype(int),
    }), width="stretch", hide_index=True)
    st.caption("Stime dimostrative su dati sintetici, non quantitativi operativi.")

st.divider()
st.subheader("Assunzioni, perimetro e limiti")
st.markdown("""
- Il prototipo riprende i concetti dei requisiti PANFLU/S.A.S.H.A.: ente, categoria di dispositivo, mese di riferimento, consumi, quantità minima, giacenze, scorte scadute ed esito.
- Le sei categorie dimostrative sono: disinfettanti, guanti, camici chirurgici, mascherine chirurgiche, copricapo e calzari.
- Il documento dei requisiti prevede il monitoraggio tramite dati aggregati e la verifica della quantità minima definita a livello regionale. Il prototipo simula tali dati e non implementa il flusso SMAF/PANFLU né un'integrazione con S.A.S.H.A.
- Le scorte minime nel dataset sono valori sintetici. In un sistema reale devono provenire dalla configurazione ufficiale regionale per ente e dispositivo.
- La logica di esito usa una regola trasparente: giacenza maggiore o uguale alla quantità minima = conforme; giacenza inferiore = sotto soglia. Il requisito originale cita indicatori verde/rosso per confronto con la soglia.
- Le previsioni confrontano media mobile semplice e regressione lineare su un periodo di verifica cronologico; i risultati sono solo illustrativi.
- La stagionalità è stimata dallo storico (rapporto al trend lineare, media per mese di calendario, media 1). Lo slider applica il profilo con fattore 1 + intensità × (indice − 1): a 0 è neutra. Poiché la serie osservata contiene già la propria stagionalità, l'intensità è uno scenario di stagionalità accentuata; sui dati sintetici il profilo è debole.
- Variazione simulata e stagionalità formano la domanda di scenario, usata sia nelle previsioni sia nelle componenti di scorta. La variabilità agisce sulle previsioni e sulla sola scorta di sicurezza.
- La scheda «Articoli e parametri» usa domanda_storica.csv e parametri_scorte.csv. La colonna mesi_stagionali è letta come moltiplicatore dell'intensità di stagionalità dell'articolo (1,0 = intensità dello slider; 0 = nessuna stagionalità).
- All'avvio i tre file CSV sono validati (presenza, colonne, righe, tipi, valori, mesi, duplicati): in caso di problema compare un errore in italiano e l'app si ferma.
- Per uso reale servirebbero controlli sulle unità di misura, lotti/scadenze, gestione delle rettifiche, autorizzazioni, audit e definizione delle responsabilità operative.
""")
