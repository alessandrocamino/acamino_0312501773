# Test Report - Dashboard PW24 'Monitoraggio delle scorte pandemiche'

**Esito dell'esecuzione del Test Book (versione 1.1)**

Versione 1.1 - 21/11/2026 - Progetto PW 24 (Pegaso L-31)

## 1. Ambiente di esecuzione

| Voce | Valore |
|---|---|
| Sistema operativo | Windows 11 (10.0.22631) |
| Python | 3.14.2 |
| Streamlit | 1.67.0 |
| pandas | 3.1.1 |
| NumPy | 2.5.5 |
| Plotly | 7.1.0 |
| pytest | 8.3.4 |
| python-docx (solo documenti) | 1.1.2 |
| Applicazione sotto test | acamino_0312501773\PW24_dashboard_sanitario\app.py (sola lettura) |
| Metodo di esecuzione | streamlit.testing.v1.AppTest (headless) + avvio server su porta 8503 (TC-40) |
| Esecuzione (una sola) | 2026-11-21 23:14:39 - durata 266 s |

## 2. Riepilogo

| Indicatore | Valore |
|---|---|
| Test pianificati (totale) | 61 |
| Test automatici pianificati | 53 |
| Test automatici eseguiti | 53 |
| Passati (PASS) | 53 |
| Falliti (FAIL) | 0 |
| Non eseguiti - manuali (NON ESEGUITO) | 8 |
| Numero di esecuzioni | una sola esecuzione |

Sono stati eseguiti 53 test automatici su 53: 53 passati e 0 falliti, in una sola esecuzione. I 8 casi manuali (TM-01, TM-02, TM-03, TM-04, TM-05, TM-06, TM-07, TM-08) non sono stati eseguiti e restano da compilare.

Differenze rispetto alla versione 1.0 (41 test automatici: 38 PASS, 3 FAIL: TC-35, TC-37, TC-38): l'app e' stata aggiornata (stagionalita', effetto di variazione e stagionalita' sulle componenti, scheda 'Articoli e parametri', validazione dei CSV). TC-35, TC-37 e TC-38 ora risultano PASS con asserzioni invariate; TC-34 e' stato adattato ai nuovi messaggi guidati; TC-06 e i conteggi dei grafici sono stati allineati alla quarta scheda; sono presenti i casi aggiunti TC-42..TC-53 (12 casi).

## 3. Risultati per caso di test

| ID | Titolo | Esito | Valore atteso | Valore ottenuto | Tempo (s) |
|---|---|---|---|---|---|
| TC-01 | Struttura del CSV di monitoraggio | PASS | 864 righe; colonne id_ente, tipologia_ente, categoria_panflu, mese_riferimento, consumo_mensile_pezzi, quantita_minima_richiesta, giacenza_pezzi, scorte_scadute_pezzi | 864 righe; colonne ['id_ente', 'tipologia_ente', 'categoria_panflu', 'mese_riferimento', 'consumo_mensile_pezzi', 'quantita_minima_richiesta', 'giacenza_pezzi', 'scorte_scadute_pezzi'] | 0.00 |
| TC-02 | Integrita' dei dati (nulli, duplicati, completezza) | PASS | 0 nulli; 0 duplicati sulla chiave; 6 enti x 6 categorie x 24 mesi = 864 | 0 nulli; 0 duplicati; 6 x 6 x 24 = 864 | 0.00 |
| TC-03 | Validita' dei valori | PASS | 0 valori negativi; 0 quantita minime <= 0; 0 righe con scadute > giacenza; mesi formato AAAA-MM | negativi=0; minime<=0: 0; scadute>giacenza: 0; formato mese ok=True | 0.00 |
| TC-04 | Totali di esito sull'intero dataset | PASS | 525 sotto soglia su 864 = 60,8%; scorte scadute totali 47.036; 1 riga con giacenza = minima | 525 su 864 = 60.8%; scadute totali 47036; righe uguali 1 | 0.00 |
| TC-05 | File ausiliari (domanda storica, parametri scorte) | PASS | domanda_storica.csv 144 righe, 4 articoli, colonne data/articolo/domanda; parametri_scorte.csv 4 righe | domanda (144, 3), articoli=4, colonne=['data', 'articolo', 'domanda']; parametri (4, 7) | 0.00 |
| TC-06 | Avvio dell'app e struttura della pagina | PASS | nessuna eccezione; titolo 'Monitoraggio delle scorte pandemiche'; 4 tab (3 originali + 'Articoli e parametri'); 4 indicatori; 10 grafici; avviso prototipo | eccezioni=0; titolo='Monitoraggio delle scorte pandemiche'; tab=['Monitoraggio', 'Analisi temporale e previsione', 'Componenti di scorta', 'Articoli e parametri']; indicatori=4; grafici=10; warning=1 | 1.36 |
| TC-07 | Indicatori e tabella di default (dicembre 2025) | PASS | dicembre 2025: {'Giacenze rilevate': 155978, 'Quantità minima richiesta': 227480, 'Righe sotto soglia': 24, 'Scorte scadute rilevate': 1863}; 36 righe in tabella, 24 sotto soglia, 12 conformi | {'Giacenze rilevate': 155978, 'Quantità minima richiesta': 227480, 'Righe sotto soglia': 24, 'Scorte scadute rilevate': 1863}; righe tabella=36; esiti={'Sotto soglia': 24, 'Conforme': 12} | 0.77 |
| TC-08 | Logica dell'esito (giacenza >= minima) | PASS | esito = Conforme se giacenza >= quantita minima, altrimenti Sotto soglia, su 24 mesi (864 righe); riga al limite (giacenza = minima) = Conforme | righe verificate=864; incoerenze=0; riga limite IRCCS Demo/COPRICAPO/2024-11 -> Conforme | 19.56 |
| TC-09 | Filtro mese di riferimento | PASS | per ognuno dei 24 mesi: 36 righe, solo il mese scelto, indicatori = pandas | errori: 0 | 0.06 |
| TC-10 | Filtro ente | PASS | per ognuno dei 6 enti (dic 2025): 6 righe, indicatori = pandas | errori: 0 | 4.91 |
| TC-11 | Filtro tipologia dispositivo (categoria) | PASS | per ognuna delle 6 categorie (dic 2025): 6 righe, indicatori = pandas | errori: 0 | 5.17 |
| TC-12 | Filtro esito verifica | PASS | dic 2025: 'Sotto soglia' = 24 righe, 'Conforme' = 12 righe, indicatori = pandas; 'Righe sotto soglia' = 0 con Conforme | righe {'Sotto soglia': 24, 'Conforme': 12}; errori 0 | 1.64 |
| TC-13 | Filtri combinati | PASS | 14 combinazioni pseudo-casuali (seed 24) di mese/ente/categoria/esito: righe e indicatori = pandas | combinazioni=14; errori=0 | 11.77 |
| TC-14 | Selezione vuota (nessun risultato) | PASS | nessuna eccezione; messaggio 'Nessun record corrisponde ai filtri selezionati.'; nessuna tabella; nessun pulsante download; indicatori = 0; 7 grafici (nessun grafico del tab Monitoraggio) | eccezioni=0; info=['Nessun record corrisponde ai filtri selezionati.', "Queste componenti sono un'estensione didattica della traccia PW24. Non equivalgono alla quantità minima PANFLU definita a livello regionale e non devono essere sommate automaticamente: le definizioni possono sovrapporsi."]; tabella_esito=False; download=False; indicatori={'Giacenze rilevate': 0, 'Quantità minima richiesta': 0, 'Righe sotto soglia': 0, 'Scorte scadute rilevate': 0}; grafici=7 | 0.71 |
| TC-15 | Indicatori calcolati sui record filtrati | PASS | indicatori sul solo record filtrato: {'Giacenze rilevate': 12782, 'Quantità minima richiesta': 10745, 'Righe sotto soglia': 0, 'Scorte scadute rilevate': 90} | {'Giacenze rilevate': 12782, 'Quantità minima richiesta': 10745, 'Righe sotto soglia': 0, 'Scorte scadute rilevate': 90} | 0.99 |
| TC-16 | Download CSV dei dati filtrati | PASS | 5 scenari: CSV scaricato = tabella filtrata mostrata = filtro pandas; UTF-8 con BOM; nome 'monitoraggio_scorte_panflu.csv'; mime text/csv | scenari=5; errori=0 | 4.11 |
| TC-17 | Selettore indicatore e grafici temporali | PASS | 4 opzioni indicatore ['Consumi','Giacenze','Scorte scadute','Quantità minima richiesta']; ogni opzione: nessuna eccezione, 10 grafici | opzioni=['Consumi', 'Giacenze', 'Scorte scadute', 'Quantità minima richiesta']; errori=0 | 5.17 |
| TC-18 | Metriche MAE/RMSE/MAPE e confronto metodi (6 categorie) | PASS | per 6 categorie (parametri default): MAE/RMSE/MAPE di media mobile e regressione lineare = ricalcolo indipendente (holdout 4 mesi); es. GUANTI MM RMSE 5978.00, LIN RMSE 10339.25, metodo Media mobile semplice | errori=0 | 4.87 |
| TC-19 | Scelta del metodo con RMSE minore | PASS | 18 scenari (6 categorie x 3): il metodo indicato e' quello con RMSE minore e coincide col riferimento | errori=0; metodi scelti osservati=['Media mobile semplice', 'Regressione lineare'] | 14.23 |
| TC-20 | Orizzonte previsivo 1-6 mesi | PASS | orizzonte 1..6: tabella con h righe, mesi consecutivi da 2026-01, valori = riferimento; GUANTI h=3: [np.int64(60554), np.int64(61501), np.int64(61260)] | errori=0 | 4.95 |
| TC-21 | Finestra della media mobile 2-6 | PASS | finestra 2..6: RMSE della media mobile e previsioni = riferimento (GUANTI); RMSE MM varia con la finestra | RMSE MM per finestra={2: 5914.92, 3: 5978.0, 4: 7445.5, 5: 9148.23, 6: 10641.87}; errori=0 | 3.94 |
| TC-22 | Valori limite degli slider di scenario | PASS | estremi degli slider (variabilita 0,5/2,0; variazione -30/+30; orizzonte 1/6; finestra 2/6): nessuna eccezione, previsioni >= 0 e = riferimento | combinazioni=8; errori=0 | 6.28 |
| TC-23 | Effetto di variabilita e variazione sulle previsioni | PASS | variazione +30% modifica le previsioni; variabilita 2,0 modifica le metriche di errore | previsioni base [60554, 61501, 61260] vs +30%: [77947, 79424, 79205]; RMSE base [5978.0, 10339.25] vs var 2,0: [5590.29, 10870.88] | 2.50 |
| TC-24 | Test unitari delle funzioni di previsione e di errore | PASS | MM [1,2,3] h1 = 2; MM ricorsiva; LIN su retta = 9, 11; clamp a 0; metriche MAE 15, RMSE 15,81, MAPE 10 per ([100,200],[110,180]) | errori=0 | 0.01 |
| TC-25 | Casi limite: MAPE con zeri e serie corte | PASS | MAPE con tutti i reali = 0 -> NaN (no divisione per zero, no eccezione); con un reale = 0 viene escluso (MAPE 10); serie di 1-2 punti gestite senza eccezioni; MAE/RMSE finiti | tutti zero: MAPE=nan, MAE=1.5; parziale: MAPE=10.0; MM serie 1 punto=[10. 10.]; LIN 2 punti=[30. 40.] | 0.01 |
| TC-26 | Holdout cronologico test_n = min(4, max(2, n//5)) | PASS | holdout = min(4, max(2, n//5)): n=24 -> 4 mesi finali; RMSE MM del riferimento a 4 mesi coincide con la dashboard (e differisce da quello a 2 mesi) | test_n(24)=4; RMSE dashboard=111.5; RMSE rif. 4 mesi=111.50; RMSE rif. 2 mesi=123.87 | 0.74 |
| TC-27 | Componenti di scorta - GUANTI (caso di riferimento) | PASS | GUANTI, lead 30, livello 0,95, variabilita 1,0, orizzonte 3, finestra 3: Ciclica 31,144.6, Sicurezza 2,363.4, Anticipata 543.5, Pipeline 62,289.3 | Ciclica 31,144.6, Sicurezza 2,363.4, Anticipata 543.5, Pipeline 62,289.3 | 0.72 |
| TC-28 | Componenti di scorta - tutte le categorie e piu' enti | PASS | 6 categorie x 3 selezioni ente (tutti, ATS Demo Nord, AREU) con lead 60, livello 0,99, variabilita 1,5: 4 componenti = formule di riferimento | casi=18; errori=0 | 14.55 |
| TC-29 | Monotonia rispetto al lead time | PASS | lead time 7..119 (passo 7) e 120: Sicurezza e Pipeline strettamente crescenti; Ciclica costante; Anticipata non decrescente | lead(7,120): sicurezza 1141.6->4707.1; pipeline 14534.2->247080.8; ciclica {31144.6}; anticipata 126.8->2155.8; errori=0 | 13.75 |
| TC-30 | Monotonia rispetto al livello di servizio | PASS | Sicurezza strettamente crescente con il livello di servizio (rapporto 0,99/0,90 = 2,326/1,282 = 1,814); altre componenti invariate | sicurezza={0.9: 1841.9, 0.95: 2363.4, 0.975: 2816.0, 0.99: 3341.8}; rapporto=1.814; altre invariate=True | 3.20 |
| TC-31 | Effetto della variabilita sulle scorte | PASS | variabilita 0,5/1,0/2,0: Sicurezza proporzionale (2,0 = 4 x 0,5); altre componenti invariate | sicurezza=[1181.7, 2363.4, 4726.8]; proporzionale=True; altre invariate=True | 2.26 |
| TC-32 | Formule di scorta ciclica e pipeline su tutte le categorie | PASS | per ogni categoria (lead 45): Pipeline = domanda media giornaliera (ultimi 6 mesi/30,4375) x 45; Ciclica = domanda giornaliera x 15; nessuna componente negativa | errori=0 | 5.17 |
| TC-33 | Robustezza: combinazioni estreme di tutti gli slider | PASS | 32 combinazioni degli estremi di tutti gli slider (con livello di servizio e categoria ruotati): nessuna eccezione, componenti finite e >= 0 | combinazioni=32; errori=0; durata 26 s | 25.90 |
| TC-34 | CSV mancante, colonna mancante, CSV vuoto | PASS | file monitoraggio mancante, colonna giacenza_pezzi mancante, solo intestazione: st.error guidato in italiano, nessuna eccezione, nessuna scheda | file mancante: File mancante: data/monitoraggio_panflu_demo.csv. Verificare che sia nella cartella data/ ; colonna mancante: Colonne mancanti in data/monitoraggio_panflu_demo.csv: giacenza_pezzi (colonne attese: id_; CSV vuoto: Il file data/monitoraggio_panflu_demo.csv non contiene righe di dati (solo intestazione). | 0.75 |
| TC-35 | Coerenza dei file dati distribuiti con l'app | PASS | tracciabilita' dati: l'app usa domanda_storica.csv e parametri_scorte.csv presenti in data/ e il README li documenta | app.py cita domanda_storica=True; parametri_scorte=True; README li documenta=True | 0.00 |
| TC-36 | Almeno 4 serie con andamenti diversi e almeno 2 metodi | PASS | >= 4 serie storiche di consumo (6 categorie) con andamenti differenti; >= 2 metodi previsionali confrontati con indicatori d'errore | categorie=6; metodi=['Media mobile semplice', 'Regressione lineare']; pendenza mensile per categoria={'CALZARI': 7.5, 'CAMICI CHIRURGICI': 13.8, 'COPRICAPO': 2.1, 'DISINFETTANTI': -0.8, 'GUANTI': -162.8, 'MASCHERINE CHIRURGICHE': -204.6} | 0.93 |
| TC-37 | Controlli di scenario richiesti dalla traccia | PASS | traccia: la dashboard consente di modificare variabilita, trend, stagionalita e lead time (esempi indicati dalla traccia) | controlli presenti: {'variabilita': True, 'trend': True, 'lead time': True, 'stagionalita': True}; etichette=['Orizzonte previsivo (mesi)', 'Finestra media mobile (mesi)', 'Moltiplicatore variabilità', 'Variazione simulata della domanda (%)', 'Lead time ipotizzato (giorni)', 'Intensità stagionalità (0 = neutra)', 'Livello di servizio obiettivo'] | 0.79 |
| TC-38 | Effetto del trend sulle componenti di scorta | PASS | traccia: gli effetti delle caratteristiche della domanda (trend) sono mostrati anche sulle diverse tipologie di scorte: con +30% almeno una componente dovrebbe cambiare | trend 0%: {'Ciclica': 31144.6, 'Sicurezza': 2363.4, 'Anticipata': 543.5, 'Pipeline': 62289.3}; trend +30%: {'Ciclica': 39446.3, 'Sicurezza': 2193.3, 'Anticipata': 898.1, 'Pipeline': 78892.6}; identiche=False | 1.50 |
| TC-39 | Tempo di esecuzione dello script | PASS | esecuzione completa dello script con parametri default in <= 10 s (AppTest, esclusa l'apertura del browser) | tempi (s): 0.46, 0.67, 0.48; massimo 0.67 | 1.61 |
| TC-40 | Avvio del server Streamlit (porta 8503) | PASS | avvio con 'streamlit run' su porta 8503: endpoint /_stcore/health = 'ok' e pagina principale HTTP 200 entro 40 s; server poi arrestato | health='ok'; http=200; tempo di avvio=1.6 s | 1.74 |
| TC-41 | Ripetibilita (determinismo) | PASS | due esecuzioni identiche producono indicatori, metriche e componenti identici (determinismo) | identici=True | 1.57 |
| TC-42 | Indici stagionali | PASS | indici stagionali di 6 categorie e 4 articoli: 12 valori, media 1, = riferimento indipendente; tabella dell'app = riferimento; intensita' 0 -> fattore 1,0 e risultati = default (TC-18/27) | errori=0; indici GUANTI=[0.974, 1.074, 1.124, 1.14, 1.132, 1.014, 0.989, 0.936, 0.912, 0.872, 0.925, 0.907] | 6.60 |
| TC-43 | Stagionalita' sulle previsioni | PASS | stagionalita' 0,5 e 1,0 su 6 categorie (+2 scenari misti): metriche, metodo e previsioni = riferimento indipendente; con intensita' 1 le previsioni GUANTI differiscono dal default | scenari=14; errori=0; GUANTI default [60554, 61501, 61260] vs s=1 [59005, 66060, 68853] | 12.74 |
| TC-44 | Stagionalita' sulle componenti di scorta | PASS | componenti di scorta con stagionalita' 0,5 e 1,0 su 6 categorie = riferimento; Ciclica e Pipeline lineari in s; con s=1 almeno una componente cambia | errori=0; GUANTI s=0 {'Ciclica': 31144.6, 'Sicurezza': 2363.4, 'Anticipata': 543.5, 'Pipeline': 62289.3} -> s=1 {'Ciclica': 28815.4, 'Sicurezza': 4353.6, 'Anticipata': 9877.8, 'Pipeline': 57630.9}; categorie con componenti modificate={'CALZARI': True, 'CAMICI CHIRURGICI': True, 'COPRICAPO': True, 'DISINFETTANTI': True, 'GUANTI': True, 'MASCHERINE CHIRURGICHE': True} | 16.44 |
| TC-45 | Variazione simulata sulle componenti di scorta | PASS | trend -30/0/+30: componenti = riferimento; Ciclica e Pipeline crescenti con il trend; la variabilita' modifica solo la Sicurezza (proporzionale) anche con trend e stagionalita' attivi | errori=0; GUANTI -30%: {'Ciclica': 22843.0, 'Sicurezza': 2661.2, 'Anticipata': 188.8, 'Pipeline': 45686.0}; 0%: {'Ciclica': 31144.6, 'Sicurezza': 2363.4, 'Anticipata': 543.5, 'Pipeline': 62289.3}; +30%: {'Ciclica': 39446.3, 'Sicurezza': 2193.3, 'Anticipata': 898.1, 'Pipeline': 78892.6}; altre invariate=True | 14.90 |
| TC-46 | Scheda Articoli e parametri | PASS | scheda articoli: parametri, confronto metodi (MAE/RMSE/MAPE, selezionato), componenti (lead e livello da parametri_scorte.csv, copertura) e previsioni di dettaglio = ricalcolo pandas indipendente da domanda_storica.csv e parametri_scorte.csv, in default e in scenario (trend 20, s 0,5, var 1,5, orizzonte 4, finestra 4); slider lead time ininfluente | errori=0; Guanti nitrile M default: RMSE MM 267.17 / LIN 170.89, metodo Regressione lineare, componenti {'Ciclica': np.float64(713.3), 'Sicurezza': np.float64(69.0), 'Anticipata': np.float64(30.4), 'Pipeline': np.float64(2139.8), 'Copertura': np.float64(65.2)}; dettagli scenario={'Guanti nitrile M': [1796, 1806, 1807, 1761], 'Kit medicazione': [306, 377, 358, 403], 'Mascherine chirurgiche': [960, 976, 977, 1043], 'Siringhe sterili 5 ml': [970, 920, 961, 976]} | 6.89 |
| TC-47 | mesi_stagionali come moltiplicatore per articolo | PASS | mesi_stagionali come moltiplicatore dell'intensita': slider 1,0 con Guanti 0,5, Kit medicazione 0, altri 1,0 -> Guanti = intensita' 0,5, Kit = intensita' 0, altri = intensita' 1,0 (app con CSV originali) | errori=0 | 3.26 |
| TC-48 | Validazione CSV: file, colonne, vuoti | PASS | per ciascuno dei 3 CSV: file mancante, colonna mancante, solo intestazione, file a 0 byte -> un solo st.error in italiano con nome file/colonna, nessuna eccezione, nessuna scheda | casi=12; errori=0 | 2.97 |
| TC-49 | Validazione CSV: valori non validi | PASS | valori non validi (numero negativo, testo in colonna numerica, mese 2024-13/abc, duplicati, id vuoto, data non valida, serie < 12 mesi, buco nella serie, articoli incoerenti, livello servizio 0/1, lead time 0, scorta negativa): messaggio italiano specifico + stop | casi=17; errori=0 | 4.38 |
| TC-50 | Funzioni nuove (unitari) | PASS | funzioni nuove: seasonal_indices recupera il profilo 1,2/0,8 (media 1; <12 punti -> 1), seasonal_factor neutro a 0 e clippato, trend_series (rampa, clamp), z_score (tabella + NormalDist), stock_components = formula originale a s=0/trend=0, serie vuota -> zeri | errori=0; indici recuperati=[1.165, 1.173, 1.18, 1.187, 1.195, 1.201, 0.806, 0.81, 0.814, 0.819, 0.823, 0.827] | 0.01 |
| TC-51 | Robustezza dei nuovi controlli | PASS | 32 combinazioni estreme con i nuovi controlli (stagionalita' 0/1, variazione +-30, variabilita 0,5/2, lead 7/120, orizzonte/finestra 1-2/6-6, categorie, enti e livelli ruotati): nessuna eccezione, componenti e vista articoli finite e >= 0, previsioni >= 0 | combinazioni=32; errori=0; durata 26 s | 26.41 |
| TC-52 | Valori di default invariati | PASS | valori di default invariati nella v1.1: {'righe': 864, 'sotto_soglia': 525, 'perc': 60.8, 'scadute_tot': 47036, 'dic_sotto': 24, 'dic_righe': 36, 'scadute_dic': 1863, 'g_rmse_ma': 5978, 'g_rmse_lin': 10339, 'g_mape_ma': 9.2, 'g_mape_lin': 16.7, 'd_rmse_ma': 447, 'd_rmse_lin': 647, 'comp': {'Ciclica': 31145, 'Sicurezza': 2363, 'Anticipata': 543, 'Pipeline': 62289}, 'titolo': 'Monitoraggio delle scorte pandemiche', 'slider_stagionalita': ('Intensità stagionalità (0 = neutra)', 0.0)} | {'righe': 864, 'sotto_soglia': 525, 'perc': 60.8, 'scadute_tot': 47036, 'dic_sotto': 24, 'dic_righe': 36, 'scadute_dic': 1863, 'g_rmse_ma': 5978, 'g_rmse_lin': 10339, 'g_mape_ma': 9.2, 'g_mape_lin': 16.7, 'd_rmse_ma': 447, 'd_rmse_lin': 647, 'comp': {'Ciclica': 31145, 'Sicurezza': 2363, 'Anticipata': 543, 'Pipeline': 62289}, 'titolo': 'Monitoraggio delle scorte pandemiche', 'slider_stagionalita': ('Intensità stagionalità (0 = neutra)', 0.0)} | 2.29 |
| TC-53 | Compatibilita' e documentazione | PASS | A-05 e documentazione: nessun use_container_width in app.py; requirements.txt con 4 versioni esatte (==) uguali a quelle installate; README con sottocartella di avvio, 3 CSV, versioni testate (3.14); NOTE.txt aggiornata | use_container_width presente=False; requirements={'streamlit': '1.67.0', 'pandas': '3.1.1', 'numpy': '2.5.5', 'plotly': '7.1.0'}; installate={'streamlit': '1.67.0', 'pandas': '3.1.1', 'numpy': '2.5.5', 'plotly': '7.1.0'}; README ok=True | 0.01 |

| ID | Titolo | Esito |
|---|---|---|
| TM-01 | Titolo e intestazione | NON ESEGUITO - da eseguire manualmente |
| TM-02 | Layout generale e barra laterale | NON ESEGUITO - da eseguire manualmente |
| TM-03 | Leggibilita' dei grafici del tab Monitoraggio | NON ESEGUITO - da eseguire manualmente |
| TM-04 | Leggibilita' dei grafici temporali e della previsione | NON ESEGUITO - da eseguire manualmente |
| TM-05 | Formato dei numeri e delle tabelle | NON ESEGUITO - da eseguire manualmente |
| TM-06 | Download del CSV dal browser | NON ESEGUITO - da eseguire manualmente |
| TM-07 | Tab Componenti di scorta e messaggi informativi | NON ESEGUITO - da eseguire manualmente |
| TM-08 | Usabilita' e comprensibilita' generale | NON ESEGUITO - da eseguire manualmente |

Checklist dei casi manuali: vuota, da compilare nel Test Book (sezione 6).

## 4. Anomalie e osservazioni

| ID | Gravita' | Test | Descrizione | Evidenza (atteso vs ottenuto) | Suggerimento |
|---|---|---|---|---|---|
| A-01 | Chiusa | TC-37 | v1.0: stagionalita' non modificabile (TC-37 FAIL). | v1.1: slider 'Intensita' stagionalita' (0 = neutra); TC-37 PASS con asserzione invariata. | Nessuno. |
| A-02 | Chiusa | TC-38 | v1.0: la variazione simulata non modificava le componenti di scorta (TC-38 FAIL). | v1.1: trend +30% -> Ciclica 39.446,3; Pipeline 78.892,6; TC-38 PASS con asserzione invariata. | Nessuno. |
| A-03 | Chiusa | TC-35 | v1.0: domanda_storica.csv e parametri_scorte.csv non letti dall'app (TC-35 FAIL). | v1.1: letti dalla scheda 'Articoli e parametri'; TC-35 e TC-46 PASS. | Nessuno. |
| A-04 | Chiusa | TC-34 | v1.0: nessuna validazione dei CSV. | v1.1: st.error guidato in italiano; TC-34 adattato ai nuovi messaggi (non piu' caratterizzazione); TC-48 e TC-49 PASS. | Nessuno. |
| A-05 | Chiusa | TC-53 | v1.0: use_container_width deprecato; versioni non fissate. | v1.1: width='stretch'; requirements con versioni esatte; TC-53 PASS. | Nessuno. |
| O-01 | Osservazione | TC-42..TC-53 | I casi TC-42..TC-53 sono stati aggiunti alla suite durante l'aggiornamento v1.1 e non facevano parte della v1.0. | 12 casi aggiunti, tutti PASS. | Nessuno. |
| O-02 | Osservazione | - | Gli screenshot del documento di consegna non sono stati rifatti e potrebbero non mostrare la scheda 'Articoli e parametri' e lo slider di stagionalita'. | Nessuno screenshot prodotto da questa suite. | Rifare gli screenshot a cura dell'autore. |

Nessun test automatico fallito in questa esecuzione.

## 5. Copertura dei requisiti

| Rif. | Requisito / funzione | Casi ed esito |
|---|---|---|
| R1 | Serie storiche di almeno quattro articoli con andamenti differenti | TC-01:PASS, TC-02:PASS, TC-05:PASS, TC-36:PASS |
| R2 | Almeno due metodi previsionali applicati | TC-18:PASS, TC-24:PASS, TC-36:PASS |
| R3 | Valutazione accuratezza con indicatori d'errore (MAE, RMSE, MAPE) | TC-18:PASS, TC-24:PASS, TC-25:PASS, TC-26:PASS |
| R4 | Individuazione del metodo piu' adatto | TC-19:PASS |
| R5 | Stima delle scorte cicliche, di sicurezza, anticipate, pipeline | TC-27:PASS, TC-28:PASS, TC-32:PASS |
| R6 | Dashboard: modifica di variabilita, trend, stagionalita, lead time | TC-22:PASS, TC-23:PASS, TC-37:PASS, TC-42:PASS, TC-43:PASS, TC-47:PASS |
| R7 | Effetti degli scenari sulle diverse tipologie di scorte | TC-29:PASS, TC-30:PASS, TC-31:PASS, TC-38:PASS, TC-44:PASS, TC-45:PASS |
| R8 | Mostrare andamento storico e previsto della domanda | TC-17:PASS, TC-20:PASS, TC-21:PASS, TM-04:NON ESEGUITO |
| R9 | Mostrare confronto di accuratezza dei metodi | TC-18:PASS, TC-19:PASS |
| R10 | Mostrare composizione delle scorte nei diversi scenari | TC-27:PASS, TC-33:PASS, TM-07:NON ESEGUITO |
| R11 | Codice, dati e file necessari all'esecuzione | TC-05:PASS, TC-35:PASS, TC-40:PASS, TC-46:PASS, TC-53:PASS |
| F1 | Monitoraggio: esito giacenza vs quantita' minima | TC-04:PASS, TC-07:PASS, TC-08:PASS |
| F2 | Filtri (mese, ente, categoria, esito), anche combinati e vuoti | TC-09:PASS, TC-10:PASS, TC-11:PASS, TC-12:PASS, TC-13:PASS, TC-14:PASS, TC-15:PASS |
| F3 | Esportazione CSV dei dati filtrati | TC-16:PASS, TM-06:NON ESEGUITO |
| N1 | Avvio, prestazioni, stabilita', robustezza | TC-06:PASS, TC-33:PASS, TC-34:PASS, TC-39:PASS, TC-40:PASS, TC-41:PASS, TC-48:PASS, TC-49:PASS, TC-51:PASS, TC-52:PASS |
| N2 | Aspetti visivi e usabilita' | TM-01:NON ESEGUITO, TM-02:NON ESEGUITO, TM-03:NON ESEGUITO, TM-05:NON ESEGUITO, TM-08:NON ESEGUITO |

## 6. Valori numerici di riferimento verificati

- TC-04: 525 su 864 = 60.8%; scadute totali 47036; righe uguali 1
- TC-07: {'Giacenze rilevate': 155978, 'Quantità minima richiesta': 227480, 'Righe sotto soglia': 24, 'Scorte scadute rilevate': 1863}; righe tabella=36; esiti={'Sotto soglia': 24, 'Conforme': 12}
- TC-18/TC-23: GUANTI, RMSE media mobile 5.978,0 contro regressione lineare 10.339,25 (metodo scelto: media mobile semplice); previsioni a 3 mesi [60554, 61501, 61260]
- TC-27: Ciclica 31,144.6, Sicurezza 2,363.4, Anticipata 543.5, Pipeline 62,289.3
- TC-29: lead(7,120): sicurezza 1141.6->4707.1; pipeline 14534.2->247080.8; ciclica {31144.6}; anticipata 126.8->2155.8; errori=0
- TC-30: sicurezza={0.9: 1841.9, 0.95: 2363.4, 0.975: 2816.0, 0.99: 3341.8}; rapporto=1.814; altre invariate=True

## 7. Limiti della verifica

- Il rendering visivo nel browser, il layout, la leggibilita' dei grafici e il formato dei numeri a video non sono verificati (casi TM-01..TM-08 non eseguiti). Non sono stati prodotti screenshot.
- I grafici Plotly sono verificati solo come presenti e senza eccezioni (conteggio), non nei contenuti visivi.
- Non verificati: accessibilita', compatibilita' tra browser e sistemi operativi, prestazioni con dati di grandi dimensioni, uso concorrente.
- I dati sono sintetici: nessuna verifica di aderenza a dati reali di enti sanitari.
- Il contenuto del download e' verificato intercettando i dati passati a st.download_button, non scaricando il file dal browser.
- Il tempo di esecuzione (TC-39) misura solo lo script in AppTest, non l'apertura della pagina nel browser; TC-40 misura l'avvio del server.
- I valori attesi sono calcolati dallo stesso team con formule ricalcolate in modo indipendente dal codice, ma sulla base della stessa descrizione funzionale: non e' una validazione metodologica dei criteri di scorta (scelte didattiche).

## 8. Conclusioni

La dashboard supera 53 test automatici su 53 in una sola esecuzione. Le nuove funzioni (stagionalita', scenario, vista a quattro articoli, validazione dei CSV) sono coperte solo dai test elencati. I valori di default della v1.0 risultano invariati (TC-52). I controlli manuali TM-01..TM-08 non sono stati eseguiti, non sono stati prodotti screenshot e i dati sono sintetici: la verifica visiva resta da fare.

## 9. Riproducibilita'

Dalla cartella PW24, con l'ambiente virtuale del progetto:

```
.venv\Scripts\python.exe -m pytest test/test_dashboard.py -v --junitxml=test/results/junit.xml
.venv\Scripts\python.exe test/genera_documenti.py   (rigenera .md e .docx dai risultati; richiede junit.xml e details.json in test/results)
```

File prodotti: test/test_dashboard.py, test/results/junit.xml, test/results/details.json.
