import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "monitoraggio_panflu_demo.csv"

st.set_page_config(page_title="PW24 | Monitoraggio delle scorte pandemiche", page_icon="📦", layout="wide")
st.title("Monitoraggio delle scorte pandemiche")
st.caption("PW 24 · Pegaso L-31 · Sviluppo di una mini-dashboard Python per la previsione della domanda e la pianificazione delle scorte")
st.warning(
    "Prototipo didattico: tutti gli enti, i consumi, le giacenze, le quantità minime e le scorte scadute "
    "sono simulati. Non rappresentano dati reali di Regione Lombardia, ARIA, AREU o di enti sanitari."
)

data = pd.read_csv(DATA_FILE)
data["mese_riferimento"] = pd.to_datetime(data["mese_riferimento"] + "-01")
CATEGORIES = sorted(data["categoria_panflu"].unique())
MONTHS = sorted(data["mese_riferimento"].unique())
LATEST = max(MONTHS)

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

tab1, tab2, tab3 = st.tabs(["Monitoraggio", "Analisi temporale e previsione", "Componenti di scorta"])

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
        st.dataframe(display, use_container_width=True, hide_index=True)
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
        st.plotly_chart(fig_cmp, use_container_width=True)

        colg1, colg2 = st.columns(2)
        with colg1:
            st.markdown("##### Scorte scadute per categoria")
            fig_exp = px.bar(
                by_cat, x="categoria_panflu", y="scorte_scadute_pezzi",
                labels={"categoria_panflu": "Tipologia dispositivo", "scorte_scadute_pezzi": "Scorte scadute (pezzi)"},
            )
            st.plotly_chart(fig_exp, use_container_width=True)
        with colg2:
            st.markdown("##### Distribuzione per esito verifica")
            esito_counts = current["esito"].value_counts().reset_index()
            esito_counts.columns = ["Esito", "Righe"]
            fig_esito = px.pie(
                esito_counts, names="Esito", values="Righe", hole=0.45,
                color="Esito",
                color_discrete_map={"Conforme": "#2e7d32", "Sotto soglia": "#c62828"},
            )
            st.plotly_chart(fig_esito, use_container_width=True)
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
    st.plotly_chart(fig, use_container_width=True)

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
    st.plotly_chart(fig_cov, use_container_width=True)

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
    # Scenario transformation is explicitly hypothetical and affects only the forecast experiment.
    idx = np.arange(len(y))
    y_scenario = np.maximum(0, y * (1 + (trend_change / 100) * (idx / max(1, len(idx)-1))))
    smooth = pd.Series(y_scenario).rolling(3, min_periods=1).mean().to_numpy()
    y_scenario = np.maximum(0, smooth + (y_scenario - smooth) * variability)
    test_n = min(4, max(2, len(y_scenario)//5))
    train, test = y_scenario[:-test_n], y_scenario[-test_n:]
    ma_test = moving_average_forecast(train, test_n, window)
    lin_test = linear_forecast(train, test_n)
    metrics = pd.DataFrame([
        {"Metodo": "Media mobile semplice", **error_metrics(test, ma_test)},
        {"Metodo": "Regressione lineare", **error_metrics(test, lin_test)}
    ])
    best = metrics.sort_values("RMSE").iloc[0]["Metodo"]
    future_ma = moving_average_forecast(y_scenario, horizon, window)
    future_lin = linear_forecast(y_scenario, horizon)
    future = future_ma if best == "Media mobile semplice" else future_lin
    future_dates = pd.date_range(hist["mese_riferimento"].max() + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    chart_hist = pd.DataFrame({"Mese": hist["mese_riferimento"], "Quantità": y_scenario, "Serie": "Storico (scenario)"})
    chart_future = pd.DataFrame({"Mese": future_dates, "Quantità": future, "Serie": "Previsione selezionata"})
    ffig = px.line(pd.concat([chart_hist, chart_future]), x="Mese", y="Quantità", color="Serie", markers=True)
    st.plotly_chart(ffig, use_container_width=True)
    st.write("Confronto dei metodi su un periodo cronologico di verifica:")
    st.dataframe(metrics.round(2), use_container_width=True, hide_index=True)
    st.success(f"Metodo selezionato in base all'RMSE più basso: {best}.")
    pred_table = pd.DataFrame({"Mese previsto": future_dates.strftime("%Y-%m"), "Consumo previsto (pezzi)": np.round(future).astype(int)})
    st.dataframe(pred_table, use_container_width=True, hide_index=True)
    st.caption("La previsione è una dimostrazione metodologica su dati simulati, non una previsione operativa né un quantitativo ufficiale di scorta minima.")

with tab3:
    st.subheader("Stima didattica delle componenti di scorta")
    cat_for_stock = selected_category if selected_category != "Tutte" else st.selectbox("Categoria per il calcolo delle componenti", CATEGORIES, key="stockcat")
    stock_hist = data[data["categoria_panflu"] == cat_for_stock].copy()
    if selected_entity != "Tutti":
        stock_hist = stock_hist[stock_hist["id_ente"] == selected_entity]
    by_month = stock_hist.groupby("mese_riferimento")["consumo_mensile_pezzi"].sum().sort_index()
    daily_mean = float(by_month.tail(6).mean() / 30.4375) if len(by_month) else 0.0
    daily_std = float(by_month.tail(12).std(ddof=1) / 30.4375) if len(by_month) > 1 else 0.0
    z_values = {0.90:1.282, 0.95:1.645, 0.975:1.960, 0.99:2.326}
    z = z_values[service_level]
    safety = z * daily_std * variability * math.sqrt(lead_days)
    cycle = daily_mean * 30 / 2
    pipeline = daily_mean * lead_days
    last3 = float(by_month.tail(3).mean()) if len(by_month) else 0.0
    forecast_mean = float(np.mean(moving_average_forecast(by_month.to_numpy(dtype=float), horizon, window))) if len(by_month) else last3
    anticipatory = max(0.0, forecast_mean - last3) * (lead_days / 30.4375)
    inv = pd.DataFrame([
        {"Componente": "Ciclica", "Quantità stimata (pezzi)": cycle, "Criterio dimostrativo": "Domanda media giornaliera × 30 giorni / 2"},
        {"Componente": "Sicurezza", "Quantità stimata (pezzi)": safety, "Criterio dimostrativo": "z × deviazione standard giornaliera × √lead time"},
        {"Componente": "Anticipata", "Quantità stimata (pezzi)": anticipatory, "Criterio dimostrativo": "Incremento previsto rispetto alla media recente × lead time in mesi"},
        {"Componente": "Pipeline", "Quantità stimata (pezzi)": pipeline, "Criterio dimostrativo": "Domanda media giornaliera × lead time"}
    ])
    st.dataframe(inv.round(1), use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(inv, x="Componente", y="Quantità stimata (pezzi)"), use_container_width=True)
    st.info("Queste componenti sono un'estensione didattica della traccia PW24. Non equivalgono alla quantità minima PANFLU definita a livello regionale e non devono essere sommate automaticamente: le definizioni possono sovrapporsi.")

st.divider()
st.subheader("Assunzioni, perimetro e limiti")
st.markdown("""
- Il prototipo riprende i concetti dei requisiti PANFLU/S.A.S.H.A.: ente, categoria di dispositivo, mese di riferimento, consumi, quantità minima, giacenze, scorte scadute ed esito.
- Le sei categorie dimostrative sono: disinfettanti, guanti, camici chirurgici, mascherine chirurgiche, copricapo e calzari.
- Il documento dei requisiti prevede il monitoraggio tramite dati aggregati e la verifica della quantità minima definita a livello regionale. Il prototipo simula tali dati e non implementa il flusso SMAF/PANFLU né un'integrazione con S.A.S.H.A.
- Le scorte minime nel dataset sono valori sintetici. In un sistema reale devono provenire dalla configurazione ufficiale regionale per ente e dispositivo.
- La logica di esito usa una regola trasparente: giacenza maggiore o uguale alla quantità minima = conforme; giacenza inferiore = sotto soglia. Il requisito originale cita indicatori verde/rosso per confronto con la soglia.
- Le previsioni confrontano media mobile semplice e regressione lineare su un periodo di verifica cronologico; i risultati sono solo illustrativi.
- Per uso reale servirebbero validazione dei dati, controlli su duplicati e unità di misura, lotti/scadenze, gestione delle rettifiche, autorizzazioni, audit e definizione delle responsabilità operative.
""")
