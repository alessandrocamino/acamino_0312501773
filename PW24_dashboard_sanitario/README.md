# PW24 – Mini-dashboard per il monitoraggio delle scorte pandemiche

Prototipo didattico ispirato ai requisiti della presentazione **“PanFlu – portale S.A.S.H.A. – Funzionalità di Inventario delle Scorte” (10 aprile 2025)**.

## Funzionalità
- Filtri per mese di riferimento, ente, categoria e stato della verifica.
- Tabella con consumo mensile, quantità minima richiesta, giacenza e scorte scadute.
- Esito “Conforme” / “Sotto soglia” e download CSV dei dati filtrati.
- Grafici temporali di consumi, giacenze, scorte scadute e quantità minime.
- Previsioni dimostrative con media mobile semplice e regressione lineare, metriche MAE/RMSE/MAPE.
- Stima didattica delle componenti di scorta ciclica, sicurezza, anticipata e pipeline.

## Dataset
`data/monitoraggio_panflu_demo.csv` contiene dati interamente sintetici su sei enti dimostrativi, sei categorie e 24 mesi (gennaio 2024–dicembre 2025). I dati non provengono da Regione Lombardia, ARIA, AREU o da enti sanitari reali. Le quantità minime sono parametri simulati.

Categorie incluse: disinfettanti, guanti, camici chirurgici, mascherine chirurgiche, copricapo e calzari.

## Avvio
Richiede Python 3.10 o superiore.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Limiti importanti
Questo è un prototipo autonomo: **non** implementa il flusso SMAF/PANFLU reale, non si integra con S.A.S.H.A. o sistemi regionali, non gestisce utenti e permessi, né tracciabilità per lotto e data di scadenza. Le scorte minime ufficiali devono essere caricate da una fonte autorizzata e validata. Le previsioni e le stime non devono essere usate per decisioni operative.

## Prima della consegna
- Eseguire l’app e verificare filtri, grafici, download e previsioni.
- Inserire nella relazione schermate realmente acquisite e risultati osservati.
- Verificare le istruzioni e la conformità alla traccia ufficiale Pegaso.
- Creare eventualmente una repository remota e inserire solo il link reale.
