"""Suite di test automatici della dashboard PW24 (Streamlit AppTest + pandas/NumPy).

L'app viene eseguita con streamlit.testing.v1.AppTest (v1.1: stagionalita', scheda articoli, validazione CSV).
Ogni funzione test_tc_XX corrisponde a un caso del Test Book (Test_Book_PW24.md/.docx).
I valori attesi sono ricalcolati in modo indipendente dai CSV con pandas/NumPy (funzioni ref_*).

Esecuzione (da cartella PW24):
    .venv\\Scripts\\python.exe -m pytest test/test_dashboard.py -v --junitxml=test/results/junit.xml
"""
import ast
import io
import itertools
import json
import math
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import warnings
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

warnings.filterwarnings("ignore")

PW24 = Path(__file__).resolve().parent.parent
APP_DIR = PW24 / "acamino_0312501773" / "PW24_dashboard_sanitario"
APP = str(APP_DIR / "app.py")
DATA = APP_DIR / "data"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
DF = pd.read_csv(DATA / "monitoraggio_panflu_demo.csv")
DEM = pd.read_csv(DATA / "domanda_storica.csv")
PAR = pd.read_csv(DATA / "parametri_scorte.csv")
ARTS = sorted(DEM["articolo"].unique())
ENTI = sorted(DF["id_ente"].unique())
CATS = sorted(DF["categoria_panflu"].unique())
MONTHS = sorted(DF["mese_riferimento"].unique())
DETAILS = {}
Z = {0.90: 1.282, 0.95: 1.645, 0.975: 1.960, 0.99: 2.326}


# ----------------------------------------------------------------------------- utilità
def record(tc, expected, actual, note=""):
    DETAILS[tc] = {"atteso": str(expected), "ottenuto": str(actual), "note": note}


@pytest.fixture(scope="session", autouse=True)
def _dump_details():
    yield
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "details.json").write_text(json.dumps(DETAILS, ensure_ascii=False, indent=1), encoding="utf-8")


def run(month=None, ente=None, cat=None, esito=None, horizon=3, window=3, var=1.0, trend=0,
        lead=30, svc=0.95, fcat=None, scat=None, radio=None, season=0.0, art=None, timeout=120):
    """Esegue l'app con AppTest impostando i widget; restituisce (AppTest, dati_download)."""
    captured = []
    orig = st.download_button

    def spy(*a, **k):
        captured.append(k)
        return orig(*a, **k)

    with mock.patch.object(st, "download_button", spy):
        at = AppTest.from_file(APP, default_timeout=timeout)
        at.run()
        sb = at.sidebar
        if month is not None:
            sb.selectbox[0].select_index(MONTHS.index(month))
        if ente is not None:
            sb.selectbox[1].select(ente)
        if cat is not None:
            sb.selectbox[2].select(cat)
        if esito is not None:
            sb.selectbox[3].select(esito)
        sb.slider[0].set_value(horizon)
        sb.slider[1].set_value(window)
        sb.slider[2].set_value(var)
        sb.slider[3].set_value(trend)
        sb.slider[4].set_value(lead)
        sb.slider[5].set_value(season)
        sb.select_slider[0].set_value(svc)
        captured.clear()
        at.run()
        changed = False
        for label, val in (("Categoria da prevedere", fcat), ("Categoria per il calcolo delle componenti", scat),
                           ("Articolo di dettaglio", art)):
            if val is not None:
                [s for s in at.selectbox if s.label == label][0].select(val)
                changed = True
        if radio is not None:
            at.radio[0].set_value(radio)
            changed = True
        if changed:
            captured.clear()
            at.run()
    return at, (captured[-1] if captured else None)


def df_with(at, col):
    for d in at.dataframe:
        if col in d.value.columns:
            return d.value
    return None


def num(s):
    return int(re.sub(r"[^\d]", "", s.split()[0]))


def metrics_of(at):
    return {m.label: num(m.value) for m in at.metric}


def ref_filter(month, ente=None, cat=None, esito=None):
    d = DF[DF["mese_riferimento"] == month].copy()
    if ente:
        d = d[d["id_ente"] == ente]
    if cat:
        d = d[d["categoria_panflu"] == cat]
    d["esito"] = np.where(d["giacenza_pezzi"] >= d["quantita_minima_richiesta"], "Conforme", "Sotto soglia")
    if esito and esito != "Tutti":
        d = d[d["esito"] == esito]
    return d


def ref_expected_metrics(d):
    return {
        "Giacenze rilevate": int(d["giacenza_pezzi"].sum()),
        "Quantità minima richiesta": int(d["quantita_minima_richiesta"].sum()),
        "Righe sotto soglia": int((d["giacenza_pezzi"] < d["quantita_minima_richiesta"]).sum()),
        "Scorte scadute rilevate": int(d["scorte_scadute_pezzi"].sum()),
    }


# ---- riferimenti indipendenti per previsioni e scorte (implementazione manuale, non importata dall'app)
def ref_series(cat, ente=None):
    d = DF[DF["categoria_panflu"] == cat]
    if ente:
        d = d[d["id_ente"] == ente]
    return d.groupby("mese_riferimento")["consumo_mensile_pezzi"].sum().sort_index().to_numpy(float)


def ref_ma(series, h, w):
    v = list(series)
    out = []
    for _ in range(h):
        x = sum(v[-w:]) / len(v[-w:])
        out.append(max(0.0, x))
        v.append(x)
    return np.array(out)


def ref_lin(series, h):
    n = len(series)
    x = np.arange(n, dtype=float)
    sl = ((x - x.mean()) * (series - series.mean())).sum() / ((x - x.mean()) ** 2).sum()
    ic = series.mean() - sl * x.mean()
    return np.maximum(0, sl * np.arange(n, n + h) + ic)


def ref_err(a, p):
    a = np.asarray(a, float)
    p = np.asarray(p, float)
    mae = np.abs(a - p).mean()
    rmse = math.sqrt(((a - p) ** 2).mean())
    nz = a != 0
    mape = (np.abs((a[nz] - p[nz]) / a[nz])).mean() * 100 if nz.any() else float("nan")
    return mae, rmse, mape


def ref_ramp(y, trend):
    n = len(y)
    idx = np.arange(n)
    return np.maximum(0, np.asarray(y, float) * (1 + (trend / 100) * idx / max(1, n - 1)))


def ref_seasonal_indices(values, months):
    """Indici stagionali: rapporto al trend lineare (formula chiusa), media per mese di calendario, media 1."""
    y = np.asarray(values, float)
    if len(y) < 12:
        return np.ones(12)
    x = np.arange(len(y), dtype=float)
    sl = ((x - x.mean()) * (y - y.mean())).sum() / ((x - x.mean()) ** 2).sum()
    fit = sl * x + (y.mean() - sl * x.mean())
    ratio = pd.Series(np.where(fit > 0, y / np.where(fit > 0, fit, 1.0), np.nan))
    raw = ratio.groupby(np.asarray(months)).mean().reindex(range(1, 13)).fillna(1.0).to_numpy()
    return raw / raw.mean()


def ref_factor(idx, months, s):
    s = min(1.0, max(0.0, s))
    return 1.0 + s * (np.asarray(idx)[np.asarray(months) - 1] - 1.0)


def ref_scenario(y, trend, var):
    y1 = ref_ramp(y, trend)
    sm = pd.Series(y1).rolling(3, min_periods=1).mean().to_numpy()
    return np.maximum(0, sm + (y1 - sm) * var)


def ref_fc_core(y, months, fut_months, horizon, window, var, trend, season):
    y = np.asarray(y, float)
    ys = ref_scenario(y, trend, var)
    idx = ref_seasonal_indices(y, months)
    fh = ref_factor(idx, months, season)
    tn = min(4, max(2, len(ys) // 5))
    tr, te = ys[:-tn], (ys * fh)[-tn:]
    m_ma = ref_err(te, ref_ma(tr, tn, window) * fh[-tn:])
    m_li = ref_err(te, ref_lin(tr, tn) * fh[-tn:])
    best = "Media mobile semplice" if m_ma[1] <= m_li[1] else "Regressione lineare"
    base = ref_ma(ys, horizon, window) if best == "Media mobile semplice" else ref_lin(ys, horizon)
    fut = base * ref_factor(idx, fut_months, season)
    return {"ma": m_ma, "lin": m_li, "best": best, "future": fut, "test_n": tn, "scen": ys * fh, "idx": idx}


CAT_MONTHS = [int(m[5:7]) for m in MONTHS]


def ref_fut_months(h):
    return [(k % 12) + 1 for k in range(h)]  # la serie delle categorie termina a dicembre 2025


def ref_forecast(cat, ente=None, horizon=3, window=3, var=1.0, trend=0, season=0.0):
    return ref_fc_core(ref_series(cat, ente), CAT_MONTHS, ref_fut_months(horizon), horizon, window, var, trend, season)


def ref_comp_core(y, months, fut_months, lead, svc, var, horizon, window, trend, season, cycle=30):
    ramp = ref_ramp(y, trend)
    idx = ref_seasonal_indices(y, months)
    ys = pd.Series(ramp * ref_factor(idx, months, season))
    dm = ys.tail(6).mean() / 30.4375
    ds = ys.tail(12).std(ddof=1) / 30.4375
    safety = Z[svc] * ds * var * math.sqrt(lead)
    fm = (ref_ma(ramp, horizon, window) * ref_factor(idx, fut_months, season)).mean()
    ant = max(0.0, fm - ys.tail(3).mean()) * lead / 30.4375
    return {"Ciclica": dm * cycle / 2, "Sicurezza": safety, "Anticipata": ant, "Pipeline": dm * lead, "dm": dm}


def ref_components(cat, ente=None, lead=30, svc=0.95, var=1.0, horizon=3, window=3, trend=0, season=0.0):
    c = ref_comp_core(ref_series(cat, ente), CAT_MONTHS, ref_fut_months(horizon), lead, svc, var, horizon, window, trend, season)
    return {k: c[k] for k in ("Ciclica", "Sicurezza", "Anticipata", "Pipeline")}


def ref_article(art, horizon=3, window=3, var=1.0, trend=0, season=0.0):
    """Ricalcolo indipendente dalla vista articoli a partire da domanda_storica.csv e parametri_scorte.csv."""
    sub = DEM[DEM["articolo"] == art].sort_values("data")
    dates = pd.to_datetime(sub["data"])
    y = sub["domanda"].to_numpy(float)
    months = dates.dt.month.to_numpy()
    fut = [(dates.max().month - 1 + k) % 12 + 1 for k in range(1, horizon + 1)]
    p = PAR.set_index("articolo").loc[art]
    s_eff = min(1.0, max(0.0, season * float(p["mesi_stagionali"])))
    fc = ref_fc_core(y, months, fut, horizon, window, var, trend, s_eff)
    cm = ref_comp_core(y, months, fut, float(p["lead_time_giorni"]), float(p["livello_servizio"]), var, horizon, window,
                       trend, s_eff, cycle=float(p["periodo_riordino_giorni"]))
    cm["Copertura"] = float(p["scorta_attuale"]) / cm["dm"]
    return {"fc": fc, "comp": cm, "p": p}


def comps_of(at):
    d = df_with(at, "Componente")
    return dict(zip(d["Componente"], d["Quantità stimata (pezzi)"]))


def assert_none(errors):
    assert not errors, "\n".join(errors[:15])


def load_app_functions():
    """Estrae (senza eseguire Streamlit) le funzioni pure dell'app per test unitari."""
    tree = ast.parse(Path(APP).read_text(encoding="utf-8"))
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    ns = {"np": np, "pd": pd, "math": math}
    exec(compile(ast.Module(body=body, type_ignores=[]), APP, "exec"), ns)
    return ns


# ============================================================================ DATI E INTEGRITÀ
def test_tc_01_struttura_csv():
    cols = ["id_ente", "tipologia_ente", "categoria_panflu", "mese_riferimento", "consumo_mensile_pezzi",
            "quantita_minima_richiesta", "giacenza_pezzi", "scorte_scadute_pezzi"]
    record("TC-01", "864 righe; colonne " + ", ".join(cols), f"{DF.shape[0]} righe; colonne {list(DF.columns)}")
    assert DF.shape == (864, 8)
    assert list(DF.columns) == cols


def test_tc_02_integrita_dati():
    chiave_dup = int(DF.duplicated(["id_ente", "categoria_panflu", "mese_riferimento"]).sum())
    nulli = int(DF.isna().sum().sum())
    comb = len(ENTI) * len(CATS) * len(MONTHS)
    record("TC-02", "0 nulli; 0 duplicati sulla chiave; 6 enti x 6 categorie x 24 mesi = 864",
           f"{nulli} nulli; {chiave_dup} duplicati; {len(ENTI)} x {len(CATS)} x {len(MONTHS)} = {comb}")
    assert nulli == 0 and chiave_dup == 0 and comb == 864
    assert MONTHS[0] == "2024-01" and MONTHS[-1] == "2025-12"


def test_tc_03_validita_valori():
    neg = int((DF[["consumo_mensile_pezzi", "quantita_minima_richiesta", "giacenza_pezzi", "scorte_scadute_pezzi"]] < 0).sum().sum())
    minz = int((DF["quantita_minima_richiesta"] <= 0).sum())
    scad = int((DF["scorte_scadute_pezzi"] > DF["giacenza_pezzi"]).sum())
    mesi_ok = bool(DF["mese_riferimento"].str.fullmatch(r"\d{4}-\d{2}").all())
    record("TC-03", "0 valori negativi; 0 quantita minime <= 0; 0 righe con scadute > giacenza; mesi formato AAAA-MM",
           f"negativi={neg}; minime<=0: {minz}; scadute>giacenza: {scad}; formato mese ok={mesi_ok}")
    assert neg == 0 and minz == 0 and scad == 0 and mesi_ok


def test_tc_04_totali_esito():
    sotto = int((DF["giacenza_pezzi"] < DF["quantita_minima_richiesta"]).sum())
    perc = round(sotto / len(DF) * 100, 1)
    scad = int(DF["scorte_scadute_pezzi"].sum())
    uguali = int((DF["giacenza_pezzi"] == DF["quantita_minima_richiesta"]).sum())
    record("TC-04", "525 sotto soglia su 864 = 60,8%; scorte scadute totali 47.036; 1 riga con giacenza = minima",
           f"{sotto} su {len(DF)} = {perc}%; scadute totali {scad}; righe uguali {uguali}")
    assert (sotto, perc, scad, uguali) == (525, 60.8, 47036, 1)


def test_tc_05_file_ausiliari():
    dem = pd.read_csv(DATA / "domanda_storica.csv")
    par = pd.read_csv(DATA / "parametri_scorte.csv")
    record("TC-05", "domanda_storica.csv 144 righe, 4 articoli, colonne data/articolo/domanda; parametri_scorte.csv 4 righe",
           f"domanda {dem.shape}, articoli={dem['articolo'].nunique()}, colonne={list(dem.columns)}; parametri {par.shape}")
    assert dem.shape == (144, 3) and dem["articolo"].nunique() == 4 and par.shape[0] == 4
    assert list(dem.columns) == ["data", "articolo", "domanda"]
    assert dem.isna().sum().sum() == 0 and par.isna().sum().sum() == 0


# ============================================================================ AVVIO E INDICATORI
def test_tc_06_avvio_e_struttura():
    at, _ = run()
    titolo = at.title[0].value if at.title else None
    tabs = [t.label for t in at.tabs]
    record("TC-06", "nessuna eccezione; titolo 'Monitoraggio delle scorte pandemiche'; 4 tab (3 originali + 'Articoli e parametri'); 4 indicatori; 10 grafici; avviso prototipo",
           f"eccezioni={len(at.exception)}; titolo={titolo!r}; tab={tabs}; indicatori={len(at.metric)}; grafici={len(at.get('plotly_chart'))}; warning={len(at.warning)}")
    assert not at.exception
    assert titolo == "Monitoraggio delle scorte pandemiche"
    assert tabs == ["Monitoraggio", "Analisi temporale e previsione", "Componenti di scorta", "Articoli e parametri"]
    assert len(at.metric) == 4 and len(at.get("plotly_chart")) == 10 and len(at.warning) == 1


def test_tc_07_indicatori_default():
    at, _ = run()
    exp = ref_expected_metrics(ref_filter("2025-12"))
    got = metrics_of(at)
    t = df_with(at, "Esito verifica")
    record("TC-07", f"dicembre 2025: {exp}; 36 righe in tabella, 24 sotto soglia, 12 conformi",
           f"{got}; righe tabella={len(t)}; esiti={t['Esito verifica'].value_counts().to_dict()}")
    assert got == exp
    assert exp["Righe sotto soglia"] == 24 and exp["Scorte scadute rilevate"] == 1863
    assert len(t) == 36 and (t["Esito verifica"] == "Sotto soglia").sum() == 24


# ============================================================================ LOGICA ESITO
_MONTH_RUNS = {}


def month_run(m):
    if m not in _MONTH_RUNS:
        _MONTH_RUNS[m] = run(month=m)
    return _MONTH_RUNS[m]


def test_tc_08_logica_esito():
    errs = []
    tot = 0
    for m in MONTHS:
        at, _ = month_run(m)
        t = df_with(at, "Esito verifica")
        exp = np.where(t["Giacenza in magazzino"] >= t["Quantità minima richiesta"], "Conforme", "Sotto soglia")
        bad = int((t["Esito verifica"].to_numpy() != exp).sum())
        tot += len(t)
        if bad:
            errs.append(f"{m}: {bad} esiti incoerenti")
    # riga al limite: giacenza == quantita minima deve risultare Conforme
    lim = DF[DF["giacenza_pezzi"] == DF["quantita_minima_richiesta"]].iloc[0]
    at, _ = run(month=lim["mese_riferimento"], ente=lim["id_ente"], cat=lim["categoria_panflu"])
    t = df_with(at, "Esito verifica")
    record("TC-08", "esito = Conforme se giacenza >= quantita minima, altrimenti Sotto soglia, su 24 mesi (864 righe); riga al limite (giacenza = minima) = Conforme",
           f"righe verificate={tot}; incoerenze={len(errs)}; riga limite {lim['id_ente']}/{lim['categoria_panflu']}/{lim['mese_riferimento']} -> {t['Esito verifica'].iloc[0]}")
    assert tot == 864
    assert t["Esito verifica"].iloc[0] == "Conforme"
    assert_none(errs)


# ============================================================================ FILTRI
def test_tc_09_filtro_mese():
    errs = []
    for m in MONTHS:
        at, _ = month_run(m)
        exp = ref_expected_metrics(ref_filter(m))
        if metrics_of(at) != exp:
            errs.append(f"{m}: atteso {exp} ottenuto {metrics_of(at)}")
        t = df_with(at, "Mese/anno")
        if len(t) != 36 or set(t["Mese/anno"]) != {m}:
            errs.append(f"{m}: tabella non coerente ({len(t)} righe)")
    record("TC-09", "per ognuno dei 24 mesi: 36 righe, solo il mese scelto, indicatori = pandas", f"errori: {len(errs)}")
    assert_none(errs)


def test_tc_10_filtro_ente():
    errs = []
    for e in ENTI:
        at, _ = run(ente=e)
        exp = ref_expected_metrics(ref_filter("2025-12", ente=e))
        t = df_with(at, "Ente")
        if metrics_of(at) != exp or len(t) != 6 or set(t["Ente"]) != {e}:
            errs.append(f"{e}: atteso {exp}, ottenuto {metrics_of(at)}, righe {len(t)}")
    record("TC-10", "per ognuno dei 6 enti (dic 2025): 6 righe, indicatori = pandas", f"errori: {len(errs)}")
    assert_none(errs)


def test_tc_11_filtro_categoria():
    errs = []
    for c in CATS:
        at, _ = run(cat=c)
        exp = ref_expected_metrics(ref_filter("2025-12", cat=c))
        t = df_with(at, "Tipologia dispositivo")
        if metrics_of(at) != exp or len(t) != 6 or set(t["Tipologia dispositivo"]) != {c}:
            errs.append(f"{c}: atteso {exp}, ottenuto {metrics_of(at)}, righe {len(t)}")
    record("TC-11", "per ognuna delle 6 categorie (dic 2025): 6 righe, indicatori = pandas", f"errori: {len(errs)}")
    assert_none(errs)


def test_tc_12_filtro_esito():
    out = {}
    errs = []
    for es in ("Sotto soglia", "Conforme"):
        at, _ = run(esito=es)
        d = ref_filter("2025-12", esito=es)
        t = df_with(at, "Esito verifica")
        out[es] = len(t)
        if metrics_of(at) != ref_expected_metrics(d) or len(t) != len(d) or set(t["Esito verifica"]) != {es}:
            errs.append(f"{es}: ottenuto {metrics_of(at)} righe {len(t)}")
    record("TC-12", "dic 2025: 'Sotto soglia' = 24 righe, 'Conforme' = 12 righe, indicatori = pandas; 'Righe sotto soglia' = 0 con Conforme",
           f"righe {out}; errori {len(errs)}")
    assert out == {"Sotto soglia": 24, "Conforme": 12}
    assert_none(errs)


def test_tc_13_filtri_combinati():
    rng = np.random.default_rng(24)
    errs = []
    n = 0
    for _ in range(14):
        m = MONTHS[int(rng.integers(len(MONTHS)))]
        e = [None] + ENTI
        c = [None] + CATS
        x = [None, "Sotto soglia", "Conforme"]
        e, c, x = e[int(rng.integers(len(e)))], c[int(rng.integers(len(c)))], x[int(rng.integers(len(x)))]
        d = ref_filter(m, e, c, x)
        at, _ = run(month=m, ente=e, cat=c, esito=x)
        n += 1
        t = df_with(at, "Esito verifica")
        got_rows = 0 if t is None else len(t)
        if metrics_of(at) != ref_expected_metrics(d) or got_rows != len(d):
            errs.append(f"{m}/{e}/{c}/{x}: atteso {len(d)} righe {ref_expected_metrics(d)}; ottenuto {got_rows} {metrics_of(at)}")
    record("TC-13", "14 combinazioni pseudo-casuali (seed 24) di mese/ente/categoria/esito: righe e indicatori = pandas",
           f"combinazioni={n}; errori={len(errs)}")
    assert_none(errs)


def empty_combo():
    r = DF.iloc[0]
    esito = "Conforme" if r["giacenza_pezzi"] < r["quantita_minima_richiesta"] else "Sotto soglia"
    return r["mese_riferimento"], r["id_ente"], r["categoria_panflu"], esito


def test_tc_14_selezione_vuota():
    m, e, c, x = empty_combo()
    assert len(ref_filter(m, e, c, x)) == 0
    at, dl = run(month=m, ente=e, cat=c, esito=x)
    infos = [i.value for i in at.info]
    got = metrics_of(at)
    record("TC-14", "nessuna eccezione; messaggio 'Nessun record corrisponde ai filtri selezionati.'; nessuna tabella; nessun pulsante download; indicatori = 0; 7 grafici (nessun grafico del tab Monitoraggio)",
           f"eccezioni={len(at.exception)}; info={infos}; tabella_esito={df_with(at,'Esito verifica') is not None}; download={dl is not None}; indicatori={got}; grafici={len(at.get('plotly_chart'))}")
    assert not at.exception
    assert "Nessun record corrisponde ai filtri selezionati." in infos
    assert df_with(at, "Esito verifica") is None and dl is None
    assert got == {k: 0 for k in got}
    assert len(at.get("plotly_chart")) == 7


def test_tc_15_indicatori_su_filtrati():
    at, _ = run(month="2024-06", ente="ASST Demo Est", cat="GUANTI")
    d = ref_filter("2024-06", "ASST Demo Est", "GUANTI")
    exp = ref_expected_metrics(d)
    got = metrics_of(at)
    record("TC-15", f"indicatori sul solo record filtrato: {exp}", f"{got}")
    assert got == exp and len(d) == 1


# ============================================================================ DOWNLOAD
def test_tc_16_download_csv():
    combos = [dict(), dict(esito="Sotto soglia"), dict(ente="AREU", cat="CALZARI"), dict(month="2024-03", cat="GUANTI", esito="Conforme"),
              dict(month="2025-06", ente="IRCCS Demo")]
    errs = []
    for kw in combos:
        at, dl = run(**kw)
        if dl is None:
            errs.append(f"{kw}: nessun download")
            continue
        raw = dl["data"]
        csv = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig")
        shown = df_with(at, "Esito verifica").reset_index(drop=True)
        d = ref_filter(kw.get("month", "2025-12"), kw.get("ente"), kw.get("cat"), kw.get("esito"))
        if not raw.startswith(b"\xef\xbb\xbf"):
            errs.append(f"{kw}: BOM assente")
        if dl.get("file_name") != "monitoraggio_scorte_panflu.csv" or dl.get("mime") != "text/csv":
            errs.append(f"{kw}: nome/mime {dl.get('file_name')} {dl.get('mime')}")
        try:
            pd.testing.assert_frame_equal(csv, shown, check_dtype=False)
        except AssertionError as ex:
            errs.append(f"{kw}: CSV != tabella mostrata ({str(ex)[:80]})")
        if len(csv) != len(d) or int(csv["Giacenza in magazzino"].sum()) != int(d["giacenza_pezzi"].sum()):
            errs.append(f"{kw}: CSV != pandas")
    record("TC-16", "5 scenari: CSV scaricato = tabella filtrata mostrata = filtro pandas; UTF-8 con BOM; nome 'monitoraggio_scorte_panflu.csv'; mime text/csv",
           f"scenari={len(combos)}; errori={len(errs)}")
    assert_none(errs)


# ============================================================================ GRAFICI / TAB TEMPORALE
def test_tc_17_selettore_indicatore_e_grafici():
    errs = []
    for r in ["Consumi", "Giacenze", "Scorte scadute", "Quantità minima richiesta"]:
        at, _ = run(radio=r, ente="AREU", cat="GUANTI")
        if at.exception or len(at.get("plotly_chart")) != 10:
            errs.append(f"{r}: eccezioni={len(at.exception)} grafici={len(at.get('plotly_chart'))}")
    at, _ = run()
    opts = list(at.radio[0].options)
    record("TC-17", "4 opzioni indicatore ['Consumi','Giacenze','Scorte scadute','Quantità minima richiesta']; ogni opzione: nessuna eccezione, 10 grafici",
           f"opzioni={opts}; errori={len(errs)}")
    assert opts == ["Consumi", "Giacenze", "Scorte scadute", "Quantità minima richiesta"]
    assert_none(errs)


# ============================================================================ PREVISIONI
def test_tc_18_metriche_tutte_categorie():
    errs = []
    for c in CATS:
        at, _ = run(cat=c)
        r = ref_forecast(c)
        mt = df_with(at, "Metodo").set_index("Metodo")
        for nome, ref in (("Media mobile semplice", r["ma"]), ("Regressione lineare", r["lin"])):
            got = mt.loc[nome, ["MAE", "RMSE", "MAPE (%)"]].to_numpy(float)
            if not np.allclose(got, np.round(ref, 2), atol=0.011):
                errs.append(f"{c}/{nome}: atteso {np.round(ref,2)} ottenuto {got}")
        if f"{r['best']}." not in at.success[0].value:
            errs.append(f"{c}: metodo atteso {r['best']}, messaggio {at.success[0].value}")
    g = ref_forecast("GUANTI")
    record("TC-18", "per 6 categorie (parametri default): MAE/RMSE/MAPE di media mobile e regressione lineare = ricalcolo indipendente (holdout 4 mesi); es. GUANTI MM RMSE "
           f"{g['ma'][1]:.2f}, LIN RMSE {g['lin'][1]:.2f}, metodo {g['best']}", f"errori={len(errs)}")
    assert_none(errs)


def test_tc_19_scelta_metodo_rmse():
    errs = []
    visti = set()
    for c in CATS:
        for var, trend in ((0.5, -30), (1.0, 0), (2.0, 30)):
            at, _ = run(cat=c, var=var, trend=trend)
            mt = df_with(at, "Metodo").set_index("Metodo")
            migliore = mt["RMSE"].idxmin()
            visti.add(migliore)
            if f"{migliore}." not in at.success[0].value:
                errs.append(f"{c} v={var} t={trend}: RMSE min = {migliore}, ma messaggio '{at.success[0].value}'")
            if ref_forecast(c, var=var, trend=trend)["best"] != migliore:
                errs.append(f"{c} v={var} t={trend}: riferimento != dashboard")
    record("TC-19", "18 scenari (6 categorie x 3): il metodo indicato e' quello con RMSE minore e coincide col riferimento",
           f"errori={len(errs)}; metodi scelti osservati={sorted(visti)}")
    assert_none(errs)


def test_tc_20_orizzonte():
    errs = []
    for h in range(1, 7):
        at, _ = run(cat="GUANTI", horizon=h)
        p = df_with(at, "Mese previsto")
        r = ref_forecast("GUANTI", horizon=h)
        mesi = [str(x.date())[:7] for x in pd.date_range("2026-01-01", periods=h, freq="MS")]
        if list(p["Mese previsto"]) != mesi:
            errs.append(f"h={h}: mesi {list(p['Mese previsto'])} != {mesi}")
        if list(p["Consumo previsto (pezzi)"]) != list(np.round(r["future"]).astype(int)):
            errs.append(f"h={h}: valori {list(p['Consumo previsto (pezzi)'])} != {list(np.round(r['future']).astype(int))}")
    r3 = list(np.round(ref_forecast("GUANTI", horizon=3)["future"]).astype(int))
    record("TC-20", f"orizzonte 1..6: tabella con h righe, mesi consecutivi da 2026-01, valori = riferimento; GUANTI h=3: {r3}", f"errori={len(errs)}")
    assert_none(errs)


def test_tc_21_finestra_media_mobile():
    errs = []
    esiti = {}
    for w in range(2, 7):
        at, _ = run(cat="GUANTI", window=w)
        r = ref_forecast("GUANTI", window=w)
        mt = df_with(at, "Metodo").set_index("Metodo")
        esiti[w] = round(float(mt.loc["Media mobile semplice", "RMSE"]), 2)
        if abs(esiti[w] - round(r["ma"][1], 2)) > 0.011:
            errs.append(f"w={w}: RMSE MM {esiti[w]} atteso {r['ma'][1]:.2f}")
        p = df_with(at, "Mese previsto")["Consumo previsto (pezzi)"].tolist()
        if p != list(np.round(r["future"]).astype(int)):
            errs.append(f"w={w}: previsioni {p}")
    record("TC-21", "finestra 2..6: RMSE della media mobile e previsioni = riferimento (GUANTI); RMSE MM varia con la finestra",
           f"RMSE MM per finestra={esiti}; errori={len(errs)}")
    assert len(set(esiti.values())) > 1
    assert_none(errs)


def test_tc_22_valori_limite_slider():
    errs = []
    n = 0
    for var, trend in itertools.product((0.5, 2.0), (-30, 30)):
        for h, w in ((1, 2), (6, 6)):
            at, _ = run(cat="CAMICI CHIRURGICI", horizon=h, window=w, var=var, trend=trend)
            r = ref_forecast("CAMICI CHIRURGICI", horizon=h, window=w, var=var, trend=trend)
            n += 1
            mt = df_with(at, "Metodo").set_index("Metodo")
            p = df_with(at, "Mese previsto")["Consumo previsto (pezzi)"].tolist()
            if at.exception or p != list(np.round(r["future"]).astype(int)):
                errs.append(f"v={var} t={trend} h={h} w={w}: eccezioni={len(at.exception)} previsioni {p} atteso {list(np.round(r['future']).astype(int))}")
            if not np.allclose(mt.loc["Regressione lineare", ["MAE", "RMSE"]].to_numpy(float), np.round(r["lin"][:2], 2), atol=0.011):
                errs.append(f"v={var} t={trend}: metriche LIN diverse")
            if (np.array(p) < 0).any():
                errs.append("previsione negativa")
    record("TC-22", "estremi degli slider (variabilita 0,5/2,0; variazione -30/+30; orizzonte 1/6; finestra 2/6): nessuna eccezione, previsioni >= 0 e = riferimento",
           f"combinazioni={n}; errori={len(errs)}")
    assert_none(errs)


def test_tc_23_variabilita_e_trend_effetto():
    base = ref_forecast("GUANTI")
    at0, _ = run(cat="GUANTI")
    at1, _ = run(cat="GUANTI", trend=30)
    at2, _ = run(cat="GUANTI", var=2.0)
    p0 = df_with(at0, "Mese previsto")["Consumo previsto (pezzi)"].tolist()
    p1 = df_with(at1, "Mese previsto")["Consumo previsto (pezzi)"].tolist()
    m0 = df_with(at0, "Metodo")["RMSE"].tolist()
    m2 = df_with(at2, "Metodo")["RMSE"].tolist()
    record("TC-23", "variazione +30% modifica le previsioni; variabilita 2,0 modifica le metriche di errore",
           f"previsioni base {p0} vs +30%: {p1}; RMSE base {m0} vs var 2,0: {m2}")
    assert p0 != p1
    assert m0 != m2


# ---- test unitari sulle funzioni dell'app (estratte via AST, senza eseguire Streamlit)
def test_tc_24_funzioni_previsione_unitari():
    f = load_app_functions()
    errs = []

    def chk(nome, got, exp):
        if not np.allclose(got, exp, equal_nan=True):
            errs.append(f"{nome}: atteso {exp} ottenuto {got}")

    chk("MM [1,2,3] h1 w3", f["moving_average_forecast"]([1, 2, 3], 1, 3), [2.0])
    chk("MM ricorsiva [1,2,3] h2 w3", f["moving_average_forecast"]([1, 2, 3], 2, 3), [2.0, 7 / 3])
    chk("MM finestra > serie", f["moving_average_forecast"]([4, 6], 1, 5), [5.0])
    chk("MM serie vuota", f["moving_average_forecast"]([], 2, 3), [0.0, 0.0])
    chk("MM valori negativi -> 0", f["moving_average_forecast"]([-5, -5], 1, 2), [0.0])
    chk("LIN retta y=2x+1", f["linear_forecast"]([1, 3, 5, 7], 2), [9.0, 11.0])
    chk("LIN serie 1 punto", f["linear_forecast"]([5], 3), [5.0, 5.0, 5.0])
    chk("LIN serie vuota", f["linear_forecast"]([], 2), [0.0, 0.0])
    chk("LIN trend decrescente clamp a 0", f["linear_forecast"]([6, 4, 2], 3), [0.0, 0.0, 0.0])
    chk("metriche esatte", [f["error_metrics"]([100, 200], [110, 180])[k] for k in ("MAE", "RMSE", "MAPE (%)")],
        [15.0, math.sqrt(250), 10.0])
    chk("metriche previsione perfetta", [f["error_metrics"]([5, 7], [5, 7])[k] for k in ("MAE", "RMSE", "MAPE (%)")], [0, 0, 0])
    record("TC-24", "MM [1,2,3] h1 = 2; MM ricorsiva; LIN su retta = 9, 11; clamp a 0; metriche MAE 15, RMSE 15,81, MAPE 10 per ([100,200],[110,180])",
           f"errori={len(errs)}")
    assert_none(errs)


def test_tc_25_casi_limite_mape_serie_corta():
    f = f_ = load_app_functions()
    em = f["error_metrics"]
    tutti_zero = em([0, 0], [1, 2])
    parz = em([0, 100], [5, 110])
    corta_ma = f["moving_average_forecast"]([10], 2, 3)
    corta_li = f["linear_forecast"]([10, 20], 2)
    record("TC-25", "MAPE con tutti i reali = 0 -> NaN (no divisione per zero, no eccezione); con un reale = 0 viene escluso (MAPE 10); serie di 1-2 punti gestite senza eccezioni; MAE/RMSE finiti",
           f"tutti zero: MAPE={tutti_zero['MAPE (%)']}, MAE={tutti_zero['MAE']}; parziale: MAPE={parz['MAPE (%)']}; MM serie 1 punto={corta_ma}; LIN 2 punti={corta_li}")
    assert math.isnan(tutti_zero["MAPE (%)"]) and tutti_zero["MAE"] == 1.5
    assert parz["MAPE (%)"] == pytest.approx(10.0)
    assert list(corta_ma) == [10.0, 10.0] and list(corta_li) == pytest.approx([30.0, 40.0])


def test_tc_26_holdout_cronologico():
    f = load_app_functions()
    atteso = {n: min(4, max(2, n // 5)) for n in (6, 10, 14, 20, 24, 40)}
    assert atteso == {6: 2, 10: 2, 14: 2, 20: 4, 24: 4, 40: 4}
    at, _ = run(cat="DISINFETTANTI", ente="ATS Demo Sud", var=1.0)
    r = ref_forecast("DISINFETTANTI", "ATS Demo Sud")
    mt = df_with(at, "Metodo").set_index("Metodo")
    # se l'holdout fosse diverso (es. 2 mesi) i valori differirebbero dal riferimento a 4 mesi
    ys = ref_scenario(ref_series("DISINFETTANTI", "ATS Demo Sud"), 0, 1.0)
    alt = ref_err(ys[-2:], ref_ma(ys[:-2], 2, 3))
    got = float(mt.loc["Media mobile semplice", "RMSE"])
    record("TC-26", "holdout = min(4, max(2, n//5)): n=24 -> 4 mesi finali; RMSE MM del riferimento a 4 mesi coincide con la dashboard (e differisce da quello a 2 mesi)",
           f"test_n(24)={r['test_n']}; RMSE dashboard={got}; RMSE rif. 4 mesi={r['ma'][1]:.2f}; RMSE rif. 2 mesi={alt[1]:.2f}")
    assert r["test_n"] == 4
    assert abs(got - round(r["ma"][1], 2)) <= 0.011 and abs(got - round(alt[1], 2)) > 0.011


# ============================================================================ COMPONENTI DI SCORTA
def test_tc_27_componenti_guanti_default():
    at, _ = run(cat="GUANTI")
    exp = ref_components("GUANTI")
    got = comps_of(at)
    errs = [f"{k}: atteso {v:.1f} ottenuto {got[k]}" for k, v in exp.items() if abs(got[k] - round(v, 1)) > 0.051]
    record("TC-27", "GUANTI, lead 30, livello 0,95, variabilita 1,0, orizzonte 3, finestra 3: " + ", ".join(f"{k} {v:,.1f}" for k, v in exp.items()),
           ", ".join(f"{k} {v:,.1f}" for k, v in got.items()))
    assert_none(errs)


def test_tc_28_componenti_tutte_categorie_enti():
    errs = []
    n = 0
    for c in CATS:
        for e in (None, "ATS Demo Nord", "AREU"):
            at, _ = run(cat=c, ente=e, lead=60, svc=0.99, var=1.5)
            exp = ref_components(c, e, lead=60, svc=0.99, var=1.5)
            got = comps_of(at)
            n += 1
            for k, v in exp.items():
                if abs(got[k] - round(v, 1)) > 0.051:
                    errs.append(f"{c}/{e}/{k}: atteso {v:.1f} ottenuto {got[k]}")
    record("TC-28", "6 categorie x 3 selezioni ente (tutti, ATS Demo Nord, AREU) con lead 60, livello 0,99, variabilita 1,5: 4 componenti = formule di riferimento",
           f"casi={n}; errori={len(errs)}")
    assert_none(errs)


def test_tc_29_monotonia_lead_time():
    leads = list(range(7, 121, 7))
    serie = {k: [] for k in ("Ciclica", "Sicurezza", "Anticipata", "Pipeline")}
    for L in leads:
        at, _ = run(cat="GUANTI", lead=L)
        for k, v in comps_of(at).items():
            serie[k].append(v)
    errs = []
    for k in ("Sicurezza", "Pipeline"):
        if not all(b > a for a, b in zip(serie[k], serie[k][1:])):
            errs.append(f"{k} non strettamente crescente")
    if len(set(serie["Ciclica"])) != 1:
        errs.append("Ciclica dipende dal lead time")
    if not all(b >= a for a, b in zip(serie["Anticipata"], serie["Anticipata"][1:])):
        errs.append("Anticipata non crescente")
    record("TC-29", "lead time 7..119 (passo 7) e 120: Sicurezza e Pipeline strettamente crescenti; Ciclica costante; Anticipata non decrescente",
           f"lead(7,120): sicurezza {serie['Sicurezza'][0]}->{serie['Sicurezza'][-1]}; pipeline {serie['Pipeline'][0]}->{serie['Pipeline'][-1]}; ciclica {set(serie['Ciclica'])}; anticipata {serie['Anticipata'][0]}->{serie['Anticipata'][-1]}; errori={len(errs)}")
    assert_none(errs)


def test_tc_30_monotonia_livello_servizio():
    s = {}
    altri = {}
    for lv in (0.90, 0.95, 0.975, 0.99):
        at, _ = run(cat="GUANTI", svc=lv)
        c = comps_of(at)
        s[lv] = c["Sicurezza"]
        altri[lv] = (c["Ciclica"], c["Anticipata"], c["Pipeline"])
    v = list(s.values())
    rapporto = s[0.99] / s[0.90]
    record("TC-30", "Sicurezza strettamente crescente con il livello di servizio (rapporto 0,99/0,90 = 2,326/1,282 = 1,814); altre componenti invariate",
           f"sicurezza={s}; rapporto={rapporto:.3f}; altre invariate={len(set(altri.values())) == 1}")
    assert all(b > a for a, b in zip(v, v[1:]))
    assert rapporto == pytest.approx(2.326 / 1.282, rel=0.002)
    assert len(set(altri.values())) == 1


def test_tc_31_effetto_variabilita_su_scorte():
    vals = {}
    for var in (0.5, 1.0, 2.0):
        at, _ = run(cat="GUANTI", var=var)
        vals[var] = comps_of(at)
    ok_prop = vals[2.0]["Sicurezza"] == pytest.approx(4 * vals[0.5]["Sicurezza"], rel=0.002)
    altre = all(vals[v][k] == vals[1.0][k] for v in vals for k in ("Ciclica", "Anticipata", "Pipeline"))
    record("TC-31", "variabilita 0,5/1,0/2,0: Sicurezza proporzionale (2,0 = 4 x 0,5); altre componenti invariate",
           f"sicurezza={[vals[v]['Sicurezza'] for v in vals]}; proporzionale={ok_prop}; altre invariate={altre}")
    assert ok_prop and altre


def test_tc_32_formule_pipeline_ciclica():
    errs = []
    for c in CATS:
        at, _ = run(cat=c, lead=45)
        g = comps_of(at)
        dm = pd.Series(ref_series(c)).tail(6).mean() / 30.4375
        if abs(g["Pipeline"] - round(dm * 45, 1)) > 0.051 or abs(g["Ciclica"] - round(dm * 15, 1)) > 0.051:
            errs.append(f"{c}: pipeline {g['Pipeline']} ciclica {g['Ciclica']}")
        if min(g.values()) < 0:
            errs.append(f"{c}: componente negativa")
    record("TC-32", "per ogni categoria (lead 45): Pipeline = domanda media giornaliera (ultimi 6 mesi/30,4375) x 45; Ciclica = domanda giornaliera x 15; nessuna componente negativa",
           f"errori={len(errs)}")
    assert_none(errs)


def test_tc_33_sweep_robustezza():
    errs = []
    n = 0
    t0 = time.time()
    for i, (h, w, v, t, L) in enumerate(itertools.product((1, 6), (2, 6), (0.5, 2.0), (-30, 30), (7, 120))):
        svc = (0.90, 0.95, 0.975, 0.99)[i % 4]
        cat = CATS[i % 6]
        at, _ = run(cat=cat, horizon=h, window=w, var=v, trend=t, lead=L, svc=svc)
        n += 1
        if at.exception:
            errs.append(f"{(h, w, v, t, L, svc, cat)}: {at.exception[0].value}")
            continue
        c = comps_of(at)
        if any(not np.isfinite(x) or x < 0 for x in c.values()):
            errs.append(f"{(h, w, v, t, L, svc, cat)}: componenti non valide {c}")
    record("TC-33", "32 combinazioni degli estremi di tutti gli slider (con livello di servizio e categoria ruotati): nessuna eccezione, componenti finite e >= 0",
           f"combinazioni={n}; errori={len(errs)}; durata {time.time()-t0:.0f} s")
    assert n == 32
    assert_none(errs)


# ============================================================================ CASI LIMITE SU FILE
def _copy_app(tmp_path):
    shutil.copy(APP, tmp_path / "app.py")
    (tmp_path / "data").mkdir()
    for name in ("monitoraggio_panflu_demo.csv", "domanda_storica.csv", "parametri_scorte.csv"):
        shutil.copy(DATA / name, tmp_path / "data" / name)
    return tmp_path / "app.py"


def run_broken(tmp_path, tag, fname, mutate=None, raw=None, delete=False):
    """Copia l'app in una cartella temporanea, altera un CSV e restituisce l'AppTest eseguito."""
    d = tmp_path / tag
    d.mkdir()
    p = _copy_app(d)
    target = d / "data" / fname
    if delete:
        target.unlink()
    elif raw is not None:
        target.write_bytes(raw)
    elif mutate is not None:
        mutate(pd.read_csv(DATA / fname)).to_csv(target, index=False)
    return AppTest.from_file(str(p), default_timeout=60).run()


def assert_guided_error(at, *fragments):
    """Errore guidato: nessuna eccezione, un solo st.error con i frammenti attesi, nessuna scheda mostrata."""
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.error) == 1, f"st.error attesi 1, ottenuti {len(at.error)}"
    msg = at.error[0].value
    for fr in fragments:
        assert fr in msg, f"'{fr}' non trovato in: {msg}"
    assert len(at.tabs) == 0
    return msg


def test_tc_34_csv_mancante_o_colonne_mancanti(tmp_path):
    mon = "monitoraggio_panflu_demo.csv"
    msgs = {}
    at = run_broken(tmp_path, "a", mon, delete=True)
    msgs["file mancante"] = assert_guided_error(at, "File mancante", f"data/{mon}")
    at = run_broken(tmp_path, "b", mon, mutate=lambda d: d.drop(columns=["giacenza_pezzi"]))
    msgs["colonna mancante"] = assert_guided_error(at, "Colonne mancanti", "giacenza_pezzi")
    at = run_broken(tmp_path, "c", mon, mutate=lambda d: d.head(0))
    msgs["CSV vuoto"] = assert_guided_error(at, "non contiene righe di dati", mon)
    record("TC-34", "file monitoraggio mancante, colonna giacenza_pezzi mancante, solo intestazione: st.error guidato in italiano, nessuna eccezione, nessuna scheda",
           "; ".join(f"{k}: {v[:90]}" for k, v in msgs.items()))


def test_tc_35_file_ausiliari_usati_dall_app():
    src = Path(APP).read_text(encoding="utf-8")
    readme = (APP_DIR / "README.md").read_text(encoding="utf-8")
    usa_dom = "domanda_storica" in src
    usa_par = "parametri_scorte" in src
    doc = "domanda_storica.csv" in readme and "parametri_scorte.csv" in readme
    record("TC-35", "tracciabilita' dati: l'app usa domanda_storica.csv e parametri_scorte.csv presenti in data/ e il README li documenta",
           f"app.py cita domanda_storica={usa_dom}; parametri_scorte={usa_par}; README li documenta={doc}")
    assert usa_dom and usa_par and doc


# ============================================================================ REQUISITI DELLA TRACCIA
def test_tc_36_almeno_quattro_serie_e_due_metodi():
    at, _ = run()
    metodi = df_with(at, "Metodo")["Metodo"].tolist()
    # serie con andamenti differenti: pendenza della regressione per categoria
    pend = {c: round(float(np.polyfit(np.arange(24), ref_series(c), 1)[0]), 1) for c in CATS}
    record("TC-36", ">= 4 serie storiche di consumo (6 categorie) con andamenti differenti; >= 2 metodi previsionali confrontati con indicatori d'errore",
           f"categorie={len(CATS)}; metodi={metodi}; pendenza mensile per categoria={pend}")
    assert len(CATS) >= 4 and len(metodi) >= 2
    assert len(set(np.sign(list(pend.values())))) >= 1 and len(set(pend.values())) >= 4


def test_tc_37_controlli_scenario_richiesti():
    at, _ = run()
    labels = [s.label for s in at.sidebar.slider] + [s.label for s in at.sidebar.select_slider]
    testo = " ".join(labels).lower()
    ok = {"variabilita": "variabilit" in testo, "trend": "variazione" in testo or "trend" in testo,
          "lead time": "lead" in testo, "stagionalita": "stagional" in testo}
    record("TC-37", "traccia: la dashboard consente di modificare variabilita, trend, stagionalita e lead time (esempi indicati dalla traccia)",
           f"controlli presenti: {ok}; etichette={labels}")
    assert all(ok.values())


def test_tc_38_trend_influenza_scorte():
    a, _ = run(cat="GUANTI", trend=0)
    b, _ = run(cat="GUANTI", trend=30)
    ca, cb = comps_of(a), comps_of(b)
    record("TC-38", "traccia: gli effetti delle caratteristiche della domanda (trend) sono mostrati anche sulle diverse tipologie di scorte: con +30% almeno una componente dovrebbe cambiare",
           f"trend 0%: {ca}; trend +30%: {cb}; identiche={ca == cb}")
    assert ca != cb


# ============================================================================ NON FUNZIONALI
def test_tc_39_tempo_di_caricamento():
    tempi = []
    for _ in range(3):
        t0 = time.perf_counter()
        at = AppTest.from_file(APP, default_timeout=60).run()
        tempi.append(time.perf_counter() - t0)
        assert not at.exception
    record("TC-39", "esecuzione completa dello script con parametri default in <= 10 s (AppTest, esclusa l'apertura del browser)",
           "tempi (s): " + ", ".join(f"{x:.2f}" for x in tempi) + f"; massimo {max(tempi):.2f}")
    assert max(tempi) <= 10


def test_tc_40_avvio_server_headless():
    py = sys.executable
    port = 8503
    proc = subprocess.Popen([py, "-m", "streamlit", "run", APP, "--server.port", str(port), "--server.headless", "true",
                             "--browser.gatherUsageStats", "false"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(APP_DIR))
    health, home, elapsed = None, None, None
    t0 = time.time()
    try:
        while time.time() - t0 < 40:
            try:
                health = urllib.request.urlopen(f"http://localhost:{port}/_stcore/health", timeout=2).read().decode()
                home = urllib.request.urlopen(f"http://localhost:{port}/", timeout=2).status
                elapsed = time.time() - t0
                break
            except Exception:
                time.sleep(0.5)
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    record("TC-40", "avvio con 'streamlit run' su porta 8503: endpoint /_stcore/health = 'ok' e pagina principale HTTP 200 entro 40 s; server poi arrestato",
           f"health={health!r}; http={home}; tempo di avvio={elapsed if elapsed is None else round(elapsed, 1)} s")
    assert health == "ok" and home == 200


def test_tc_41_stabilita_ripetizione():
    r1, _ = run(cat="GUANTI", ente="AREU", month="2025-06")
    r2, _ = run(cat="GUANTI", ente="AREU", month="2025-06")
    same = (metrics_of(r1) == metrics_of(r2) and df_with(r1, "Metodo").equals(df_with(r2, "Metodo"))
            and df_with(r1, "Componente").equals(df_with(r2, "Componente")))
    record("TC-41", "due esecuzioni identiche producono indicatori, metriche e componenti identici (determinismo)", f"identici={same}")
    assert same


# ============================================================================ v1.1: STAGIONALITA', SCENARIO, ARTICOLI, VALIDAZIONE
def pred_of(at):
    return df_with(at, "Mese previsto")["Consumo previsto (pezzi)"].tolist()


def check_forecast(at, r, errs, tag):
    mt = df_with(at, "Metodo").set_index("Metodo")
    for nome, ref in (("Media mobile semplice", r["ma"]), ("Regressione lineare", r["lin"])):
        got = mt.loc[nome, ["MAE", "RMSE", "MAPE (%)"]].to_numpy(float)
        if not np.allclose(got, np.round(ref, 2), atol=0.011):
            errs.append(f"{tag}/{nome}: atteso {np.round(ref, 2)} ottenuto {got}")
    if f"{r['best']}." not in at.success[0].value:
        errs.append(f"{tag}: metodo atteso {r['best']}, messaggio {at.success[0].value}")
    exp = list(np.round(r["future"]).astype(int))
    if pred_of(at) != exp:
        errs.append(f"{tag}: previsioni {pred_of(at)} atteso {exp}")


def check_components(got, exp, errs, tag):
    for k, v in exp.items():
        if abs(got[k] - round(v, 1)) > 0.051:
            errs.append(f"{tag}/{k}: atteso {v:.1f} ottenuto {got[k]}")


def test_tc_42_indici_stagionali():
    f = load_app_functions()
    errs = []
    for c in CATS:
        got = f["seasonal_indices"](ref_series(c), CAT_MONTHS)
        ref = ref_seasonal_indices(ref_series(c), CAT_MONTHS)
        if len(got) != 12 or abs(got.mean() - 1) > 1e-9 or not np.allclose(got, ref, atol=1e-9):
            errs.append(f"{c}: indici app != riferimento")
    for a in ARTS:
        sub = DEM[DEM["articolo"] == a].sort_values("data")
        mesi = pd.to_datetime(sub["data"]).dt.month.to_numpy()
        got = f["seasonal_indices"](sub["domanda"].to_numpy(float), mesi)
        ref = ref_seasonal_indices(sub["domanda"].to_numpy(float), mesi)
        if abs(got.mean() - 1) > 1e-9 or not np.allclose(got, ref, atol=1e-9):
            errs.append(f"{a}: indici app != riferimento")
    # tabella mostrata dall'app (expander) = riferimento; a intensita' 0 il fattore e' 1,0 per tutti i mesi
    for c in CATS:
        at, _ = run(cat=c)
        t = df_with(at, "Indice stagionale stimato")
        ref = ref_seasonal_indices(ref_series(c), CAT_MONTHS)
        if len(t) != 12 or not np.allclose(t["Indice stagionale stimato"], np.round(ref, 3), atol=0.0011):
            errs.append(f"{c}: tabella indici != riferimento")
        if not (t["Fattore applicato (intensità)"] == 1.0).all():
            errs.append(f"{c}: fattore a intensita' 0 non neutro")
    at, _ = run(cat="GUANTI", season=1.0)
    t = df_with(at, "Indice stagionale stimato")
    if not np.allclose(t["Fattore applicato (intensità)"], t["Indice stagionale stimato"], atol=0.0011):
        errs.append("a intensita' 1 il fattore deve coincidere con l'indice")
    g = ref_seasonal_indices(ref_series("GUANTI"), CAT_MONTHS)
    # default neutro: previsioni e componenti GUANTI = riferimenti di TC-18/27
    at0, _ = run(cat="GUANTI")
    check_forecast(at0, ref_forecast("GUANTI"), errs, "GUANTI default")
    check_components(comps_of(at0), ref_components("GUANTI"), errs, "GUANTI default")
    record("TC-42", "indici stagionali di 6 categorie e 4 articoli: 12 valori, media 1, = riferimento indipendente; tabella dell'app = riferimento; intensita' 0 -> fattore 1,0 e risultati = default (TC-18/27)",
           f"errori={len(errs)}; indici GUANTI={np.round(g, 3).tolist()}")
    assert_none(errs)


def test_tc_43_stagionalita_su_previsioni():
    errs = []
    n = 0
    for c in CATS:
        for s in (0.5, 1.0):
            at, _ = run(cat=c, season=s)
            check_forecast(at, ref_forecast(c, season=s), errs, f"{c} s={s}")
            n += 1
    at, _ = run(cat="GUANTI", season=0.7, var=1.5, trend=20, horizon=5, window=4)
    check_forecast(at, ref_forecast("GUANTI", season=0.7, var=1.5, trend=20, horizon=5, window=4), errs, "GUANTI scenario misto")
    at, _ = run(cat="DISINFETTANTI", ente="AREU", season=1.0, trend=-30, horizon=6)
    check_forecast(at, ref_forecast("DISINFETTANTI", "AREU", season=1.0, trend=-30, horizon=6), errs, "DISINFETTANTI/AREU")
    n += 2
    p0 = pred_of(run(cat="GUANTI")[0])
    p1 = pred_of(run(cat="GUANTI", season=1.0)[0])
    record("TC-43", "stagionalita' 0,5 e 1,0 su 6 categorie (+2 scenari misti): metriche, metodo e previsioni = riferimento indipendente; con intensita' 1 le previsioni GUANTI differiscono dal default",
           f"scenari={n}; errori={len(errs)}; GUANTI default {p0} vs s=1 {p1}")
    assert p0 != p1
    assert_none(errs)


def test_tc_44_stagionalita_su_componenti():
    errs = []
    cambia = {}
    for c in CATS:
        r = {s: comps_of(run(cat=c, season=s)[0]) for s in (0.0, 0.5, 1.0)}
        for s in (0.5, 1.0):
            check_components(r[s], ref_components(c, season=s), errs, f"{c} s={s}")
        for k in ("Ciclica", "Pipeline"):
            if abs(r[0.5][k] - (r[0.0][k] + r[1.0][k]) / 2) > 0.1:
                errs.append(f"{c}/{k}: non lineare in s ({r[0.0][k]}, {r[0.5][k]}, {r[1.0][k]})")
        cambia[c] = r[0.0] != r[1.0]
    g0 = comps_of(run(cat="GUANTI")[0])
    g1 = comps_of(run(cat="GUANTI", season=1.0)[0])
    record("TC-44", "componenti di scorta con stagionalita' 0,5 e 1,0 su 6 categorie = riferimento; Ciclica e Pipeline lineari in s; con s=1 almeno una componente cambia",
           f"errori={len(errs)}; GUANTI s=0 {g0} -> s=1 {g1}; categorie con componenti modificate={cambia}")
    assert g0 != g1
    assert_none(errs)


def test_tc_45_trend_su_componenti():
    errs = []
    comp = {}
    for t in (-30, 0, 30):
        at, _ = run(cat="GUANTI", trend=t)
        comp[t] = comps_of(at)
        check_components(comp[t], ref_components("GUANTI", trend=t), errs, f"GUANTI trend {t}")
    for c in CATS:
        for t in (-30, 30):
            check_components(comps_of(run(cat=c, trend=t)[0]), ref_components(c, trend=t), errs, f"{c} trend {t}")
    for k in ("Ciclica", "Pipeline"):
        if not comp[-30][k] < comp[0][k] < comp[30][k]:
            errs.append(f"{k}: ordine non monotono {comp[-30][k]}, {comp[0][k]}, {comp[30][k]}")
    # la variabilita' continua a modificare solo la Sicurezza, anche con trend e stagionalita' attivi
    v = {x: comps_of(run(cat="GUANTI", var=x, trend=20, season=0.5)[0]) for x in (0.5, 1.0, 2.0)}
    altre = all(v[x][k] == v[1.0][k] for x in v for k in ("Ciclica", "Anticipata", "Pipeline"))
    prop = v[2.0]["Sicurezza"] == pytest.approx(4 * v[0.5]["Sicurezza"], rel=0.002)
    record("TC-45", "trend -30/0/+30: componenti = riferimento; Ciclica e Pipeline crescenti con il trend; la variabilita' modifica solo la Sicurezza (proporzionale) anche con trend e stagionalita' attivi",
           f"errori={len(errs)}; GUANTI -30%: {comp[-30]}; 0%: {comp[0]}; +30%: {comp[30]}; altre invariate={altre}")
    assert altre and prop
    assert_none(errs)


def art_tables(at):
    return (df_with(at, "Scorta attuale"), df_with(at, "Selezionato"), df_with(at, "Copertura (giorni)"))


def check_articles(at, kw, errs, tag):
    par, met, comp = art_tables(at)
    if par is None or met is None or comp is None:
        errs.append(f"{tag}: tabelle articoli assenti")
        return
    if list(met["Articolo"].unique()) != ARTS or list(comp["Articolo"]) != ARTS or len(met) != 8 or len(comp) != 4:
        errs.append(f"{tag}: articoli/righe inattesi")
        return
    for a in ARTS:
        r = ref_article(a, **kw)
        p = r["p"]
        prow = par[par["Articolo"] == a].iloc[0]
        if (prow["Scorta attuale"], prow["Lead time (giorni)"], prow["Livello di servizio"], prow["Periodo di riordino (giorni)"],
                prow["Costo unitario (EUR)"], prow["Fattore stagionalità"]) != (
                p["scorta_attuale"], p["lead_time_giorni"], p["livello_servizio"], p["periodo_riordino_giorni"],
                p["costo_unitario_eur"], p["mesi_stagionali"]):
            errs.append(f"{tag}/{a}: parametri != CSV")
        for nome, ref in (("Media mobile semplice", r["fc"]["ma"]), ("Regressione lineare", r["fc"]["lin"])):
            row = met[(met["Articolo"] == a) & (met["Metodo"] == nome)].iloc[0]
            if not np.allclose([row["MAE"], row["RMSE"], row["MAPE (%)"]], np.round(ref, 2), atol=0.011):
                errs.append(f"{tag}/{a}/{nome}: metriche {row.tolist()} atteso {np.round(ref, 2)}")
            if (row["Selezionato"] == "sì") != (nome == r["fc"]["best"]):
                errs.append(f"{tag}/{a}/{nome}: flag Selezionato errato")
        row = comp[comp["Articolo"] == a].iloc[0]
        c = r["comp"]
        for k in ("Ciclica", "Sicurezza", "Anticipata", "Pipeline"):
            if abs(row[k] - round(c[k], 1)) > 0.051:
                errs.append(f"{tag}/{a}/{k}: atteso {c[k]:.1f} ottenuto {row[k]}")
        if abs(row["Copertura (giorni)"] - round(c["Copertura"], 1)) > 0.051:
            errs.append(f"{tag}/{a}/copertura: atteso {c['Copertura']:.1f} ottenuto {row['Copertura (giorni)']}")
        if row["Lead time (giorni)"] != p["lead_time_giorni"] or row["Livello di servizio"] != p["livello_servizio"]:
            errs.append(f"{tag}/{a}: lead/livello non da parametri_scorte.csv")


def test_tc_46_vista_quattro_articoli():
    errs = []
    scen = dict(horizon=4, window=4, var=1.5, trend=20, season=0.5)
    at0, _ = run()
    check_articles(at0, {}, errs, "default")
    at1, _ = run(**scen)
    check_articles(at1, dict(horizon=4, window=4, var=1.5, trend=20, season=0.5), errs, "scenario")
    dettagli = {}
    for a in ARTS:
        at, _ = run(art=a, **scen)
        p = df_with(at, "Mese (articolo)")
        exp = list(np.round(ref_article(a, **scen)["fc"]["future"]).astype(int))
        dettagli[a] = p["Domanda prevista (pezzi)"].tolist()
        if dettagli[a] != exp or len(p) != 4:
            errs.append(f"dettaglio {a}: {dettagli[a]} atteso {exp}")
    # lo slider lead time non si applica agli articoli
    atl, _ = run(lead=120)
    for x, y in zip(art_tables(at0), art_tables(atl)):
        if not x.equals(y):
            errs.append("lo slider lead time modifica la vista articoli")
    g = ref_article("Guanti nitrile M")
    record("TC-46", "scheda articoli: parametri, confronto metodi (MAE/RMSE/MAPE, selezionato), componenti (lead e livello da parametri_scorte.csv, copertura) e previsioni di dettaglio = ricalcolo pandas indipendente da domanda_storica.csv e parametri_scorte.csv, in default e in scenario (trend 20, s 0,5, var 1,5, orizzonte 4, finestra 4); slider lead time ininfluente",
           f"errori={len(errs)}; Guanti nitrile M default: RMSE MM {g['fc']['ma'][1]:.2f} / LIN {g['fc']['lin'][1]:.2f}, metodo {g['fc']['best']}, "
           f"componenti { {k: round(v, 1) for k, v in g['comp'].items() if k != 'dm'} }; dettagli scenario={dettagli}")
    assert_none(errs)


def test_tc_47_mesi_stagionali_per_articolo(tmp_path):
    d = tmp_path / "ms"
    d.mkdir()
    p = _copy_app(d)
    par = pd.read_csv(DATA / "parametri_scorte.csv")
    par.loc[par["articolo"] == "Guanti nitrile M", "mesi_stagionali"] = 0.5
    par.loc[par["articolo"] == "Kit medicazione", "mesi_stagionali"] = 0.0
    par.to_csv(d / "data" / "parametri_scorte.csv", index=False)
    at = AppTest.from_file(str(p), default_timeout=120)
    at.run()
    at.sidebar.slider[5].set_value(1.0)
    at.run()
    assert not at.exception
    _, met, comp = art_tables(at)
    base = {s: art_tables(run(season=s)[0]) for s in (0.0, 0.5, 1.0)}
    errs = []
    for art, s in (("Guanti nitrile M", 0.5), ("Kit medicazione", 0.0), ("Mascherine chirurgiche", 1.0), ("Siringhe sterili 5 ml", 1.0)):
        _, bmet, bcomp = base[s]
        m1 = met[met["Articolo"] == art].reset_index(drop=True)
        m2 = bmet[bmet["Articolo"] == art].reset_index(drop=True)
        c1 = comp[comp["Articolo"] == art].reset_index(drop=True)
        c2 = bcomp[bcomp["Articolo"] == art].reset_index(drop=True)
        if not (m1.equals(m2) and c1.equals(c2)):
            errs.append(f"{art}: con mesi_stagionali la vista != app originale a intensita' {s}")
    record("TC-47", "mesi_stagionali come moltiplicatore dell'intensita': slider 1,0 con Guanti 0,5, Kit medicazione 0, altri 1,0 -> Guanti = intensita' 0,5, Kit = intensita' 0, altri = intensita' 1,0 (app con CSV originali)",
           f"errori={len(errs)}")
    assert_none(errs)


def test_tc_48_validazione_file_colonne_vuoto(tmp_path):
    spec = {
        "monitoraggio_panflu_demo.csv": "id_ente",
        "domanda_storica.csv": "domanda",
        "parametri_scorte.csv": "lead_time_giorni",
    }
    errs = []
    n = 0
    for fn, col in spec.items():
        casi = {
            "mancante": (dict(delete=True), ["File mancante", f"data/{fn}"]),
            "colonna": (dict(mutate=lambda d, c=col: d.drop(columns=[c])), ["Colonne mancanti", col, f"data/{fn}"]),
            "solo intestazione": (dict(mutate=lambda d: d.head(0)), ["non contiene righe di dati", f"data/{fn}"]),
            "0 byte": (dict(raw=b""), ["è vuoto", f"data/{fn}"]),
        }
        for nome, (kw, frag) in casi.items():
            n += 1
            try:
                assert_guided_error(run_broken(tmp_path, f"{fn[:4]}{nome[:3]}{n}", fn, **kw), *frag)
            except AssertionError as ex:
                errs.append(f"{fn}/{nome}: {str(ex)[:150]}")
    record("TC-48", "per ciascuno dei 3 CSV: file mancante, colonna mancante, solo intestazione, file a 0 byte -> un solo st.error in italiano con nome file/colonna, nessuna eccezione, nessuna scheda",
           f"casi={n}; errori={len(errs)}")
    assert n == 12
    assert_none(errs)


def test_tc_49_validazione_valori(tmp_path):
    mon, dem, par = "monitoraggio_panflu_demo.csv", "domanda_storica.csv", "parametri_scorte.csv"

    def setv(col, val, row=3):
        def f(d):
            d[col] = d[col].astype(object)
            d.loc[row, col] = val
            return d
        return f

    primo = "Guanti nitrile M"
    casi = [
        ("negativo", mon, setv("consumo_mensile_pezzi", -5), ["consumo_mensile_pezzi", "maggiore o uguale a 0", "riga 5"]),
        ("testo in numerico", mon, setv("giacenza_pezzi", "abc"), ["giacenza_pezzi", "non numerici", "'abc'"]),
        ("mese 2024-13", mon, setv("mese_riferimento", "2024-13"), ["Mese non valido", "2024-13"]),
        ("mese abc", mon, setv("mese_riferimento", "abc"), ["Mese non valido", "abc"]),
        ("duplicato", mon, lambda d: pd.concat([d, d.head(1)], ignore_index=True), ["duplicate", "id_ente"]),
        ("id vuoto", mon, setv("id_ente", ""), ["id_ente", "mancanti"]),
        ("domanda negativa", dem, setv("domanda", -1), ["domanda", "maggiore o uguale a 0"]),
        ("data non valida", dem, setv("data", "2023-13-01"), ["Data non valida", "2023-13-01"]),
        ("duplicato domanda", dem, lambda d: pd.concat([d, d.head(1)], ignore_index=True), ["duplicate", "articolo"]),
        ("serie corta", dem, lambda d: d[~((d["articolo"] == primo) & (d["data"] > "2023-08-01"))], ["almeno 12", primo]),
        ("buco nella serie", dem, lambda d: d.drop(index=d[(d["articolo"] == primo) & (d["data"] == "2024-05-01")].index), ["non continua", primo]),
        ("articoli incoerenti", par, lambda d: d.assign(articolo=d["articolo"].replace({"Kit medicazione": "Kit sutura"})), ["non coincidono", "Kit medicazione", "Kit sutura"]),
        ("livello servizio 1", par, setv("livello_servizio", 1.0, 0), ["livello_servizio", "minori di 1"]),
        ("livello servizio 0", par, setv("livello_servizio", 0.0, 0), ["livello_servizio", "maggiore di 0"]),
        ("lead time 0", par, setv("lead_time_giorni", 0, 1), ["lead_time_giorni", "maggiore di 0"]),
        ("scorta negativa", par, setv("scorta_attuale", -10, 2), ["scorta_attuale", "maggiore o uguale a 0"]),
        ("articolo duplicato", par, lambda d: pd.concat([d, d.head(1)], ignore_index=True), ["duplicate", "articolo"]),
    ]
    errs = []
    for i, (nome, fn, mut, frag) in enumerate(casi):
        try:
            assert_guided_error(run_broken(tmp_path, f"v{i}", fn, mutate=mut), *frag)
        except AssertionError as ex:
            errs.append(f"{nome}: {str(ex)[:160]}")
    record("TC-49", "valori non validi (numero negativo, testo in colonna numerica, mese 2024-13/abc, duplicati, id vuoto, data non valida, serie < 12 mesi, buco nella serie, articoli incoerenti, livello servizio 0/1, lead time 0, scorta negativa): messaggio italiano specifico + stop",
           f"casi={len(casi)}; errori={len(errs)}")
    assert_none(errs)


def test_tc_50_funzioni_nuove_unitari():
    f = load_app_functions()
    errs = []
    prof = np.array([1.2] * 6 + [0.8] * 6)
    t = np.arange(36)
    y = (100 + 2 * t) * prof[t % 12]
    mesi = t % 12 + 1
    idx = f["seasonal_indices"](y, mesi)
    if abs(idx.mean() - 1) > 1e-12 or not (idx[:6] > 1.1).all() or not (idx[6:] < 0.9).all():
        errs.append(f"pattern non recuperato: {np.round(idx, 3)}")
    if not np.array_equal(f["seasonal_indices"](y[:11], mesi[:11]), np.ones(12)):
        errs.append("<12 punti: indici non neutri")
    sf = f["seasonal_factor"]
    if not np.array_equal(sf(idx, [1, 7, 12], 0.0), np.ones(3)):
        errs.append("intensita' 0 non esattamente 1")
    if not np.allclose(sf(idx, [1, 7], 1.0), idx[[0, 6]]) or not np.allclose(sf(idx, [1, 7], 5.0), idx[[0, 6]]) \
            or not np.array_equal(sf(idx, [1, 7], -2.0), np.ones(2)):
        errs.append("intensita' 1 / fuori range non gestita")
    ts = f["trend_series"]
    if not np.allclose(ts([100, 100, 100], 30), [100, 115, 130]) or not np.allclose(ts([100, 100, 100], -30), [100, 85, 70]):
        errs.append("rampa di trend errata")
    if not np.array_equal(ts([10, 10], -200), [10, 0]) and not np.array_equal(ts([10, 10], -200), [10.0, 0.0]):
        errs.append("clamp a 0 della rampa errato")
    z = f["z_score"]
    if [z(0.90), z(0.95), z(0.975), z(0.99)] != [1.282, 1.645, 1.960, 2.326]:
        errs.append("z tabellari errati")
    if abs(z(0.8) - 0.8416) > 0.001 or abs(z(0.999) - 3.0902) > 0.001:
        errs.append(f"fallback z errato: {z(0.8)}, {z(0.999)}")
    # stock_components con s=0 e trend=0 = formula originale su serie nota
    ser = np.array([1000, 1100, 900, 1200, 1300, 1250, 1400, 1350, 1500, 1450, 1600, 1550, 1700, 1650, 1800, 1750, 1900, 1850], float)
    m = np.arange(len(ser)) % 12 + 1
    sc = f["stock_components"](ser, m, [7, 8, 9], 45, 0.95, 1.2, 3, 3, 0, 0.0, np.ones(12))
    s = pd.Series(ser)
    dm = s.tail(6).mean() / 30.4375
    ds = s.tail(12).std(ddof=1) / 30.4375
    fm = np.mean(f["moving_average_forecast"](ser, 3, 3))
    exp = {"Ciclica": dm * 15, "Sicurezza": 1.645 * ds * 1.2 * math.sqrt(45), "Anticipata": max(0, fm - s.tail(3).mean()) * 45 / 30.4375, "Pipeline": dm * 45}
    for k, v in exp.items():
        if not math.isclose(sc[k], v, rel_tol=1e-12):
            errs.append(f"{k}: {sc[k]} != {v}")
    vuoto = f["stock_components"]([], [], [], 30, 0.95, 1.0, 3, 3, 0, 0.0, np.ones(12))
    if any(vuoto[k] != 0.0 for k in ("Ciclica", "Sicurezza", "Anticipata", "Pipeline")):
        errs.append("serie vuota: componenti non nulle")
    # il trend influisce sulle componenti anche a livello di funzione
    up = f["stock_components"](ser, m, [7, 8, 9], 45, 0.95, 1.0, 3, 3, 30, 0.0, np.ones(12))
    if not up["Pipeline"] > sc["Pipeline"]:
        errs.append("trend +30 non aumenta la Pipeline")
    record("TC-50", "funzioni nuove: seasonal_indices recupera il profilo 1,2/0,8 (media 1; <12 punti -> 1), seasonal_factor neutro a 0 e clippato, trend_series (rampa, clamp), z_score (tabella + NormalDist), stock_components = formula originale a s=0/trend=0, serie vuota -> zeri",
           f"errori={len(errs)}; indici recuperati={np.round(idx, 3).tolist()}")
    assert_none(errs)


def test_tc_51_robustezza_nuovi_controlli():
    errs = []
    n = 0
    t0 = time.time()
    for i, (s, t, v, L, hw) in enumerate(itertools.product((0.0, 1.0), (-30, 30), (0.5, 2.0), (7, 120), ((1, 2), (6, 6)))):
        svc = (0.90, 0.95, 0.975, 0.99)[i % 4]
        cat = CATS[i % 6]
        ente = (None, "AREU")[i % 2]
        h, w = hw
        at, _ = run(cat=cat, ente=ente, horizon=h, window=w, var=v, trend=t, lead=L, svc=svc, season=s)
        n += 1
        tag = (s, t, v, L, h, w, svc, cat, ente)
        if at.exception:
            errs.append(f"{tag}: {at.exception[0].value}")
            continue
        c = comps_of(at)
        if any(not np.isfinite(x) or x < 0 for x in c.values()):
            errs.append(f"{tag}: componenti non valide {c}")
        if min(pred_of(at)) < 0 or len(pred_of(at)) != h:
            errs.append(f"{tag}: previsioni non valide {pred_of(at)}")
        par, met, comp = art_tables(at)
        vals = comp.drop(columns=["Articolo"]).to_numpy(float)
        if not np.isfinite(vals).all() or (vals < 0).any() or not np.isfinite(met[["MAE", "RMSE"]].to_numpy(float)).all():
            errs.append(f"{tag}: vista articoli non valida")
        if min(df_with(at, "Mese (articolo)")["Domanda prevista (pezzi)"]) < 0:
            errs.append(f"{tag}: previsione articolo negativa")
    record("TC-51", "32 combinazioni estreme con i nuovi controlli (stagionalita' 0/1, variazione +-30, variabilita 0,5/2, lead 7/120, orizzonte/finestra 1-2/6-6, categorie, enti e livelli ruotati): nessuna eccezione, componenti e vista articoli finite e >= 0, previsioni >= 0",
           f"combinazioni={n}; errori={len(errs)}; durata {time.time()-t0:.0f} s")
    assert n == 32
    assert_none(errs)


def test_tc_52_valori_default_invariati():
    at, _ = run(cat="GUANTI")
    g = at  # indicatori e componenti
    at_all, _ = run()
    m = metrics_of(at_all)
    sotto = int((DF["giacenza_pezzi"] < DF["quantita_minima_richiesta"]).sum())
    mt = df_with(g, "Metodo").set_index("Metodo")
    comp = comps_of(g)
    atd, _ = run(cat="DISINFETTANTI")
    mtd = df_with(atd, "Metodo").set_index("Metodo")
    dec = ref_filter("2025-12")
    ob = {
        "righe": len(DF), "sotto_soglia": sotto, "perc": round(sotto / len(DF) * 100, 1), "scadute_tot": int(DF["scorte_scadute_pezzi"].sum()),
        "dic_sotto": m["Righe sotto soglia"], "dic_righe": len(dec), "scadute_dic": m["Scorte scadute rilevate"],
        "g_rmse_ma": round(float(mt.loc["Media mobile semplice", "RMSE"])), "g_rmse_lin": round(float(mt.loc["Regressione lineare", "RMSE"])),
        "g_mape_ma": round(float(mt.loc["Media mobile semplice", "MAPE (%)"]), 1), "g_mape_lin": round(float(mt.loc["Regressione lineare", "MAPE (%)"]), 1),
        "d_rmse_ma": round(float(mtd.loc["Media mobile semplice", "RMSE"])), "d_rmse_lin": round(float(mtd.loc["Regressione lineare", "RMSE"])),
        "comp": {k: round(v) for k, v in ref_components("GUANTI").items()},
        "titolo": at.title[0].value, "slider_stagionalita": (at.sidebar.slider[5].label, at.sidebar.slider[5].value),
    }
    exp = {
        "righe": 864, "sotto_soglia": 525, "perc": 60.8, "scadute_tot": 47036, "dic_sotto": 24, "dic_righe": 36, "scadute_dic": 1863,
        "g_rmse_ma": 5978, "g_rmse_lin": 10339, "g_mape_ma": 9.2, "g_mape_lin": 16.7, "d_rmse_ma": 447, "d_rmse_lin": 647,
        "comp": {"Ciclica": 31145, "Sicurezza": 2363, "Anticipata": 543, "Pipeline": 62289},
        "titolo": "Monitoraggio delle scorte pandemiche", "slider_stagionalita": ("Intensità stagionalità (0 = neutra)", 0.0),
    }
    record("TC-52", f"valori di default invariati nella v1.1: {exp}", f"{ob}")
    assert ob == exp
    assert all(abs(comp[k] - round(v, 1)) <= 0.051 for k, v in ref_components("GUANTI").items())


def test_tc_53_compatibilita_e_documentazione():
    import importlib.metadata as md
    src = Path(APP).read_text(encoding="utf-8")
    req = [r.strip() for r in (APP_DIR / "requirements.txt").read_text(encoding="utf-8").splitlines() if r.strip()]
    pinned = {r.split("==")[0]: r.split("==")[1] for r in req if "==" in r}
    inst = {k: md.version(k) for k in ("streamlit", "pandas", "numpy", "plotly")}
    readme = (APP_DIR / "README.md").read_text(encoding="utf-8")
    note = (APP_DIR / "NOTE.txt").read_text(encoding="utf-8")
    ok_readme = all(x in readme for x in ("monitoraggio_panflu_demo.csv", "domanda_storica.csv", "parametri_scorte.csv",
                                          "cd acamino_0312501773/PW24_dashboard_sanitario", "3.14", "mesi_stagionali"))
    record("TC-53", "A-05 e documentazione: nessun use_container_width in app.py; requirements.txt con 4 versioni esatte (==) uguali a quelle installate; README con sottocartella di avvio, 3 CSV, versioni testate (3.14); NOTE.txt aggiornata",
           f"use_container_width presente={'use_container_width' in src}; requirements={pinned}; installate={inst}; README ok={ok_readme}")
    assert "use_container_width" not in src
    assert len(req) == 4 and pinned == inst
    assert ok_readme and "PW24_dashboard_sanitario" in note and "domanda_storica" in note
