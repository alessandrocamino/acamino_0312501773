# PW24 – Mini-dashboard per il monitoraggio delle scorte pandemiche
Prototipo didattico ispirato ai requisiti della presentazione **“PanFlu – portale S.A.S.H.A. – Funzionalità di Inventario delle Scorte” (10 aprile 2025)**.
## Funzionalità
- Filtri per mese di riferimento, ente, categoria e stato della verifica.
- Tabella con consumo mensile, quantità minima richiesta, giacenza e scorte scadute.
- Esito “Conforme” / “Sotto soglia” e download CSV dei dati filtrati.
- Grafici temporali di consumi, giacenze, scorte scadute e quantità minime.
- Previsioni dimostrative con media mobile semplice e regressione lineare, metriche MAE/RMSE/MAPE.
- Stima didattica delle componenti di scorta ciclica, sicurezza, anticipata e pipeline.
- Scheda «Articoli e parametri»: previsioni e componenti di scorta per 4 articoli di magazzino, calcolate dai file `domanda_storica.csv` e `parametri_scorte.csv`.
## Controlli dello scenario (barra laterale)
- **Orizzonte previsivo** e **finestra della media mobile**.
- **Moltiplicatore di variabilità**: amplifica le oscillazioni della serie nell'esperimento di previsione e la scorta di sicurezza.
- **Variazione simulata della domanda (%)**: rampa lineare sulla serie (primo mese invariato, ultimo mese con la variazione piena). Agisce sulle previsioni **e** sulle componenti di scorta.
- **Lead time ipotizzato** e **livello di servizio**: valgono per le 6 categorie; per gli articoli si usano i valori di `parametri_scorte.csv`.
- **Intensità stagionalità (0 = neutra)**: gli indici stagionali mensili sono stimati dallo storico (rapporto tra consumo e trend lineare, media per mese di calendario, normalizzata a media 1). Il fattore applicato al mese è `1 + intensità × (indice − 1)`: con intensità 0 vale esattamente 1 e i risultati restano invariati. La serie osservata contiene già la propria stagionalità, quindi lo slider rappresenta uno scenario di stagionalità accentuata. Gli indici sono visibili nell'expander «Indici stagionali stimati».
- Variazione e stagionalità definiscono la **domanda di scenario**, usata allo stesso modo da previsioni e componenti di scorta. Le previsioni applicano il fattore stagionale del mese previsto al risultato del metodo scelto.
- **Articoli**: la colonna `mesi_stagionali` di `parametri_scorte.csv` è interpretata come moltiplicatore dell'intensità di stagionalità dell'articolo (intensità effettiva = slider × valore, limitata a 0–1). Con 1,0 si usa l'intensità dello slider.
## Dataset
- `data/monitoraggio_panflu_demo.csv`: dati interamente sintetici su sei enti dimostrativi, sei categorie e 24 mesi (gennaio 2024–dicembre 2025). Alimenta monitoraggio, grafici temporali, previsioni e componenti delle 6 categorie. Le quantità minime sono parametri simulati.
- `data/domanda_storica.csv`: domanda mensile sintetica di 4 articoli (Guanti nitrile M, Mascherine chirurgiche, Siringhe sterili 5 ml, Kit medicazione), 36 mesi (gennaio 2023–dicembre 2025). Colonne: `data`, `articolo`, `domanda`.
- `data/parametri_scorte.csv`: parametri per articolo (scorta attuale, costo unitario, lead time, livello di servizio, periodo di riordino, `mesi_stagionali`). Gli articoli devono coincidere con quelli di `domanda_storica.csv`.

I dati non provengono da Regione Lombardia, ARIA, AREU o da enti sanitari reali. Categorie incluse: disinfettanti, guanti, camici chirurgici, mascherine chirurgiche, copricapo e calzari.

All'avvio i tre file sono validati (presenza, colonne, righe di dati, tipi numerici, valori non negativi, mesi nel formato AAAA-MM, duplicati, serie continue di almeno 12 mesi per articolo). In caso di problema l'app mostra un messaggio di errore in italiano e si ferma.
## Avvio
Dalla cartella del progetto che contiene `app.py` (la sottocartella `PW24_dashboard_sanitario`):
```bash
cd acamino_0312501773/PW24_dashboard_sanitario
pip install -r requirements.txt
streamlit run app.py
```
Versioni testate: Python 3.14.2, Streamlit 1.67.0, pandas 3.1.1, numpy 2.5.5, plotly 7.1.0. Altre versioni non sono state verificate.
## Limiti importanti
Questo è un prototipo autonomo: **non** implementa il flusso SMAF/PANFLU reale, non si integra con S.A.S.H.A. o sistemi regionali, non gestisce utenti e permessi, né tracciabilità per lotto e data di scadenza. Le scorte minime ufficiali devono essere caricate da una fonte autorizzata e validata. I dati sono sintetici: gli indici stagionali stimati su serie di questo tipo sono poco informativi e il loro effetto è solo illustrativo. Le previsioni e le stime non devono essere usate per decisioni operative.
