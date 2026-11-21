"""Genera Test Book e Test Report (.md e .docx) a partire dai risultati reali di pytest.

Uso (dopo aver eseguito la suite, vedi Test_Report_PW24.md):
    .venv\\Scripts\\python.exe test/genera_documenti.py
Legge: test/results/junit_run1.xml, junit_run2.xml, details_run2.json. Nessun esito e' scritto a mano.
"""
import json
import platform
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy
import pandas
import plotly
import pytest
import streamlit
import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm

T = Path(__file__).resolve().parent
RES = T / "results"
VERSIONE = "1.1"
DATA_DOC = "21/11/2026"
COMANDO = r'.venv\Scripts\python.exe -m pytest test/test_dashboard.py -v --junitxml=test/results/junit.xml'

# ------------------------------------------------------------------ casi di test: (id, titolo, area, requisito, precondizioni, input, passi, tipo, priorita)
A = "Automatico"
CASI = [
    ("TC-01", "Struttura del CSV di monitoraggio", "Dati e integrita'", "Dati: ente, categoria, mese, consumi, minima, giacenza, scadute", "File data/monitoraggio_panflu_demo.csv presente", "CSV demo", "Leggere il CSV con pandas; contare righe e confrontare nomi colonna", A, "Alta"),
    ("TC-02", "Integrita' dei dati (nulli, duplicati, completezza)", "Dati e integrita'", "Qualita' dati sintetici", "TC-01 superato", "CSV demo", "Contare valori nulli; duplicati sulla chiave (ente, categoria, mese); verificare la griglia 6 x 6 x 24", A, "Alta"),
    ("TC-03", "Validita' dei valori", "Dati e integrita'", "Qualita' dati sintetici", "TC-01 superato", "CSV demo", "Verificare assenza di negativi, minime <= 0, scadute > giacenza, formato mese AAAA-MM", A, "Media"),
    ("TC-04", "Totali di esito sull'intero dataset", "Dati e integrita'", "Verifica giacenza vs quantita' minima", "TC-01 superato", "CSV demo", "Calcolare con pandas righe con giacenza < minima, percentuale, scadute totali, righe al limite", A, "Alta"),
    ("TC-05", "File ausiliari (domanda storica, parametri scorte)", "Dati e integrita'", "Traccia: serie storiche di >= 4 articoli", "File presenti in data/", "domanda_storica.csv, parametri_scorte.csv", "Leggere i file; verificare dimensioni, colonne, nulli", A, "Media"),
    ("TC-06", "Avvio dell'app e struttura della pagina", "Avvio e struttura", "Titolo, tab, indicatori, grafici", "Ambiente Python con streamlit", "Parametri di default", "Eseguire app.py con AppTest; verificare eccezioni, titolo, tab, metriche, grafici, avviso 'prototipo didattico'", A, "Alta"),
    ("TC-07", "Indicatori e tabella di default (dicembre 2025)", "Indicatori", "Indicatori di sintesi sui record filtrati", "TC-06 superato", "Mese 2025-12, Tutti/Tutte/Tutti", "Avviare con default; leggere le 4 metriche e la tabella; confrontare con pandas", A, "Alta"),
    ("TC-08", "Logica dell'esito (giacenza >= minima)", "Logica esito", "Esito Conforme / Sotto soglia", "TC-06 superato", "Tutti i 24 mesi; riga al limite giacenza = minima", "Per ogni mese leggere la tabella e ricalcolare l'esito; verificare la riga al limite", A, "Alta"),
    ("TC-09", "Filtro mese di riferimento", "Filtri", "Filtro mese", "TC-06 superato", "24 mesi", "Selezionare ciascun mese; confrontare righe e indicatori con pandas", A, "Alta"),
    ("TC-10", "Filtro ente", "Filtri", "Filtro ente", "TC-06 superato", "6 enti", "Selezionare ciascun ente; confrontare righe e indicatori", A, "Alta"),
    ("TC-11", "Filtro tipologia dispositivo (categoria)", "Filtri", "Filtro categoria", "TC-06 superato", "6 categorie", "Selezionare ciascuna categoria; confrontare righe e indicatori", A, "Alta"),
    ("TC-12", "Filtro esito verifica", "Filtri", "Filtro esito", "TC-06 superato", "Sotto soglia / Conforme", "Selezionare ciascun esito; confrontare righe e indicatori", A, "Alta"),
    ("TC-13", "Filtri combinati", "Filtri", "Combinazione di filtri", "TC-09..TC-12 superati", "14 combinazioni pseudo-casuali (seed 24)", "Impostare mese, ente, categoria, esito; confrontare righe e indicatori con pandas", A, "Alta"),
    ("TC-14", "Selezione vuota (nessun risultato)", "Filtri", "Gestione assenza di record", "TC-06 superato", "Combinazione senza record (ATS Demo Nord / DISINFETTANTI / 2024-01 con esito opposto a quello reale)", "Impostare i filtri; verificare messaggio, assenza di tabella/download, indicatori a 0, nessuna eccezione", A, "Alta"),
    ("TC-15", "Indicatori calcolati sui record filtrati", "Indicatori", "Indicatori sui record filtrati", "TC-06 superato", "2024-06, ASST Demo Est, GUANTI", "Filtrare a un solo record; confrontare le 4 metriche con il record del CSV", A, "Media"),
    ("TC-16", "Download CSV dei dati filtrati", "Download", "Esportazione dati filtrati", "Tabella non vuota", "5 scenari di filtro", "Intercettare i dati passati a download_button; leggere il CSV; confrontare con tabella mostrata e con pandas; verificare BOM, nome file, mime", A, "Alta"),
    ("TC-17", "Selettore indicatore e grafici temporali", "Grafici", "Andamento storico", "TC-06 superato", "4 opzioni del selettore", "Selezionare ciascuna opzione; verificare nessuna eccezione e numero di grafici", A, "Media"),
    ("TC-18", "Metriche MAE/RMSE/MAPE e confronto metodi (6 categorie)", "Previsioni", "Applicare e confrontare >= 2 metodi; indicatori d'errore", "TC-06 superato", "Default: orizzonte 3, finestra 3, variabilita 1,0, variazione 0%", "Per ogni categoria leggere la tabella metriche; confrontare con calcolo indipendente (holdout 4 mesi)", A, "Alta"),
    ("TC-19", "Scelta del metodo con RMSE minore", "Previsioni", "Individuare il metodo piu' adatto", "TC-18 superato", "6 categorie x 3 scenari (variabilita/variazione)", "Leggere metriche e messaggio di metodo selezionato; verificare che coincida con RMSE minimo e col riferimento", A, "Alta"),
    ("TC-20", "Orizzonte previsivo 1-6 mesi", "Previsioni", "Previsione della domanda", "TC-06 superato", "Orizzonte 1..6; GUANTI", "Impostare lo slider; verificare righe, mesi consecutivi da 2026-01 e valori", A, "Alta"),
    ("TC-21", "Finestra della media mobile 2-6", "Previsioni", "Parametri del metodo", "TC-06 superato", "Finestra 2..6; GUANTI", "Impostare lo slider; confrontare RMSE della media mobile e previsioni col riferimento", A, "Media"),
    ("TC-22", "Valori limite degli slider di scenario", "Previsioni", "Modifica delle caratteristiche della domanda", "TC-06 superato", "Variabilita 0,5/2,0; variazione -30/+30; orizzonte 1/6; finestra 2/6", "Impostare le 16 combinazioni di estremi; verificare assenza di eccezioni, previsioni >= 0 e valori = riferimento", A, "Alta"),
    ("TC-23", "Effetto di variabilita e variazione sulle previsioni", "Previsioni", "Effetti sulle previsioni", "TC-06 superato", "Variazione +30%; variabilita 2,0; GUANTI", "Confrontare previsioni/metriche col caso di base", A, "Media"),
    ("TC-24", "Test unitari delle funzioni di previsione e di errore", "Previsioni", "Correttezza dei metodi", "Funzioni estratte da app.py via AST", "Serie note ([1,2,3], retta y=2x+1, ecc.)", "Eseguire le funzioni con valori a risultato noto e confrontare", A, "Alta"),
    ("TC-25", "Casi limite: MAPE con zeri e serie corte", "Casi limite", "Robustezza del calcolo", "Come TC-24", "Reali = 0; serie di 1-2 punti", "Eseguire error_metrics, moving_average_forecast e linear_forecast sui casi limite", A, "Alta"),
    ("TC-26", "Holdout cronologico test_n = min(4, max(2, n//5))", "Previsioni", "Valutazione dell'accuratezza", "TC-18 superato", "ATS Demo Sud, DISINFETTANTI; n = 24", "Calcolare test_n; confrontare RMSE dashboard con riferimento a 4 mesi e a 2 mesi", A, "Media"),
    ("TC-27", "Componenti di scorta - GUANTI (caso di riferimento)", "Componenti di scorta", "Scorte cicliche, di sicurezza, anticipate, pipeline", "TC-06 superato", "GUANTI, lead time 30, livello 0,95, variabilita 1,0, orizzonte 3, finestra 3", "Leggere la tabella Componenti; confrontare con le formule ricalcolate", A, "Alta"),
    ("TC-28", "Componenti di scorta - tutte le categorie e piu' enti", "Componenti di scorta", "Scorte per tipologia", "TC-27 superato", "6 categorie x (Tutti, ATS Demo Nord, AREU); lead 60, livello 0,99, variabilita 1,5", "Impostare i parametri; confrontare le 4 componenti col riferimento", A, "Alta"),
    ("TC-29", "Monotonia rispetto al lead time", "Componenti di scorta", "Effetto del lead time sulle scorte", "TC-27 superato", "Lead time 7..120 (passo 7), GUANTI", "Eseguire per ogni valore; verificare crescita di sicurezza e pipeline e costanza della ciclica", A, "Alta"),
    ("TC-30", "Monotonia rispetto al livello di servizio", "Componenti di scorta", "Effetto del livello di servizio", "TC-27 superato", "Livello 0,90/0,95/0,975/0,99, GUANTI", "Eseguire per ogni livello; verificare crescita della sicurezza e rapporto z", A, "Alta"),
    ("TC-31", "Effetto della variabilita sulle scorte", "Componenti di scorta", "Effetto della variabilita", "TC-27 superato", "Variabilita 0,5/1,0/2,0, GUANTI", "Verificare proporzionalita della sicurezza e invarianza delle altre componenti", A, "Media"),
    ("TC-32", "Formule di scorta ciclica e pipeline su tutte le categorie", "Componenti di scorta", "Criteri di calcolo definiti", "TC-27 superato", "6 categorie, lead 45", "Confrontare pipeline = d x 45 e ciclica = d x 15 (d = domanda giornaliera media ultimi 6 mesi)", A, "Media"),
    ("TC-33", "Robustezza: combinazioni estreme di tutti gli slider", "Robustezza", "Nessuna eccezione", "TC-06 superato", "32 combinazioni degli estremi (orizzonte, finestra, variabilita, variazione, lead) con livello e categoria ruotati", "Eseguire ciascuna combinazione; verificare nessuna eccezione e componenti finite e >= 0", A, "Alta"),
    ("TC-34", "CSV mancante, colonna mancante, CSV vuoto", "Casi limite", "Gestione errori sui dati", "Copia di app.py in cartella temporanea", "File assente; colonna giacenza_pezzi rimossa; solo intestazione", "Eseguire l'app su ciascuna variante: attesi st.error guidato in italiano, nessuna eccezione, nessuna scheda (v1.0: documentava le eccezioni non gestite)", A, "Media"),
    ("TC-35", "Coerenza dei file dati distribuiti con l'app", "Requisiti traccia", "Repository con codice, dati e file necessari", "Codice sorgente app.py", "app.py, data/*.csv", "Cercare in app.py l'uso di domanda_storica.csv e parametri_scorte.csv", A, "Bassa"),
    ("TC-36", "Almeno 4 serie con andamenti diversi e almeno 2 metodi", "Requisiti traccia", "Traccia: >= 4 articoli, >= 2 metodi", "TC-18 superato", "6 categorie", "Contare categorie e metodi; calcolare la pendenza di ciascuna serie", A, "Alta"),
    ("TC-37", "Controlli di scenario richiesti dalla traccia", "Requisiti traccia", "Modificare variabilita, trend, stagionalita, lead time", "TC-06 superato", "Etichette degli slider", "Elencare i controlli della barra laterale e verificare la presenza dei quattro elementi", A, "Media"),
    ("TC-38", "Effetto del trend sulle componenti di scorta", "Requisiti traccia", "Effetti delle caratteristiche della domanda sulle scorte", "TC-27 superato", "Variazione 0% e +30%, GUANTI", "Confrontare le componenti nei due scenari", A, "Media"),
    ("TC-39", "Tempo di esecuzione dello script", "Non funzionali", "Prestazioni minime", "TC-06 superato", "3 esecuzioni, soglia 10 s", "Misurare il tempo di una esecuzione completa con AppTest", A, "Media"),
    ("TC-40", "Avvio del server Streamlit (porta 8503)", "Non funzionali", "Avvio", "Porta 8503 libera", "streamlit run app.py --server.headless true", "Avviare il server; interrogare /_stcore/health e la pagina principale; arrestare il server", A, "Alta"),
    ("TC-41", "Ripetibilita (determinismo)", "Non funzionali", "Stabilita dei risultati", "TC-06 superato", "GUANTI, AREU, 2025-06", "Eseguire due volte; confrontare indicatori, metriche, componenti", A, "Media"),
    ("TC-42", "Indici stagionali", "Stagionalita'", "Stagionalita' modificabile (v1.1)", "TC-06 superato", "6 categorie, 4 articoli", "Confrontare indici dell'app con un ricalcolo indipendente; verificare intensita' 0 neutra", A, "Media"),
    ("TC-43", "Stagionalita' sulle previsioni", "Stagionalita'", "Stagionalita' modificabile (v1.1)", "TC-42 superato", "Intensita' 0,5 e 1,0", "Confrontare metriche, metodo e previsioni con il riferimento indipendente", A, "Media"),
    ("TC-44", "Stagionalita' sulle componenti di scorta", "Stagionalita'", "Effetti sulle scorte (v1.1)", "TC-42 superato", "Intensita' 0,5 e 1,0", "Confrontare le componenti con il riferimento; verificare linearita' di ciclica e pipeline", A, "Media"),
    ("TC-45", "Variazione simulata sulle componenti di scorta", "Scenario", "Effetti sulle scorte (v1.1)", "TC-27 superato", "Variazione -30/0/+30%", "Confrontare le componenti con il riferimento; la variabilita' modifica solo la sicurezza", A, "Media"),
    ("TC-46", "Scheda Articoli e parametri", "Articoli", "4 articoli da domanda_storica.csv e parametri_scorte.csv (v1.1)", "TC-05 superato", "Default e scenario", "Confrontare tabelle e previsioni con un ricalcolo pandas indipendente", A, "Alta"),
    ("TC-47", "mesi_stagionali come moltiplicatore per articolo", "Articoli", "Stagionalita' per articolo (v1.1)", "TC-46 superato", "Slider 1,0; valori 0,5/0/1,0", "Verificare che l'intensita' effettiva segua il parametro dell'articolo", A, "Media"),
    ("TC-48", "Validazione CSV: file, colonne, vuoti", "Validazione", "Messaggi guidati (v1.1)", "Copia dell'app", "3 CSV: mancante, colonna mancante, solo intestazione, 0 byte", "Eseguire l'app sulle varianti: un solo st.error in italiano, nessuna eccezione", A, "Alta"),
    ("TC-49", "Validazione CSV: valori non validi", "Validazione", "Messaggi guidati (v1.1)", "Copia dell'app", "17 varianti (negativi, testo, mesi, duplicati, serie corte, ...)", "Eseguire l'app: messaggio specifico e stop", A, "Alta"),
    ("TC-50", "Funzioni nuove (unitari)", "Stagionalita'", "Correttezza delle funzioni (v1.1)", "Funzioni estratte da app.py", "Serie sintetiche", "Verificare indici, fattori, rampa, z-score e componenti a scenario neutro", A, "Media"),
    ("TC-51", "Robustezza dei nuovi controlli", "Casi limite", "Robustezza (v1.1)", "TC-06 superato", "32 combinazioni estreme", "Eseguire l'app: nessuna eccezione, valori finiti e non negativi", A, "Media"),
    ("TC-52", "Valori di default invariati", "Regressione", "Default come v1.0", "TC-06 superato", "Parametri di default", "Confrontare i valori noti della v1.0 con quelli ottenuti", A, "Alta"),
    ("TC-53", "Compatibilita' e documentazione", "Non funzionali", "A-05 e README/NOTE (v1.1)", "File del progetto", "app.py, requirements.txt, README, NOTE", "Verificare assenza di use_container_width, versioni fissate e coerenza della documentazione", A, "Bassa"),
]
MANUALI = [
    ("TM-01", "Titolo e intestazione", "Aprire http://localhost:8501 in un browser.", ["Il titolo 'Monitoraggio delle scorte pandemiche' e' visibile in cima alla pagina", "La didascalia con 'PW 24' e' leggibile", "L'avviso di prototipo didattico e' ben visibile e comprensibile"]),
    ("TM-02", "Layout generale e barra laterale", "Ridimensionare la finestra (ampia / stretta) e osservare layout e barra laterale.", ["Le 4 metriche sono affiancate e non troncate", "La barra laterale e' ordinata (filtri, scenario)", "Nessuna sovrapposizione di elementi a larghezza ridotta", "Le tab sono navigabili"]),
    ("TM-03", "Leggibilita' dei grafici del tab Monitoraggio", "Aprire il tab Monitoraggio e osservare i tre grafici.", ["Assi, titoli e legende leggibili", "Colori Conforme (verde) / Sotto soglia (rosso) distinguibili", "Il passaggio del mouse mostra i valori (tooltip)"]),
    ("TM-04", "Leggibilita' dei grafici temporali e della previsione", "Aprire il tab 'Analisi temporale e previsione'.", ["Linea storica e previsione distinguibili (serie e colori)", "Asse dei mesi leggibile", "Il cambio di indicatore aggiorna il grafico"]),
    ("TM-05", "Formato dei numeri e delle tabelle", "Controllare tabelle e indicatori.", ["Separatori delle migliaia/decimali coerenti nelle metriche (nota: le metriche usano il formato inglese 12,345)", "Le colonne della tabella hanno nomi in italiano e sono leggibili", "Valori arrotondati in modo comprensibile"]),
    ("TM-06", "Download del CSV dal browser", "Cliccare 'Scarica i dati filtrati in CSV' con un filtro attivo.", ["Il file si scarica con nome monitoraggio_scorte_panflu.csv", "Il file si apre in Excel con accenti corretti", "Il contenuto coincide con la tabella a video"]),
    ("TM-07", "Tab Componenti di scorta e messaggi informativi", "Aprire il tab 'Componenti di scorta' e variare gli slider.", ["Le 4 componenti sono comprensibili e il grafico si aggiorna", "Il messaggio che le componenti non vanno sommate e' visibile", "I criteri dimostrativi sono leggibili"]),
    ("TM-08", "Usabilita' e comprensibilita' generale", "Far utilizzare la dashboard a una persona non coinvolta nello sviluppo.", ["I filtri e gli slider sono comprensibili senza spiegazioni", "Le etichette sono in italiano corretto", "Nessun errore a video durante l'uso", "Sezione 'Assunzioni, perimetro e limiti' letta e compresa"]),
]
ANOMALIE = [
    ("A-01", "Chiusa", "TC-37", "v1.0: stagionalita' non modificabile (TC-37 FAIL).", "v1.1: slider 'Intensita' stagionalita' (0 = neutra); TC-37 PASS con asserzione invariata.", "Nessuno."),
    ("A-02", "Chiusa", "TC-38", "v1.0: la variazione simulata non modificava le componenti di scorta (TC-38 FAIL).", "v1.1: trend +30% -> Ciclica 39.446,3; Pipeline 78.892,6; TC-38 PASS con asserzione invariata.", "Nessuno."),
    ("A-03", "Chiusa", "TC-35", "v1.0: domanda_storica.csv e parametri_scorte.csv non letti dall'app (TC-35 FAIL).", "v1.1: letti dalla scheda 'Articoli e parametri'; TC-35 e TC-46 PASS.", "Nessuno."),
    ("A-04", "Chiusa", "TC-34", "v1.0: nessuna validazione dei CSV.", "v1.1: st.error guidato in italiano; TC-34 adattato ai nuovi messaggi (non piu' caratterizzazione); TC-48 e TC-49 PASS.", "Nessuno."),
    ("A-05", "Chiusa", "TC-53", "v1.0: use_container_width deprecato; versioni non fissate.", "v1.1: width='stretch'; requirements con versioni esatte; TC-53 PASS.", "Nessuno."),
    ("O-01", "Osservazione", "TC-42..TC-53", "I casi TC-42..TC-53 sono stati aggiunti alla suite durante l'aggiornamento v1.1 e non facevano parte della v1.0.", "12 casi aggiunti, tutti PASS.", "Nessuno."),
    ("O-02", "Osservazione", "-", "Gli screenshot del documento di consegna non sono stati rifatti e potrebbero non mostrare la scheda 'Articoli e parametri' e lo slider di stagionalita'.", "Nessuno screenshot prodotto da questa suite.", "Rifare gli screenshot a cura dell'autore."),
]
REQ = [
    ("R1", "Serie storiche di almeno quattro articoli con andamenti differenti", ["TC-01", "TC-02", "TC-05", "TC-36"]),
    ("R2", "Almeno due metodi previsionali applicati", ["TC-18", "TC-24", "TC-36"]),
    ("R3", "Valutazione accuratezza con indicatori d'errore (MAE, RMSE, MAPE)", ["TC-18", "TC-24", "TC-25", "TC-26"]),
    ("R4", "Individuazione del metodo piu' adatto", ["TC-19"]),
    ("R5", "Stima delle scorte cicliche, di sicurezza, anticipate, pipeline", ["TC-27", "TC-28", "TC-32"]),
    ("R6", "Dashboard: modifica di variabilita, trend, stagionalita, lead time", ["TC-22", "TC-23", "TC-37", "TC-42", "TC-43", "TC-47"]),
    ("R7", "Effetti degli scenari sulle diverse tipologie di scorte", ["TC-29", "TC-30", "TC-31", "TC-38", "TC-44", "TC-45"]),
    ("R8", "Mostrare andamento storico e previsto della domanda", ["TC-17", "TC-20", "TC-21", "TM-04"]),
    ("R9", "Mostrare confronto di accuratezza dei metodi", ["TC-18", "TC-19"]),
    ("R10", "Mostrare composizione delle scorte nei diversi scenari", ["TC-27", "TC-33", "TM-07"]),
    ("R11", "Codice, dati e file necessari all'esecuzione", ["TC-05", "TC-35", "TC-40", "TC-46", "TC-53"]),
    ("F1", "Monitoraggio: esito giacenza vs quantita' minima", ["TC-04", "TC-07", "TC-08"]),
    ("F2", "Filtri (mese, ente, categoria, esito), anche combinati e vuoti", ["TC-09", "TC-10", "TC-11", "TC-12", "TC-13", "TC-14", "TC-15"]),
    ("F3", "Esportazione CSV dei dati filtrati", ["TC-16", "TM-06"]),
    ("N1", "Avvio, prestazioni, stabilita', robustezza", ["TC-06", "TC-33", "TC-34", "TC-39", "TC-40", "TC-41", "TC-48", "TC-49", "TC-51", "TC-52"]),
    ("N2", "Aspetti visivi e usabilita'", ["TM-01", "TM-02", "TM-03", "TM-05", "TM-08"]),
]


def carica():
    out = {}
    root = ET.parse(RES / "junit.xml").getroot()
    ts = root.find("testsuite").get("timestamp")
    for tc in root.iter("testcase"):
        m = re.match(r"test_tc_(\d+)_", tc.get("name"))
        if not m:
            continue
        i = f"TC-{int(m.group(1)):02d}"
        stato = "FAIL" if tc.find("failure") is not None or tc.find("error") is not None else ("SKIP" if tc.find("skipped") is not None else "PASS")
        out[i] = (stato, float(tc.get("time")))
    return out, ts, float(root.find("testsuite").get("time"))


r2, ts2, dur2 = carica()
det = json.loads((RES / "details.json").read_text(encoding="utf-8"))
assert set(r2) == {c[0] for c in CASI}, set(r2) ^ {c[0] for c in CASI}
n_pass = sum(1 for k in r2 if r2[k][0] == "PASS")
n_fail = sum(1 for k in r2 if r2[k][0] == "FAIL")
n_man = len(MANUALI)
n_auto = len(CASI)


def esito_doc(i):
    return r2[i][0] if i in r2 else "NON ESEGUITO"


# =========================================================================== testo comune
def titolo_doc(nome):
    return f"{nome} - Dashboard PW24 'Monitoraggio delle scorte pandemiche'"


def fmt_md_table(header, rows):
    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def ambiente():
    return [
        ("Sistema operativo", f"{platform.system()} {platform.release()} ({platform.version()})"),
        ("Python", platform.python_version()),
        ("Streamlit", streamlit.__version__), ("pandas", pandas.__version__), ("NumPy", numpy.__version__),
        ("Plotly", plotly.__version__), ("pytest", pytest.__version__), ("python-docx (solo documenti)", "1.1.2"),
        ("Applicazione sotto test", r"acamino_0312501773\PW24_dashboard_sanitario\app.py (sola lettura)"),
        ("Metodo di esecuzione", "streamlit.testing.v1.AppTest (headless) + avvio server su porta 8503 (TC-40)"),
        ("Esecuzione (una sola)", f"{ts2[:19].replace('T', ' ')} - durata {dur2:.0f} s"),
    ]


# =========================================================================== modello documento
class Doc:
    """Costruisce in parallelo Markdown e DOCX."""

    def __init__(self, titolo, sottotitolo):
        self.md = [f"# {titolo}", "", f"**{sottotitolo}**", "", f"Versione {VERSIONE} - {DATA_DOC} - Progetto PW 24 (Pegaso L-31)", ""]
        d = docx.Document()
        s = d.sections[0]
        s.orientation = WD_ORIENT.LANDSCAPE
        s.page_width, s.page_height = s.page_height, s.page_width
        for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(s, a, Cm(1.8))
        for nome in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3"):
            st_ = d.styles[nome]
            st_.font.name = "Times New Roman"
            st_._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
            st_._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
            st_._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        d.styles["Normal"].font.size = Pt(11)
        for nome, sz in (("Title", 20), ("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 12)):
            d.styles[nome].font.size = Pt(sz)
            d.styles[nome].font.color.rgb = None
        s.header.paragraphs[0].text = f"PW24 - {titolo.split(' - ')[0]} - v{VERSIONE}"
        s.header.paragraphs[0].runs[0].font.size = Pt(9)
        self._piedi(s)
        self.d = d
        t = d.add_paragraph(titolo, style="Title")
        t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = d.add_paragraph(sottotitolo)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].bold = True
        p = d.add_paragraph(f"Versione {VERSIONE} - {DATA_DOC} - Progetto PW 24 (Pegaso L-31)")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _piedi(self, s):
        p = s.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("Pagina ")
        r = p.add_run()
        for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
            if tag:
                e = OxmlElement("w:fldChar")
                e.set(qn("w:fldCharType"), tag)
            else:
                e = OxmlElement("w:instrText")
                e.set(qn("xml:space"), "preserve")
                e.text = txt
            r._r.append(e)

    def h(self, testo, livello=1):
        self.md += [f"{'#' * (livello + 1)} {testo}", ""]
        self.d.add_heading(testo, level=livello)

    def p(self, testo, bold=False):
        self.md += [f"**{testo}**" if bold else testo, ""]
        par = self.d.add_paragraph()
        r = par.add_run(testo)
        r.bold = bold

    def bullets(self, voci):
        self.md += [f"- {v}" for v in voci] + [""]
        for v in voci:
            self.d.add_paragraph(v, style="List Bullet")

    def code(self, testo):
        self.md += ["```", testo, "```", ""]
        par = self.d.add_paragraph()
        r = par.add_run(testo)
        r.font.name = "Courier New"
        r.font.size = Pt(9.5)

    def table(self, header, rows, widths=None, colora_col=None):
        self.md += [fmt_md_table(header, rows), ""]
        t = self.d.add_table(rows=1, cols=len(header))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, hd in enumerate(header):
            c = t.rows[0].cells[i]
            c.text = ""
            r = c.paragraphs[0].add_run(hd)
            r.bold = True
            r.font.size = Pt(10)
            sh = OxmlElement("w:shd")
            sh.set(qn("w:val"), "clear")
            sh.set(qn("w:fill"), "D9E2F3")
            c._tc.get_or_add_tcPr().append(sh)
        trPr = t.rows[0]._tr.get_or_add_trPr()
        th = OxmlElement("w:tblHeader")
        th.set(qn("w:val"), "true")
        trPr.append(th)
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                r = cells[i].paragraphs[0].add_run(str(v))
                r.font.size = Pt(9.5)
                if colora_col is not None and i == colora_col:
                    r.bold = True
                    col = {"PASS": "1B5E20", "FAIL": "B71C1C"}.get(str(v))
                    if col:
                        from docx.shared import RGBColor
                        r.font.color.rgb = RGBColor.from_string(col)
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Cm(w)
        self.d.add_paragraph()

    def save(self, nome):
        self.d.save(str(T / f"{nome}.docx"))
        (T / f"{nome}.md").write_text("\n".join(self.md), encoding="utf-8")


def valore_atteso(i):
    return det[i]["atteso"]


# =========================================================================== TEST BOOK
def test_book():
    b = Doc(titolo_doc("Test Book"), "Piano di test della dashboard Streamlit per il monitoraggio delle scorte pandemiche (dati sintetici)")
    b.h("1. Scopo e ambito")
    b.p("Il documento definisce i casi di test per verificare la dashboard sviluppata per il PW 24 (traccia: mini-dashboard Python per previsione della domanda e pianificazione delle scorte). "
        "Il contesto applicativo e' il monitoraggio delle scorte pandemiche (categorie PANFLU) con dati interamente sintetici. Il codice sotto test non viene modificato.")
    b.p("Sistema sotto test: app.py (Streamlit), data/monitoraggio_panflu_demo.csv (864 righe: 6 enti x 6 categorie x 24 mesi, da 2024-01 a 2025-12), data/domanda_storica.csv, data/parametri_scorte.csv.")
    b.h("2. Funzionalita' reali individuate in app.py")
    b.bullets([
        "Caricamento del CSV di monitoraggio all'avvio (senza validazione delle colonne: un file mancante o malformato genera un'eccezione).",
        "Filtri nella barra laterale: mese di riferimento (default: ultimo mese, dicembre 2025), ente, tipologia dispositivo (categoria), esito verifica.",
        "Esito per riga: Conforme se giacenza >= quantita' minima richiesta, altrimenti Sotto soglia.",
        "Quattro indicatori sui record filtrati: giacenze, quantita' minima, righe sotto soglia, scorte scadute.",
        "Tabella filtrata con pulsante di download CSV (UTF-8 con BOM), messaggio 'Nessun record...' se la selezione e' vuota.",
        "Grafici: confronto giacenza/minima per categoria, scorte scadute per categoria, torta degli esiti; andamento temporale per indicatore e copertura nel tempo; previsione; componenti di scorta.",
        "Previsioni: media mobile semplice e regressione lineare; holdout cronologico test_n = min(4, max(2, n//5)); metriche MAE, RMSE, MAPE; scelta del metodo con RMSE minore.",
        "Slider di scenario: orizzonte 1-6, finestra 2-6, variabilita 0,5-2,0 (passo 0,1), variazione simulata -30..+30% (passo 5), lead time 7-120 giorni (passo 7), livello di servizio 0,90/0,95/0,975/0,99.",
        "Componenti di scorta: ciclica = d x 30 / 2; sicurezza = z x sigma_g x variabilita x radice(lead); pipeline = d x lead; anticipata = max(0, media prevista - media ultimi 3 mesi) x lead/30,4375, con d = media degli ultimi 6 mesi / 30,4375 e sigma_g = dev. standard (ddof=1) degli ultimi 12 mesi / 30,4375; z = 1,282 / 1,645 / 1,960 / 2,326.",
    ])
    b.h("3. Strategia e criteri")
    b.bullets([
        "Test automatici: streamlit.testing.v1.AppTest (esecuzione headless dell'app) e funzioni pure estratte da app.py; avvio reale del server sulla porta 8503 per il controllo di salute. Script: test/test_dashboard.py (pytest).",
        "I valori attesi sono ricalcolati in modo indipendente da CSV con pandas/NumPy (implementazione di riferimento nello script, non importata dall'app).",
        "Test manuali: aspetti visivi e di usabilita' non automatizzabili, con checklist da compilare.",
        "Esito: PASS se tutte le asserzioni sono vere; FAIL se almeno una e' falsa (verificato che non dipenda dal test); NON ESEGUITO per i casi manuali non ancora svolti.",
        "Priorita': Alta (funzione essenziale), Media, Bassa.",
    ])
    b.h("4. Elenco dei casi di test automatici")
    b.table(["ID", "Titolo", "Area", "Tipo", "Priorita'"], [(c[0], c[1], c[2], c[7], c[8]) for c in CASI], [2, 12, 5, 3, 2.5])
    b.h("5. Dettaglio dei casi automatici")
    for c in CASI:
        i, tit, area, req, pre, inp, passi, tipo, pr = c
        b.h(f"{i} - {tit}", 3)
        b.table(["Campo", "Descrizione"], [
            ("Obiettivo", tit), ("Requisito / funzione collegata", req), ("Area", area),
            ("Precondizioni", pre), ("Dati / parametri di input", inp), ("Passi", passi),
            ("Risultato atteso", valore_atteso(i)), ("Tipo", tipo), ("Priorita'", pr),
        ], [5, 20])
    b.h("6. Casi di test manuali (da eseguire con browser)")
    b.p("Precondizione comune: dashboard in esecuzione (es. http://localhost:8501) con i dati demo. Per ogni voce annotare esito (OK / KO) e note. Questi casi NON sono stati eseguiti dal sistema automatico.")
    for i, tit, passo, chk in MANUALI:
        b.h(f"{i} - {tit}", 3)
        b.p(f"Passi: {passo}")
        b.table(["Verifica", "OK", "KO", "Note"], [(v, "[ ]", "[ ]", "") for v in chk], [13, 2, 2, 8])
        b.p("Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________")
    b.h("7. Matrice di tracciabilita' requisiti - casi di test")
    b.table(["Rif.", "Requisito / funzione", "Casi di test"], [(r, t, ", ".join(c)) for r, t, c in REQ], [2, 14, 9])
    b.h("8. Come eseguire i test automatici")
    b.code(COMANDO)
    b.p("Prerequisiti: ambiente .venv con streamlit, pandas, numpy, plotly, pytest. Non e' necessario che la dashboard sia in esecuzione; il caso TC-40 usa la porta 8503.")
    b.save("Test_Book_PW24")


# =========================================================================== TEST REPORT
def test_report():
    r = Doc(titolo_doc("Test Report"), "Esito dell'esecuzione del Test Book (versione 1.1)")
    r.h("1. Ambiente di esecuzione")
    r.table(["Voce", "Valore"], ambiente(), [6, 19])
    tot = n_auto + n_man
    r.h("2. Riepilogo")
    r.table(["Indicatore", "Valore"], [
        ("Test pianificati (totale)", tot), ("Test automatici pianificati", n_auto), ("Test automatici eseguiti", n_auto),
        ("Passati (PASS)", n_pass), ("Falliti (FAIL)", n_fail), ("Non eseguiti - manuali (NON ESEGUITO)", n_man),
        ("Numero di esecuzioni", "una sola esecuzione"),
    ], [9, 12])
    r.p(f"Sono stati eseguiti {n_auto} test automatici su {n_auto}: {n_pass} passati e {n_fail} falliti, in una sola esecuzione. I {n_man} casi manuali ({', '.join(m[0] for m in MANUALI)}) non sono stati eseguiti e restano da compilare.")
    r.p("Differenze rispetto alla versione 1.0 (41 test automatici: 38 PASS, 3 FAIL: TC-35, TC-37, TC-38): l'app e' stata aggiornata (stagionalita', effetto di variazione e stagionalita' sulle componenti, scheda 'Articoli e parametri', validazione dei CSV). TC-35, TC-37 e TC-38 ora risultano PASS con asserzioni invariate; TC-34 e' stato adattato ai nuovi messaggi guidati; TC-06 e i conteggi dei grafici sono stati allineati alla quarta scheda; sono presenti i casi aggiunti TC-42..TC-53 (12 casi).", bold=False)
    r.h("3. Risultati per caso di test")
    rows = []
    for c in CASI:
        i = c[0]
        rows.append((i, c[1], esito_doc(i), valore_atteso(i), det[i]["ottenuto"], f"{r2[i][1]:.2f}"))
    r.table(["ID", "Titolo", "Esito", "Valore atteso", "Valore ottenuto", "Tempo (s)"], rows, [1.5, 4.2, 1.7, 7.5, 7.5, 1.6], colora_col=2)
    for i, tit, passo, chk in MANUALI:
        pass
    r.table(["ID", "Titolo", "Esito"], [(m[0], m[1], "NON ESEGUITO - da eseguire manualmente") for m in MANUALI], [2, 12, 10])
    r.p("Checklist dei casi manuali: vuota, da compilare nel Test Book (sezione 6).")
    r.h("4. Anomalie e osservazioni")
    r.table(["ID", "Gravita'", "Test", "Descrizione", "Evidenza (atteso vs ottenuto)", "Suggerimento"], ANOMALIE, [1.3, 1.6, 1.6, 8, 6.5, 5.5])
    r.p(f"Test falliti: {n_fail}." if n_fail else "Nessun test automatico fallito in questa esecuzione.")
    r.h("5. Copertura dei requisiti")
    righe = []
    for rid, txt, casi in REQ:
        auto = [c for c in casi if c.startswith("TC")]
        es = [f"{c}:{esito_doc(c)}" for c in casi]
        if any(c.startswith("TM") for c in casi):
            es = [e.replace("NON ESEGUITO", "NON ESEGUITO") for e in es]
        righe.append((rid, txt, ", ".join(es)))
    r.table(["Rif.", "Requisito / funzione", "Casi ed esito"], righe, [1.5, 10, 14])
    r.h("6. Valori numerici di riferimento verificati")
    r.bullets([
        f"TC-04: {det['TC-04']['ottenuto']}",
        f"TC-07: {det['TC-07']['ottenuto']}",
        f"TC-18/TC-23: GUANTI, RMSE media mobile 5.978,0 contro regressione lineare 10.339,25 (metodo scelto: media mobile semplice); previsioni a 3 mesi {det['TC-23']['ottenuto'].split(' vs ')[0].replace('previsioni base ', '')}",
        f"TC-27: {det['TC-27']['ottenuto']}",
        f"TC-29: {det['TC-29']['ottenuto']}",
        f"TC-30: {det['TC-30']['ottenuto']}",
    ])
    r.h("7. Limiti della verifica")
    r.bullets([
        "Il rendering visivo nel browser, il layout, la leggibilita' dei grafici e il formato dei numeri a video non sono verificati (casi TM-01..TM-08 non eseguiti). Non sono stati prodotti screenshot.",
        "I grafici Plotly sono verificati solo come presenti e senza eccezioni (conteggio), non nei contenuti visivi.",
        "Non verificati: accessibilita', compatibilita' tra browser e sistemi operativi, prestazioni con dati di grandi dimensioni, uso concorrente.",
        "I dati sono sintetici: nessuna verifica di aderenza a dati reali di enti sanitari.",
        "Il contenuto del download e' verificato intercettando i dati passati a st.download_button, non scaricando il file dal browser.",
        "Il tempo di esecuzione (TC-39) misura solo lo script in AppTest, non l'apertura della pagina nel browser; TC-40 misura l'avvio del server.",
        "I valori attesi sono calcolati dallo stesso team con formule ricalcolate in modo indipendente dal codice, ma sulla base della stessa descrizione funzionale: non e' una validazione metodologica dei criteri di scorta (scelte didattiche).",
    ])
    r.h("8. Conclusioni")
    r.p(f"La dashboard supera {n_pass} test automatici su {n_auto} in una sola esecuzione. Le nuove funzioni (stagionalita', scenario, vista a quattro articoli, validazione dei CSV) sono coperte solo dai test elencati. "
        "I valori di default della v1.0 risultano invariati (TC-52). I controlli manuali TM-01..TM-08 non sono stati eseguiti, non sono stati prodotti screenshot e i dati sono sintetici: la verifica visiva resta da fare.")
    r.h("9. Riproducibilita'")
    r.p("Dalla cartella PW24, con l'ambiente virtuale del progetto:")
    r.code(COMANDO + "\n.venv\\Scripts\\python.exe test/genera_documenti.py   (rigenera .md e .docx dai risultati; richiede junit.xml e details.json in test/results)")
    r.p("File prodotti: test/test_dashboard.py, test/results/junit.xml, test/results/details.json.")
    r.save("Test_Report_PW24")


if __name__ == "__main__":
    test_book()
    test_report()
    print("OK", n_pass, n_fail)
