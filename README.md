# Skitsiabi Streamlit rakendus

See projekt loob abivahendi, mis aitab koostada Maa- ja Ruumiameti WMS-kaartide põhjal A4-le sobiva skitsi ruudustikuga.

## Käivitamine

1. Ava terminal selles kaustas:
   ```bash
   cd /Users/siimvahkel/Desktop/Koodid/Sktis
   ```
2. Paigalda nõutavad paketid:
   ```bash
   pip install -r requirements.txt
   ```
3. Käivita Streamlit:
   ```bash
   streamlit run app.py
   ```

## Kuidas kasutada

- Valida seade `devices.csv` andmebaasist või sisestada ekraani mõõtmed käsitsi.
- Määrata kaardiala mõõtmed ja soovitud skitsi mõõtkava.
- Valida WMS-teenus ja kiht ning luua ruudustikuga kaardipilt.
- Laadida loodud PNG alla ning kasutada skitsina paberkandjal.

## Failid

- `app.py` – Streamliti rakendus.
- `devices.csv` – seadmete ja ekraani mõõtmete andmebaas.
- `requirements.txt` – Python sõltuvused.
- `README.md` – kasutusjuhend.

## Täiendav

Kui `devices.csv` puudub või ei lae, saab seadme mõõtmed sisestada käsitsi.
