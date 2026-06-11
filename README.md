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

- Sisesta ala kaks diagonaalnurka: kas L-EST97 X/Y või WGS84 lat/lon.
- Vali, milliseid elemente soovid skitsil näha: WMS kaart, ruudustik, põhjasuund ja mõõtkava.
- Valida seade `devices.csv` andmebaasist või sisestada ekraani mõõtmed käsitsi.
- Määrata soovitud skitsi mõõtkava ja ruudustiku samm.
- Laadida loodud PNG alla ning kasutada skitsina paberkandjal.

## Failid

- `app.py` – Streamliti rakendus.
- `devices.csv` – seadmete ja ekraani mõõtmete andmebaas.
- `requirements.txt` – Python sõltuvused.
- `README.md` – kasutusjuhend.

## Täiendav

Kui `devices.csv` puudub või ei lae, saab seadme mõõtmed sisestada käsitsi.
