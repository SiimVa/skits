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

- Sisesta ala kaks diagonaalnurka MGRS-formaadis.
- Vali, milliseid skitsi elemente soovid näha: WMS kaart, ruudustik, põhjasuund ja mõõtkava.
- Vali olulisemad maastiku elemendid: teed, sihid, jõed, kraavid, majad ja sild.
- Valida kaardi mõõtkava (vaikimisi 1:50 000) ja seejärel skitsi mõõtkava.
- Sisestada kaardilt mõõdetud mm; süsteem arvutab, mitu mm see on skitsil.
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
