# Test Book - Dashboard PW24 'Monitoraggio delle scorte pandemiche'

**Piano di test della dashboard Streamlit per il monitoraggio delle scorte pandemiche (dati sintetici)**

Versione 1.1 - 21/11/2026 - Progetto PW 24 (Pegaso L-31)

## 1. Scopo e ambito

Il documento definisce i casi di test per verificare la dashboard sviluppata per il PW 24 (traccia: mini-dashboard Python per previsione della domanda e pianificazione delle scorte). Il contesto applicativo e' il monitoraggio delle scorte pandemiche (categorie PANFLU) con dati interamente sintetici. Il codice sotto test non viene modificato.

Sistema sotto test: app.py (Streamlit), data/monitoraggio_panflu_demo.csv (864 righe: 6 enti x 6 categorie x 24 mesi, da 2024-01 a 2025-12), data/domanda_storica.csv, data/parametri_scorte.csv.

## 2. Funzionalita' reali individuate in app.py

- Caricamento del CSV di monitoraggio all'avvio (senza validazione delle colonne: un file mancante o malformato genera un'eccezione).
- Filtri nella barra laterale: mese di riferimento (default: ultimo mese, dicembre 2025), ente, tipologia dispositivo (categoria), esito verifica.
- Esito per riga: Conforme se giacenza >= quantita' minima richiesta, altrimenti Sotto soglia.
- Quattro indicatori sui record filtrati: giacenze, quantita' minima, righe sotto soglia, scorte scadute.
- Tabella filtrata con pulsante di download CSV (UTF-8 con BOM), messaggio 'Nessun record...' se la selezione e' vuota.
- Grafici: confronto giacenza/minima per categoria, scorte scadute per categoria, torta degli esiti; andamento temporale per indicatore e copertura nel tempo; previsione; componenti di scorta.
- Previsioni: media mobile semplice e regressione lineare; holdout cronologico test_n = min(4, max(2, n//5)); metriche MAE, RMSE, MAPE; scelta del metodo con RMSE minore.
- Slider di scenario: orizzonte 1-6, finestra 2-6, variabilita 0,5-2,0 (passo 0,1), variazione simulata -30..+30% (passo 5), lead time 7-120 giorni (passo 7), livello di servizio 0,90/0,95/0,975/0,99.
- Componenti di scorta: ciclica = d x 30 / 2; sicurezza = z x sigma_g x variabilita x radice(lead); pipeline = d x lead; anticipata = max(0, media prevista - media ultimi 3 mesi) x lead/30,4375, con d = media degli ultimi 6 mesi / 30,4375 e sigma_g = dev. standard (ddof=1) degli ultimi 12 mesi / 30,4375; z = 1,282 / 1,645 / 1,960 / 2,326.

## 3. Strategia e criteri

- Test automatici: streamlit.testing.v1.AppTest (esecuzione headless dell'app) e funzioni pure estratte da app.py; avvio reale del server sulla porta 8503 per il controllo di salute. Script: test/test_dashboard.py (pytest).
- I valori attesi sono ricalcolati in modo indipendente da CSV con pandas/NumPy (implementazione di riferimento nello script, non importata dall'app).
- Test manuali: aspetti visivi e di usabilita' non automatizzabili, con checklist da compilare.
- Esito: PASS se tutte le asserzioni sono vere; FAIL se almeno una e' falsa (verificato che non dipenda dal test); NON ESEGUITO per i casi manuali non ancora svolti.
- Priorita': Alta (funzione essenziale), Media, Bassa.

## 4. Elenco dei casi di test automatici

| ID | Titolo | Area | Tipo | Priorita' |
|---|---|---|---|---|
| TC-01 | Struttura del CSV di monitoraggio | Dati e integrita' | Automatico | Alta |
| TC-02 | Integrita' dei dati (nulli, duplicati, completezza) | Dati e integrita' | Automatico | Alta |
| TC-03 | Validita' dei valori | Dati e integrita' | Automatico | Media |
| TC-04 | Totali di esito sull'intero dataset | Dati e integrita' | Automatico | Alta |
| TC-05 | File ausiliari (domanda storica, parametri scorte) | Dati e integrita' | Automatico | Media |
| TC-06 | Avvio dell'app e struttura della pagina | Avvio e struttura | Automatico | Alta |
| TC-07 | Indicatori e tabella di default (dicembre 2025) | Indicatori | Automatico | Alta |
| TC-08 | Logica dell'esito (giacenza >= minima) | Logica esito | Automatico | Alta |
| TC-09 | Filtro mese di riferimento | Filtri | Automatico | Alta |
| TC-10 | Filtro ente | Filtri | Automatico | Alta |
| TC-11 | Filtro tipologia dispositivo (categoria) | Filtri | Automatico | Alta |
| TC-12 | Filtro esito verifica | Filtri | Automatico | Alta |
| TC-13 | Filtri combinati | Filtri | Automatico | Alta |
| TC-14 | Selezione vuota (nessun risultato) | Filtri | Automatico | Alta |
| TC-15 | Indicatori calcolati sui record filtrati | Indicatori | Automatico | Media |
| TC-16 | Download CSV dei dati filtrati | Download | Automatico | Alta |
| TC-17 | Selettore indicatore e grafici temporali | Grafici | Automatico | Media |
| TC-18 | Metriche MAE/RMSE/MAPE e confronto metodi (6 categorie) | Previsioni | Automatico | Alta |
| TC-19 | Scelta del metodo con RMSE minore | Previsioni | Automatico | Alta |
| TC-20 | Orizzonte previsivo 1-6 mesi | Previsioni | Automatico | Alta |
| TC-21 | Finestra della media mobile 2-6 | Previsioni | Automatico | Media |
| TC-22 | Valori limite degli slider di scenario | Previsioni | Automatico | Alta |
| TC-23 | Effetto di variabilita e variazione sulle previsioni | Previsioni | Automatico | Media |
| TC-24 | Test unitari delle funzioni di previsione e di errore | Previsioni | Automatico | Alta |
| TC-25 | Casi limite: MAPE con zeri e serie corte | Casi limite | Automatico | Alta |
| TC-26 | Holdout cronologico test_n = min(4, max(2, n//5)) | Previsioni | Automatico | Media |
| TC-27 | Componenti di scorta - GUANTI (caso di riferimento) | Componenti di scorta | Automatico | Alta |
| TC-28 | Componenti di scorta - tutte le categorie e piu' enti | Componenti di scorta | Automatico | Alta |
| TC-29 | Monotonia rispetto al lead time | Componenti di scorta | Automatico | Alta |
| TC-30 | Monotonia rispetto al livello di servizio | Componenti di scorta | Automatico | Alta |
| TC-31 | Effetto della variabilita sulle scorte | Componenti di scorta | Automatico | Media |
| TC-32 | Formule di scorta ciclica e pipeline su tutte le categorie | Componenti di scorta | Automatico | Media |
| TC-33 | Robustezza: combinazioni estreme di tutti gli slider | Robustezza | Automatico | Alta |
| TC-34 | CSV mancante, colonna mancante, CSV vuoto | Casi limite | Automatico | Media |
| TC-35 | Coerenza dei file dati distribuiti con l'app | Requisiti traccia | Automatico | Bassa |
| TC-36 | Almeno 4 serie con andamenti diversi e almeno 2 metodi | Requisiti traccia | Automatico | Alta |
| TC-37 | Controlli di scenario richiesti dalla traccia | Requisiti traccia | Automatico | Media |
| TC-38 | Effetto del trend sulle componenti di scorta | Requisiti traccia | Automatico | Media |
| TC-39 | Tempo di esecuzione dello script | Non funzionali | Automatico | Media |
| TC-40 | Avvio del server Streamlit (porta 8503) | Non funzionali | Automatico | Alta |
| TC-41 | Ripetibilita (determinismo) | Non funzionali | Automatico | Media |
| TC-42 | Indici stagionali | Stagionalita' | Automatico | Media |
| TC-43 | Stagionalita' sulle previsioni | Stagionalita' | Automatico | Media |
| TC-44 | Stagionalita' sulle componenti di scorta | Stagionalita' | Automatico | Media |
| TC-45 | Variazione simulata sulle componenti di scorta | Scenario | Automatico | Media |
| TC-46 | Scheda Articoli e parametri | Articoli | Automatico | Alta |
| TC-47 | mesi_stagionali come moltiplicatore per articolo | Articoli | Automatico | Media |
| TC-48 | Validazione CSV: file, colonne, vuoti | Validazione | Automatico | Alta |
| TC-49 | Validazione CSV: valori non validi | Validazione | Automatico | Alta |
| TC-50 | Funzioni nuove (unitari) | Stagionalita' | Automatico | Media |
| TC-51 | Robustezza dei nuovi controlli | Casi limite | Automatico | Media |
| TC-52 | Valori di default invariati | Regressione | Automatico | Alta |
| TC-53 | Compatibilita' e documentazione | Non funzionali | Automatico | Bassa |

## 5. Dettaglio dei casi automatici

#### TC-01 - Struttura del CSV di monitoraggio

| Campo | Descrizione |
|---|---|
| Obiettivo | Struttura del CSV di monitoraggio |
| Requisito / funzione collegata | Dati: ente, categoria, mese, consumi, minima, giacenza, scadute |
| Area | Dati e integrita' |
| Precondizioni | File data/monitoraggio_panflu_demo.csv presente |
| Dati / parametri di input | CSV demo |
| Passi | Leggere il CSV con pandas; contare righe e confrontare nomi colonna |
| Risultato atteso | 864 righe; colonne id_ente, tipologia_ente, categoria_panflu, mese_riferimento, consumo_mensile_pezzi, quantita_minima_richiesta, giacenza_pezzi, scorte_scadute_pezzi |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-02 - Integrita' dei dati (nulli, duplicati, completezza)

| Campo | Descrizione |
|---|---|
| Obiettivo | Integrita' dei dati (nulli, duplicati, completezza) |
| Requisito / funzione collegata | Qualita' dati sintetici |
| Area | Dati e integrita' |
| Precondizioni | TC-01 superato |
| Dati / parametri di input | CSV demo |
| Passi | Contare valori nulli; duplicati sulla chiave (ente, categoria, mese); verificare la griglia 6 x 6 x 24 |
| Risultato atteso | 0 nulli; 0 duplicati sulla chiave; 6 enti x 6 categorie x 24 mesi = 864 |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-03 - Validita' dei valori

| Campo | Descrizione |
|---|---|
| Obiettivo | Validita' dei valori |
| Requisito / funzione collegata | Qualita' dati sintetici |
| Area | Dati e integrita' |
| Precondizioni | TC-01 superato |
| Dati / parametri di input | CSV demo |
| Passi | Verificare assenza di negativi, minime <= 0, scadute > giacenza, formato mese AAAA-MM |
| Risultato atteso | 0 valori negativi; 0 quantita minime <= 0; 0 righe con scadute > giacenza; mesi formato AAAA-MM |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-04 - Totali di esito sull'intero dataset

| Campo | Descrizione |
|---|---|
| Obiettivo | Totali di esito sull'intero dataset |
| Requisito / funzione collegata | Verifica giacenza vs quantita' minima |
| Area | Dati e integrita' |
| Precondizioni | TC-01 superato |
| Dati / parametri di input | CSV demo |
| Passi | Calcolare con pandas righe con giacenza < minima, percentuale, scadute totali, righe al limite |
| Risultato atteso | 525 sotto soglia su 864 = 60,8%; scorte scadute totali 47.036; 1 riga con giacenza = minima |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-05 - File ausiliari (domanda storica, parametri scorte)

| Campo | Descrizione |
|---|---|
| Obiettivo | File ausiliari (domanda storica, parametri scorte) |
| Requisito / funzione collegata | Traccia: serie storiche di >= 4 articoli |
| Area | Dati e integrita' |
| Precondizioni | File presenti in data/ |
| Dati / parametri di input | domanda_storica.csv, parametri_scorte.csv |
| Passi | Leggere i file; verificare dimensioni, colonne, nulli |
| Risultato atteso | domanda_storica.csv 144 righe, 4 articoli, colonne data/articolo/domanda; parametri_scorte.csv 4 righe |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-06 - Avvio dell'app e struttura della pagina

| Campo | Descrizione |
|---|---|
| Obiettivo | Avvio dell'app e struttura della pagina |
| Requisito / funzione collegata | Titolo, tab, indicatori, grafici |
| Area | Avvio e struttura |
| Precondizioni | Ambiente Python con streamlit |
| Dati / parametri di input | Parametri di default |
| Passi | Eseguire app.py con AppTest; verificare eccezioni, titolo, tab, metriche, grafici, avviso 'prototipo didattico' |
| Risultato atteso | nessuna eccezione; titolo 'Monitoraggio delle scorte pandemiche'; 4 tab (3 originali + 'Articoli e parametri'); 4 indicatori; 10 grafici; avviso prototipo |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-07 - Indicatori e tabella di default (dicembre 2025)

| Campo | Descrizione |
|---|---|
| Obiettivo | Indicatori e tabella di default (dicembre 2025) |
| Requisito / funzione collegata | Indicatori di sintesi sui record filtrati |
| Area | Indicatori |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Mese 2025-12, Tutti/Tutte/Tutti |
| Passi | Avviare con default; leggere le 4 metriche e la tabella; confrontare con pandas |
| Risultato atteso | dicembre 2025: {'Giacenze rilevate': 155978, 'Quantità minima richiesta': 227480, 'Righe sotto soglia': 24, 'Scorte scadute rilevate': 1863}; 36 righe in tabella, 24 sotto soglia, 12 conformi |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-08 - Logica dell'esito (giacenza >= minima)

| Campo | Descrizione |
|---|---|
| Obiettivo | Logica dell'esito (giacenza >= minima) |
| Requisito / funzione collegata | Esito Conforme / Sotto soglia |
| Area | Logica esito |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Tutti i 24 mesi; riga al limite giacenza = minima |
| Passi | Per ogni mese leggere la tabella e ricalcolare l'esito; verificare la riga al limite |
| Risultato atteso | esito = Conforme se giacenza >= quantita minima, altrimenti Sotto soglia, su 24 mesi (864 righe); riga al limite (giacenza = minima) = Conforme |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-09 - Filtro mese di riferimento

| Campo | Descrizione |
|---|---|
| Obiettivo | Filtro mese di riferimento |
| Requisito / funzione collegata | Filtro mese |
| Area | Filtri |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 24 mesi |
| Passi | Selezionare ciascun mese; confrontare righe e indicatori con pandas |
| Risultato atteso | per ognuno dei 24 mesi: 36 righe, solo il mese scelto, indicatori = pandas |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-10 - Filtro ente

| Campo | Descrizione |
|---|---|
| Obiettivo | Filtro ente |
| Requisito / funzione collegata | Filtro ente |
| Area | Filtri |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 6 enti |
| Passi | Selezionare ciascun ente; confrontare righe e indicatori |
| Risultato atteso | per ognuno dei 6 enti (dic 2025): 6 righe, indicatori = pandas |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-11 - Filtro tipologia dispositivo (categoria)

| Campo | Descrizione |
|---|---|
| Obiettivo | Filtro tipologia dispositivo (categoria) |
| Requisito / funzione collegata | Filtro categoria |
| Area | Filtri |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 6 categorie |
| Passi | Selezionare ciascuna categoria; confrontare righe e indicatori |
| Risultato atteso | per ognuna delle 6 categorie (dic 2025): 6 righe, indicatori = pandas |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-12 - Filtro esito verifica

| Campo | Descrizione |
|---|---|
| Obiettivo | Filtro esito verifica |
| Requisito / funzione collegata | Filtro esito |
| Area | Filtri |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Sotto soglia / Conforme |
| Passi | Selezionare ciascun esito; confrontare righe e indicatori |
| Risultato atteso | dic 2025: 'Sotto soglia' = 24 righe, 'Conforme' = 12 righe, indicatori = pandas; 'Righe sotto soglia' = 0 con Conforme |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-13 - Filtri combinati

| Campo | Descrizione |
|---|---|
| Obiettivo | Filtri combinati |
| Requisito / funzione collegata | Combinazione di filtri |
| Area | Filtri |
| Precondizioni | TC-09..TC-12 superati |
| Dati / parametri di input | 14 combinazioni pseudo-casuali (seed 24) |
| Passi | Impostare mese, ente, categoria, esito; confrontare righe e indicatori con pandas |
| Risultato atteso | 14 combinazioni pseudo-casuali (seed 24) di mese/ente/categoria/esito: righe e indicatori = pandas |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-14 - Selezione vuota (nessun risultato)

| Campo | Descrizione |
|---|---|
| Obiettivo | Selezione vuota (nessun risultato) |
| Requisito / funzione collegata | Gestione assenza di record |
| Area | Filtri |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Combinazione senza record (ATS Demo Nord / DISINFETTANTI / 2024-01 con esito opposto a quello reale) |
| Passi | Impostare i filtri; verificare messaggio, assenza di tabella/download, indicatori a 0, nessuna eccezione |
| Risultato atteso | nessuna eccezione; messaggio 'Nessun record corrisponde ai filtri selezionati.'; nessuna tabella; nessun pulsante download; indicatori = 0; 7 grafici (nessun grafico del tab Monitoraggio) |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-15 - Indicatori calcolati sui record filtrati

| Campo | Descrizione |
|---|---|
| Obiettivo | Indicatori calcolati sui record filtrati |
| Requisito / funzione collegata | Indicatori sui record filtrati |
| Area | Indicatori |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 2024-06, ASST Demo Est, GUANTI |
| Passi | Filtrare a un solo record; confrontare le 4 metriche con il record del CSV |
| Risultato atteso | indicatori sul solo record filtrato: {'Giacenze rilevate': 12782, 'Quantità minima richiesta': 10745, 'Righe sotto soglia': 0, 'Scorte scadute rilevate': 90} |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-16 - Download CSV dei dati filtrati

| Campo | Descrizione |
|---|---|
| Obiettivo | Download CSV dei dati filtrati |
| Requisito / funzione collegata | Esportazione dati filtrati |
| Area | Download |
| Precondizioni | Tabella non vuota |
| Dati / parametri di input | 5 scenari di filtro |
| Passi | Intercettare i dati passati a download_button; leggere il CSV; confrontare con tabella mostrata e con pandas; verificare BOM, nome file, mime |
| Risultato atteso | 5 scenari: CSV scaricato = tabella filtrata mostrata = filtro pandas; UTF-8 con BOM; nome 'monitoraggio_scorte_panflu.csv'; mime text/csv |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-17 - Selettore indicatore e grafici temporali

| Campo | Descrizione |
|---|---|
| Obiettivo | Selettore indicatore e grafici temporali |
| Requisito / funzione collegata | Andamento storico |
| Area | Grafici |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 4 opzioni del selettore |
| Passi | Selezionare ciascuna opzione; verificare nessuna eccezione e numero di grafici |
| Risultato atteso | 4 opzioni indicatore ['Consumi','Giacenze','Scorte scadute','Quantità minima richiesta']; ogni opzione: nessuna eccezione, 10 grafici |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-18 - Metriche MAE/RMSE/MAPE e confronto metodi (6 categorie)

| Campo | Descrizione |
|---|---|
| Obiettivo | Metriche MAE/RMSE/MAPE e confronto metodi (6 categorie) |
| Requisito / funzione collegata | Applicare e confrontare >= 2 metodi; indicatori d'errore |
| Area | Previsioni |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Default: orizzonte 3, finestra 3, variabilita 1,0, variazione 0% |
| Passi | Per ogni categoria leggere la tabella metriche; confrontare con calcolo indipendente (holdout 4 mesi) |
| Risultato atteso | per 6 categorie (parametri default): MAE/RMSE/MAPE di media mobile e regressione lineare = ricalcolo indipendente (holdout 4 mesi); es. GUANTI MM RMSE 5978.00, LIN RMSE 10339.25, metodo Media mobile semplice |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-19 - Scelta del metodo con RMSE minore

| Campo | Descrizione |
|---|---|
| Obiettivo | Scelta del metodo con RMSE minore |
| Requisito / funzione collegata | Individuare il metodo piu' adatto |
| Area | Previsioni |
| Precondizioni | TC-18 superato |
| Dati / parametri di input | 6 categorie x 3 scenari (variabilita/variazione) |
| Passi | Leggere metriche e messaggio di metodo selezionato; verificare che coincida con RMSE minimo e col riferimento |
| Risultato atteso | 18 scenari (6 categorie x 3): il metodo indicato e' quello con RMSE minore e coincide col riferimento |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-20 - Orizzonte previsivo 1-6 mesi

| Campo | Descrizione |
|---|---|
| Obiettivo | Orizzonte previsivo 1-6 mesi |
| Requisito / funzione collegata | Previsione della domanda |
| Area | Previsioni |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Orizzonte 1..6; GUANTI |
| Passi | Impostare lo slider; verificare righe, mesi consecutivi da 2026-01 e valori |
| Risultato atteso | orizzonte 1..6: tabella con h righe, mesi consecutivi da 2026-01, valori = riferimento; GUANTI h=3: [np.int64(60554), np.int64(61501), np.int64(61260)] |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-21 - Finestra della media mobile 2-6

| Campo | Descrizione |
|---|---|
| Obiettivo | Finestra della media mobile 2-6 |
| Requisito / funzione collegata | Parametri del metodo |
| Area | Previsioni |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Finestra 2..6; GUANTI |
| Passi | Impostare lo slider; confrontare RMSE della media mobile e previsioni col riferimento |
| Risultato atteso | finestra 2..6: RMSE della media mobile e previsioni = riferimento (GUANTI); RMSE MM varia con la finestra |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-22 - Valori limite degli slider di scenario

| Campo | Descrizione |
|---|---|
| Obiettivo | Valori limite degli slider di scenario |
| Requisito / funzione collegata | Modifica delle caratteristiche della domanda |
| Area | Previsioni |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Variabilita 0,5/2,0; variazione -30/+30; orizzonte 1/6; finestra 2/6 |
| Passi | Impostare le 16 combinazioni di estremi; verificare assenza di eccezioni, previsioni >= 0 e valori = riferimento |
| Risultato atteso | estremi degli slider (variabilita 0,5/2,0; variazione -30/+30; orizzonte 1/6; finestra 2/6): nessuna eccezione, previsioni >= 0 e = riferimento |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-23 - Effetto di variabilita e variazione sulle previsioni

| Campo | Descrizione |
|---|---|
| Obiettivo | Effetto di variabilita e variazione sulle previsioni |
| Requisito / funzione collegata | Effetti sulle previsioni |
| Area | Previsioni |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Variazione +30%; variabilita 2,0; GUANTI |
| Passi | Confrontare previsioni/metriche col caso di base |
| Risultato atteso | variazione +30% modifica le previsioni; variabilita 2,0 modifica le metriche di errore |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-24 - Test unitari delle funzioni di previsione e di errore

| Campo | Descrizione |
|---|---|
| Obiettivo | Test unitari delle funzioni di previsione e di errore |
| Requisito / funzione collegata | Correttezza dei metodi |
| Area | Previsioni |
| Precondizioni | Funzioni estratte da app.py via AST |
| Dati / parametri di input | Serie note ([1,2,3], retta y=2x+1, ecc.) |
| Passi | Eseguire le funzioni con valori a risultato noto e confrontare |
| Risultato atteso | MM [1,2,3] h1 = 2; MM ricorsiva; LIN su retta = 9, 11; clamp a 0; metriche MAE 15, RMSE 15,81, MAPE 10 per ([100,200],[110,180]) |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-25 - Casi limite: MAPE con zeri e serie corte

| Campo | Descrizione |
|---|---|
| Obiettivo | Casi limite: MAPE con zeri e serie corte |
| Requisito / funzione collegata | Robustezza del calcolo |
| Area | Casi limite |
| Precondizioni | Come TC-24 |
| Dati / parametri di input | Reali = 0; serie di 1-2 punti |
| Passi | Eseguire error_metrics, moving_average_forecast e linear_forecast sui casi limite |
| Risultato atteso | MAPE con tutti i reali = 0 -> NaN (no divisione per zero, no eccezione); con un reale = 0 viene escluso (MAPE 10); serie di 1-2 punti gestite senza eccezioni; MAE/RMSE finiti |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-26 - Holdout cronologico test_n = min(4, max(2, n//5))

| Campo | Descrizione |
|---|---|
| Obiettivo | Holdout cronologico test_n = min(4, max(2, n//5)) |
| Requisito / funzione collegata | Valutazione dell'accuratezza |
| Area | Previsioni |
| Precondizioni | TC-18 superato |
| Dati / parametri di input | ATS Demo Sud, DISINFETTANTI; n = 24 |
| Passi | Calcolare test_n; confrontare RMSE dashboard con riferimento a 4 mesi e a 2 mesi |
| Risultato atteso | holdout = min(4, max(2, n//5)): n=24 -> 4 mesi finali; RMSE MM del riferimento a 4 mesi coincide con la dashboard (e differisce da quello a 2 mesi) |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-27 - Componenti di scorta - GUANTI (caso di riferimento)

| Campo | Descrizione |
|---|---|
| Obiettivo | Componenti di scorta - GUANTI (caso di riferimento) |
| Requisito / funzione collegata | Scorte cicliche, di sicurezza, anticipate, pipeline |
| Area | Componenti di scorta |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | GUANTI, lead time 30, livello 0,95, variabilita 1,0, orizzonte 3, finestra 3 |
| Passi | Leggere la tabella Componenti; confrontare con le formule ricalcolate |
| Risultato atteso | GUANTI, lead 30, livello 0,95, variabilita 1,0, orizzonte 3, finestra 3: Ciclica 31,144.6, Sicurezza 2,363.4, Anticipata 543.5, Pipeline 62,289.3 |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-28 - Componenti di scorta - tutte le categorie e piu' enti

| Campo | Descrizione |
|---|---|
| Obiettivo | Componenti di scorta - tutte le categorie e piu' enti |
| Requisito / funzione collegata | Scorte per tipologia |
| Area | Componenti di scorta |
| Precondizioni | TC-27 superato |
| Dati / parametri di input | 6 categorie x (Tutti, ATS Demo Nord, AREU); lead 60, livello 0,99, variabilita 1,5 |
| Passi | Impostare i parametri; confrontare le 4 componenti col riferimento |
| Risultato atteso | 6 categorie x 3 selezioni ente (tutti, ATS Demo Nord, AREU) con lead 60, livello 0,99, variabilita 1,5: 4 componenti = formule di riferimento |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-29 - Monotonia rispetto al lead time

| Campo | Descrizione |
|---|---|
| Obiettivo | Monotonia rispetto al lead time |
| Requisito / funzione collegata | Effetto del lead time sulle scorte |
| Area | Componenti di scorta |
| Precondizioni | TC-27 superato |
| Dati / parametri di input | Lead time 7..120 (passo 7), GUANTI |
| Passi | Eseguire per ogni valore; verificare crescita di sicurezza e pipeline e costanza della ciclica |
| Risultato atteso | lead time 7..119 (passo 7) e 120: Sicurezza e Pipeline strettamente crescenti; Ciclica costante; Anticipata non decrescente |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-30 - Monotonia rispetto al livello di servizio

| Campo | Descrizione |
|---|---|
| Obiettivo | Monotonia rispetto al livello di servizio |
| Requisito / funzione collegata | Effetto del livello di servizio |
| Area | Componenti di scorta |
| Precondizioni | TC-27 superato |
| Dati / parametri di input | Livello 0,90/0,95/0,975/0,99, GUANTI |
| Passi | Eseguire per ogni livello; verificare crescita della sicurezza e rapporto z |
| Risultato atteso | Sicurezza strettamente crescente con il livello di servizio (rapporto 0,99/0,90 = 2,326/1,282 = 1,814); altre componenti invariate |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-31 - Effetto della variabilita sulle scorte

| Campo | Descrizione |
|---|---|
| Obiettivo | Effetto della variabilita sulle scorte |
| Requisito / funzione collegata | Effetto della variabilita |
| Area | Componenti di scorta |
| Precondizioni | TC-27 superato |
| Dati / parametri di input | Variabilita 0,5/1,0/2,0, GUANTI |
| Passi | Verificare proporzionalita della sicurezza e invarianza delle altre componenti |
| Risultato atteso | variabilita 0,5/1,0/2,0: Sicurezza proporzionale (2,0 = 4 x 0,5); altre componenti invariate |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-32 - Formule di scorta ciclica e pipeline su tutte le categorie

| Campo | Descrizione |
|---|---|
| Obiettivo | Formule di scorta ciclica e pipeline su tutte le categorie |
| Requisito / funzione collegata | Criteri di calcolo definiti |
| Area | Componenti di scorta |
| Precondizioni | TC-27 superato |
| Dati / parametri di input | 6 categorie, lead 45 |
| Passi | Confrontare pipeline = d x 45 e ciclica = d x 15 (d = domanda giornaliera media ultimi 6 mesi) |
| Risultato atteso | per ogni categoria (lead 45): Pipeline = domanda media giornaliera (ultimi 6 mesi/30,4375) x 45; Ciclica = domanda giornaliera x 15; nessuna componente negativa |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-33 - Robustezza: combinazioni estreme di tutti gli slider

| Campo | Descrizione |
|---|---|
| Obiettivo | Robustezza: combinazioni estreme di tutti gli slider |
| Requisito / funzione collegata | Nessuna eccezione |
| Area | Robustezza |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 32 combinazioni degli estremi (orizzonte, finestra, variabilita, variazione, lead) con livello e categoria ruotati |
| Passi | Eseguire ciascuna combinazione; verificare nessuna eccezione e componenti finite e >= 0 |
| Risultato atteso | 32 combinazioni degli estremi di tutti gli slider (con livello di servizio e categoria ruotati): nessuna eccezione, componenti finite e >= 0 |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-34 - CSV mancante, colonna mancante, CSV vuoto

| Campo | Descrizione |
|---|---|
| Obiettivo | CSV mancante, colonna mancante, CSV vuoto |
| Requisito / funzione collegata | Gestione errori sui dati |
| Area | Casi limite |
| Precondizioni | Copia di app.py in cartella temporanea |
| Dati / parametri di input | File assente; colonna giacenza_pezzi rimossa; solo intestazione |
| Passi | Eseguire l'app su ciascuna variante: attesi st.error guidato in italiano, nessuna eccezione, nessuna scheda (v1.0: documentava le eccezioni non gestite) |
| Risultato atteso | file monitoraggio mancante, colonna giacenza_pezzi mancante, solo intestazione: st.error guidato in italiano, nessuna eccezione, nessuna scheda |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-35 - Coerenza dei file dati distribuiti con l'app

| Campo | Descrizione |
|---|---|
| Obiettivo | Coerenza dei file dati distribuiti con l'app |
| Requisito / funzione collegata | Repository con codice, dati e file necessari |
| Area | Requisiti traccia |
| Precondizioni | Codice sorgente app.py |
| Dati / parametri di input | app.py, data/*.csv |
| Passi | Cercare in app.py l'uso di domanda_storica.csv e parametri_scorte.csv |
| Risultato atteso | tracciabilita' dati: l'app usa domanda_storica.csv e parametri_scorte.csv presenti in data/ e il README li documenta |
| Tipo | Automatico |
| Priorita' | Bassa |

#### TC-36 - Almeno 4 serie con andamenti diversi e almeno 2 metodi

| Campo | Descrizione |
|---|---|
| Obiettivo | Almeno 4 serie con andamenti diversi e almeno 2 metodi |
| Requisito / funzione collegata | Traccia: >= 4 articoli, >= 2 metodi |
| Area | Requisiti traccia |
| Precondizioni | TC-18 superato |
| Dati / parametri di input | 6 categorie |
| Passi | Contare categorie e metodi; calcolare la pendenza di ciascuna serie |
| Risultato atteso | >= 4 serie storiche di consumo (6 categorie) con andamenti differenti; >= 2 metodi previsionali confrontati con indicatori d'errore |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-37 - Controlli di scenario richiesti dalla traccia

| Campo | Descrizione |
|---|---|
| Obiettivo | Controlli di scenario richiesti dalla traccia |
| Requisito / funzione collegata | Modificare variabilita, trend, stagionalita, lead time |
| Area | Requisiti traccia |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Etichette degli slider |
| Passi | Elencare i controlli della barra laterale e verificare la presenza dei quattro elementi |
| Risultato atteso | traccia: la dashboard consente di modificare variabilita, trend, stagionalita e lead time (esempi indicati dalla traccia) |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-38 - Effetto del trend sulle componenti di scorta

| Campo | Descrizione |
|---|---|
| Obiettivo | Effetto del trend sulle componenti di scorta |
| Requisito / funzione collegata | Effetti delle caratteristiche della domanda sulle scorte |
| Area | Requisiti traccia |
| Precondizioni | TC-27 superato |
| Dati / parametri di input | Variazione 0% e +30%, GUANTI |
| Passi | Confrontare le componenti nei due scenari |
| Risultato atteso | traccia: gli effetti delle caratteristiche della domanda (trend) sono mostrati anche sulle diverse tipologie di scorte: con +30% almeno una componente dovrebbe cambiare |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-39 - Tempo di esecuzione dello script

| Campo | Descrizione |
|---|---|
| Obiettivo | Tempo di esecuzione dello script |
| Requisito / funzione collegata | Prestazioni minime |
| Area | Non funzionali |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 3 esecuzioni, soglia 10 s |
| Passi | Misurare il tempo di una esecuzione completa con AppTest |
| Risultato atteso | esecuzione completa dello script con parametri default in <= 10 s (AppTest, esclusa l'apertura del browser) |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-40 - Avvio del server Streamlit (porta 8503)

| Campo | Descrizione |
|---|---|
| Obiettivo | Avvio del server Streamlit (porta 8503) |
| Requisito / funzione collegata | Avvio |
| Area | Non funzionali |
| Precondizioni | Porta 8503 libera |
| Dati / parametri di input | streamlit run app.py --server.headless true |
| Passi | Avviare il server; interrogare /_stcore/health e la pagina principale; arrestare il server |
| Risultato atteso | avvio con 'streamlit run' su porta 8503: endpoint /_stcore/health = 'ok' e pagina principale HTTP 200 entro 40 s; server poi arrestato |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-41 - Ripetibilita (determinismo)

| Campo | Descrizione |
|---|---|
| Obiettivo | Ripetibilita (determinismo) |
| Requisito / funzione collegata | Stabilita dei risultati |
| Area | Non funzionali |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | GUANTI, AREU, 2025-06 |
| Passi | Eseguire due volte; confrontare indicatori, metriche, componenti |
| Risultato atteso | due esecuzioni identiche producono indicatori, metriche e componenti identici (determinismo) |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-42 - Indici stagionali

| Campo | Descrizione |
|---|---|
| Obiettivo | Indici stagionali |
| Requisito / funzione collegata | Stagionalita' modificabile (v1.1) |
| Area | Stagionalita' |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 6 categorie, 4 articoli |
| Passi | Confrontare indici dell'app con un ricalcolo indipendente; verificare intensita' 0 neutra |
| Risultato atteso | indici stagionali di 6 categorie e 4 articoli: 12 valori, media 1, = riferimento indipendente; tabella dell'app = riferimento; intensita' 0 -> fattore 1,0 e risultati = default (TC-18/27) |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-43 - Stagionalita' sulle previsioni

| Campo | Descrizione |
|---|---|
| Obiettivo | Stagionalita' sulle previsioni |
| Requisito / funzione collegata | Stagionalita' modificabile (v1.1) |
| Area | Stagionalita' |
| Precondizioni | TC-42 superato |
| Dati / parametri di input | Intensita' 0,5 e 1,0 |
| Passi | Confrontare metriche, metodo e previsioni con il riferimento indipendente |
| Risultato atteso | stagionalita' 0,5 e 1,0 su 6 categorie (+2 scenari misti): metriche, metodo e previsioni = riferimento indipendente; con intensita' 1 le previsioni GUANTI differiscono dal default |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-44 - Stagionalita' sulle componenti di scorta

| Campo | Descrizione |
|---|---|
| Obiettivo | Stagionalita' sulle componenti di scorta |
| Requisito / funzione collegata | Effetti sulle scorte (v1.1) |
| Area | Stagionalita' |
| Precondizioni | TC-42 superato |
| Dati / parametri di input | Intensita' 0,5 e 1,0 |
| Passi | Confrontare le componenti con il riferimento; verificare linearita' di ciclica e pipeline |
| Risultato atteso | componenti di scorta con stagionalita' 0,5 e 1,0 su 6 categorie = riferimento; Ciclica e Pipeline lineari in s; con s=1 almeno una componente cambia |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-45 - Variazione simulata sulle componenti di scorta

| Campo | Descrizione |
|---|---|
| Obiettivo | Variazione simulata sulle componenti di scorta |
| Requisito / funzione collegata | Effetti sulle scorte (v1.1) |
| Area | Scenario |
| Precondizioni | TC-27 superato |
| Dati / parametri di input | Variazione -30/0/+30% |
| Passi | Confrontare le componenti con il riferimento; la variabilita' modifica solo la sicurezza |
| Risultato atteso | trend -30/0/+30: componenti = riferimento; Ciclica e Pipeline crescenti con il trend; la variabilita' modifica solo la Sicurezza (proporzionale) anche con trend e stagionalita' attivi |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-46 - Scheda Articoli e parametri

| Campo | Descrizione |
|---|---|
| Obiettivo | Scheda Articoli e parametri |
| Requisito / funzione collegata | 4 articoli da domanda_storica.csv e parametri_scorte.csv (v1.1) |
| Area | Articoli |
| Precondizioni | TC-05 superato |
| Dati / parametri di input | Default e scenario |
| Passi | Confrontare tabelle e previsioni con un ricalcolo pandas indipendente |
| Risultato atteso | scheda articoli: parametri, confronto metodi (MAE/RMSE/MAPE, selezionato), componenti (lead e livello da parametri_scorte.csv, copertura) e previsioni di dettaglio = ricalcolo pandas indipendente da domanda_storica.csv e parametri_scorte.csv, in default e in scenario (trend 20, s 0,5, var 1,5, orizzonte 4, finestra 4); slider lead time ininfluente |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-47 - mesi_stagionali come moltiplicatore per articolo

| Campo | Descrizione |
|---|---|
| Obiettivo | mesi_stagionali come moltiplicatore per articolo |
| Requisito / funzione collegata | Stagionalita' per articolo (v1.1) |
| Area | Articoli |
| Precondizioni | TC-46 superato |
| Dati / parametri di input | Slider 1,0; valori 0,5/0/1,0 |
| Passi | Verificare che l'intensita' effettiva segua il parametro dell'articolo |
| Risultato atteso | mesi_stagionali come moltiplicatore dell'intensita': slider 1,0 con Guanti 0,5, Kit medicazione 0, altri 1,0 -> Guanti = intensita' 0,5, Kit = intensita' 0, altri = intensita' 1,0 (app con CSV originali) |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-48 - Validazione CSV: file, colonne, vuoti

| Campo | Descrizione |
|---|---|
| Obiettivo | Validazione CSV: file, colonne, vuoti |
| Requisito / funzione collegata | Messaggi guidati (v1.1) |
| Area | Validazione |
| Precondizioni | Copia dell'app |
| Dati / parametri di input | 3 CSV: mancante, colonna mancante, solo intestazione, 0 byte |
| Passi | Eseguire l'app sulle varianti: un solo st.error in italiano, nessuna eccezione |
| Risultato atteso | per ciascuno dei 3 CSV: file mancante, colonna mancante, solo intestazione, file a 0 byte -> un solo st.error in italiano con nome file/colonna, nessuna eccezione, nessuna scheda |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-49 - Validazione CSV: valori non validi

| Campo | Descrizione |
|---|---|
| Obiettivo | Validazione CSV: valori non validi |
| Requisito / funzione collegata | Messaggi guidati (v1.1) |
| Area | Validazione |
| Precondizioni | Copia dell'app |
| Dati / parametri di input | 17 varianti (negativi, testo, mesi, duplicati, serie corte, ...) |
| Passi | Eseguire l'app: messaggio specifico e stop |
| Risultato atteso | valori non validi (numero negativo, testo in colonna numerica, mese 2024-13/abc, duplicati, id vuoto, data non valida, serie < 12 mesi, buco nella serie, articoli incoerenti, livello servizio 0/1, lead time 0, scorta negativa): messaggio italiano specifico + stop |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-50 - Funzioni nuove (unitari)

| Campo | Descrizione |
|---|---|
| Obiettivo | Funzioni nuove (unitari) |
| Requisito / funzione collegata | Correttezza delle funzioni (v1.1) |
| Area | Stagionalita' |
| Precondizioni | Funzioni estratte da app.py |
| Dati / parametri di input | Serie sintetiche |
| Passi | Verificare indici, fattori, rampa, z-score e componenti a scenario neutro |
| Risultato atteso | funzioni nuove: seasonal_indices recupera il profilo 1,2/0,8 (media 1; <12 punti -> 1), seasonal_factor neutro a 0 e clippato, trend_series (rampa, clamp), z_score (tabella + NormalDist), stock_components = formula originale a s=0/trend=0, serie vuota -> zeri |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-51 - Robustezza dei nuovi controlli

| Campo | Descrizione |
|---|---|
| Obiettivo | Robustezza dei nuovi controlli |
| Requisito / funzione collegata | Robustezza (v1.1) |
| Area | Casi limite |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | 32 combinazioni estreme |
| Passi | Eseguire l'app: nessuna eccezione, valori finiti e non negativi |
| Risultato atteso | 32 combinazioni estreme con i nuovi controlli (stagionalita' 0/1, variazione +-30, variabilita 0,5/2, lead 7/120, orizzonte/finestra 1-2/6-6, categorie, enti e livelli ruotati): nessuna eccezione, componenti e vista articoli finite e >= 0, previsioni >= 0 |
| Tipo | Automatico |
| Priorita' | Media |

#### TC-52 - Valori di default invariati

| Campo | Descrizione |
|---|---|
| Obiettivo | Valori di default invariati |
| Requisito / funzione collegata | Default come v1.0 |
| Area | Regressione |
| Precondizioni | TC-06 superato |
| Dati / parametri di input | Parametri di default |
| Passi | Confrontare i valori noti della v1.0 con quelli ottenuti |
| Risultato atteso | valori di default invariati nella v1.1: {'righe': 864, 'sotto_soglia': 525, 'perc': 60.8, 'scadute_tot': 47036, 'dic_sotto': 24, 'dic_righe': 36, 'scadute_dic': 1863, 'g_rmse_ma': 5978, 'g_rmse_lin': 10339, 'g_mape_ma': 9.2, 'g_mape_lin': 16.7, 'd_rmse_ma': 447, 'd_rmse_lin': 647, 'comp': {'Ciclica': 31145, 'Sicurezza': 2363, 'Anticipata': 543, 'Pipeline': 62289}, 'titolo': 'Monitoraggio delle scorte pandemiche', 'slider_stagionalita': ('Intensità stagionalità (0 = neutra)', 0.0)} |
| Tipo | Automatico |
| Priorita' | Alta |

#### TC-53 - Compatibilita' e documentazione

| Campo | Descrizione |
|---|---|
| Obiettivo | Compatibilita' e documentazione |
| Requisito / funzione collegata | A-05 e README/NOTE (v1.1) |
| Area | Non funzionali |
| Precondizioni | File del progetto |
| Dati / parametri di input | app.py, requirements.txt, README, NOTE |
| Passi | Verificare assenza di use_container_width, versioni fissate e coerenza della documentazione |
| Risultato atteso | A-05 e documentazione: nessun use_container_width in app.py; requirements.txt con 4 versioni esatte (==) uguali a quelle installate; README con sottocartella di avvio, 3 CSV, versioni testate (3.14); NOTE.txt aggiornata |
| Tipo | Automatico |
| Priorita' | Bassa |

## 6. Casi di test manuali (da eseguire con browser)

Precondizione comune: dashboard in esecuzione (es. http://localhost:8501) con i dati demo. Per ogni voce annotare esito (OK / KO) e note. Questi casi NON sono stati eseguiti dal sistema automatico.

#### TM-01 - Titolo e intestazione

Passi: Aprire http://localhost:8501 in un browser.

| Verifica | OK | KO | Note |
|---|---|---|---|
| Il titolo 'Monitoraggio delle scorte pandemiche' e' visibile in cima alla pagina | [ ] | [ ] |  |
| La didascalia con 'PW 24' e' leggibile | [ ] | [ ] |  |
| L'avviso di prototipo didattico e' ben visibile e comprensibile | [ ] | [ ] |  |

Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________

#### TM-02 - Layout generale e barra laterale

Passi: Ridimensionare la finestra (ampia / stretta) e osservare layout e barra laterale.

| Verifica | OK | KO | Note |
|---|---|---|---|
| Le 4 metriche sono affiancate e non troncate | [ ] | [ ] |  |
| La barra laterale e' ordinata (filtri, scenario) | [ ] | [ ] |  |
| Nessuna sovrapposizione di elementi a larghezza ridotta | [ ] | [ ] |  |
| Le tab sono navigabili | [ ] | [ ] |  |

Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________

#### TM-03 - Leggibilita' dei grafici del tab Monitoraggio

Passi: Aprire il tab Monitoraggio e osservare i tre grafici.

| Verifica | OK | KO | Note |
|---|---|---|---|
| Assi, titoli e legende leggibili | [ ] | [ ] |  |
| Colori Conforme (verde) / Sotto soglia (rosso) distinguibili | [ ] | [ ] |  |
| Il passaggio del mouse mostra i valori (tooltip) | [ ] | [ ] |  |

Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________

#### TM-04 - Leggibilita' dei grafici temporali e della previsione

Passi: Aprire il tab 'Analisi temporale e previsione'.

| Verifica | OK | KO | Note |
|---|---|---|---|
| Linea storica e previsione distinguibili (serie e colori) | [ ] | [ ] |  |
| Asse dei mesi leggibile | [ ] | [ ] |  |
| Il cambio di indicatore aggiorna il grafico | [ ] | [ ] |  |

Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________

#### TM-05 - Formato dei numeri e delle tabelle

Passi: Controllare tabelle e indicatori.

| Verifica | OK | KO | Note |
|---|---|---|---|
| Separatori delle migliaia/decimali coerenti nelle metriche (nota: le metriche usano il formato inglese 12,345) | [ ] | [ ] |  |
| Le colonne della tabella hanno nomi in italiano e sono leggibili | [ ] | [ ] |  |
| Valori arrotondati in modo comprensibile | [ ] | [ ] |  |

Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________

#### TM-06 - Download del CSV dal browser

Passi: Cliccare 'Scarica i dati filtrati in CSV' con un filtro attivo.

| Verifica | OK | KO | Note |
|---|---|---|---|
| Il file si scarica con nome monitoraggio_scorte_panflu.csv | [ ] | [ ] |  |
| Il file si apre in Excel con accenti corretti | [ ] | [ ] |  |
| Il contenuto coincide con la tabella a video | [ ] | [ ] |  |

Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________

#### TM-07 - Tab Componenti di scorta e messaggi informativi

Passi: Aprire il tab 'Componenti di scorta' e variare gli slider.

| Verifica | OK | KO | Note |
|---|---|---|---|
| Le 4 componenti sono comprensibili e il grafico si aggiorna | [ ] | [ ] |  |
| Il messaggio che le componenti non vanno sommate e' visibile | [ ] | [ ] |  |
| I criteri dimostrativi sono leggibili | [ ] | [ ] |  |

Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________

#### TM-08 - Usabilita' e comprensibilita' generale

Passi: Far utilizzare la dashboard a una persona non coinvolta nello sviluppo.

| Verifica | OK | KO | Note |
|---|---|---|---|
| I filtri e gli slider sono comprensibili senza spiegazioni | [ ] | [ ] |  |
| Le etichette sono in italiano corretto | [ ] | [ ] |  |
| Nessun errore a video durante l'uso | [ ] | [ ] |  |
| Sezione 'Assunzioni, perimetro e limiti' letta e compresa | [ ] | [ ] |  |

Esito complessivo: [ ] OK  [ ] KO     Eseguito da: ________  Data: ________

## 7. Matrice di tracciabilita' requisiti - casi di test

| Rif. | Requisito / funzione | Casi di test |
|---|---|---|
| R1 | Serie storiche di almeno quattro articoli con andamenti differenti | TC-01, TC-02, TC-05, TC-36 |
| R2 | Almeno due metodi previsionali applicati | TC-18, TC-24, TC-36 |
| R3 | Valutazione accuratezza con indicatori d'errore (MAE, RMSE, MAPE) | TC-18, TC-24, TC-25, TC-26 |
| R4 | Individuazione del metodo piu' adatto | TC-19 |
| R5 | Stima delle scorte cicliche, di sicurezza, anticipate, pipeline | TC-27, TC-28, TC-32 |
| R6 | Dashboard: modifica di variabilita, trend, stagionalita, lead time | TC-22, TC-23, TC-37, TC-42, TC-43, TC-47 |
| R7 | Effetti degli scenari sulle diverse tipologie di scorte | TC-29, TC-30, TC-31, TC-38, TC-44, TC-45 |
| R8 | Mostrare andamento storico e previsto della domanda | TC-17, TC-20, TC-21, TM-04 |
| R9 | Mostrare confronto di accuratezza dei metodi | TC-18, TC-19 |
| R10 | Mostrare composizione delle scorte nei diversi scenari | TC-27, TC-33, TM-07 |
| R11 | Codice, dati e file necessari all'esecuzione | TC-05, TC-35, TC-40, TC-46, TC-53 |
| F1 | Monitoraggio: esito giacenza vs quantita' minima | TC-04, TC-07, TC-08 |
| F2 | Filtri (mese, ente, categoria, esito), anche combinati e vuoti | TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15 |
| F3 | Esportazione CSV dei dati filtrati | TC-16, TM-06 |
| N1 | Avvio, prestazioni, stabilita', robustezza | TC-06, TC-33, TC-34, TC-39, TC-40, TC-41, TC-48, TC-49, TC-51, TC-52 |
| N2 | Aspetti visivi e usabilita' | TM-01, TM-02, TM-03, TM-05, TM-08 |

## 8. Come eseguire i test automatici

```
.venv\Scripts\python.exe -m pytest test/test_dashboard.py -v --junitxml=test/results/junit.xml
```

Prerequisiti: ambiente .venv con streamlit, pandas, numpy, plotly, pytest. Non e' necessario che la dashboard sia in esecuzione; il caso TC-40 usa la porta 8503.
