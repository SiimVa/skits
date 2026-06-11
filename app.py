import io
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlencode

import pandas as pd
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

st.set_page_config(page_title="Skitsiabi", layout="wide")

WMS_SERVICES = {
    "Aluskaartide komplekt — /wms/alus": "https://kaart.maaamet.ee/wms/alus",
    "Kaardigrupid — /wms/kaart": "https://kaart.maaamet.ee/wms/kaart",
    "Halltoonides kaart — /wms/hallkaart": "https://kaart.maaamet.ee/wms/hallkaart",
    "Fotokaart / ortofoto — /wms/fotokaart": "https://kaart.maaamet.ee/wms/fotokaart",
    "Ajaloolised kaardid — /wms/ajalooline": "https://kaart.maaamet.ee/wms/ajalooline",
}

A4_LANDSCAPE_USABLE_CM = (25.0, 17.0)
A4_PORTRAIT_USABLE_CM = (17.0, 25.0)

@dataclass
class Device:
    label: str
    width_mm: float
    height_mm: float
    width_px: int
    height_px: int


def load_devices() -> pd.DataFrame:
    try:
        return pd.read_csv("devices.csv")
    except FileNotFoundError:
        st.warning("devices.csv puudub. Sisesta seade käsitsi.")
        return pd.DataFrame(columns=["brand", "model", "width_mm", "height_mm", "width_px", "height_px", "notes"])
    except Exception as e:
        st.warning(f"Seadmefaili lugemine ebaõnnestus: {e}")
        return pd.DataFrame(columns=["brand", "model", "width_mm", "height_mm", "width_px", "height_px", "notes"])


def get_wms_layers(base_url: str) -> list[str]:
    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetCapabilities",
        "VERSION": "1.3.0",
    }
    r = requests.get(base_url, params=params, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {"wms": "http://www.opengis.net/wms"}
    names = []
    for layer in root.findall(".//wms:Layer", ns):
        name_el = layer.find("wms:Name", ns)
        title_el = layer.find("wms:Title", ns)
        if name_el is not None and name_el.text:
            title = title_el.text if title_el is not None and title_el.text else name_el.text
            names.append(f"{name_el.text} — {title}")
    if not names:  # fallback for WMS 1.1.1/no namespace responses
        for layer in root.findall(".//Layer"):
            name_el = layer.find("Name")
            title_el = layer.find("Title")
            if name_el is not None and name_el.text:
                title = title_el.text if title_el is not None and title_el.text else name_el.text
                names.append(f"{name_el.text} — {title}")
    return sorted(set(names))


def cm_on_sketch(real_m: float, scale_denominator: int) -> float:
    # 1:N => 1 cm map = N cm real = N/100 m real
    return real_m / (scale_denominator / 100.0)


def recommend_scales(width_m: float, height_m: float, usable_cm: tuple[float, float]) -> pd.DataFrame:
    scales = [1000, 2000, 5000, 7500, 10000, 15000, 20000, 25000, 50000]
    rows = []
    for s in scales:
        w_cm = cm_on_sketch(width_m, s)
        h_cm = cm_on_sketch(height_m, s)
        fits = w_cm <= usable_cm[0] and h_cm <= usable_cm[1]
        detail = "mahutab" if fits else "ei mahu"
        rows.append({
            "mõõtkava": f"1 : {s:,}".replace(",", " "),
            "laius skitsil (cm)": round(w_cm, 1),
            "kõrgus skitsil (cm)": round(h_cm, 1),
            "hinnang": detail,
        })
    return pd.DataFrame(rows)


def bbox_from_center(x: float, y: float, width_m: float, height_m: float):
    return (x - width_m/2, y - height_m/2, x + width_m/2, y + height_m/2)


def wms_getmap_url(base_url: str, layer: str, bbox, width_px: int, height_px: int):
    # EPSG:3301 uses axis x,y in most Estonian WMS services; WMS 1.1.1 avoids axis order surprises.
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "STYLES": "",
        "SRS": "EPSG:3301",
        "BBOX": ",".join(f"{v:.3f}" for v in bbox),
        "WIDTH": int(width_px),
        "HEIGHT": int(height_px),
        "FORMAT": "image/png",
        "TRANSPARENT": "TRUE",
    }
    return base_url + "?" + urlencode(params)


def fetch_map_image(url: str) -> Image.Image:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def add_grid(img: Image.Image, width_m: float, height_m: float, grid_m: float, label: str, attribution: str):
    out = img.copy()
    draw = ImageDraw.Draw(out, "RGBA")
    w, h = out.size
    # grid line step in pixels
    step_x = w * grid_m / width_m
    step_y = h * grid_m / height_m
    # choose font
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", max(12, int(min(w, h) / 45)))
        small = ImageFont.truetype("DejaVuSans.ttf", max(10, int(min(w, h) / 60)))
    except Exception:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    # grid
    x = 0.0
    idx = 0
    while x <= w + 0.5:
        alpha = 155 if idx % 5 == 0 else 85
        draw.line([(x, 0), (x, h)], fill=(0, 0, 0, alpha), width=2 if idx % 5 == 0 else 1)
        idx += 1
        x += step_x
    y = 0.0
    idy = 0
    while y <= h + 0.5:
        alpha = 155 if idy % 5 == 0 else 85
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha), width=2 if idy % 5 == 0 else 1)
        idy += 1
        y += step_y
    # border and north arrow
    draw.rectangle([(0, 0), (w-1, h-1)], outline=(0, 0, 0, 255), width=4)
    draw.rectangle([(10, 10), (min(w-10, 900), 92)], fill=(255, 255, 255, 205))
    draw.text((22, 18), label, fill=(0, 0, 0, 255), font=font)
    draw.text((22, 55), f"Ruudustik: {grid_m:g} m | {attribution}", fill=(0, 0, 0, 255), font=small)
    # north arrow
    ax = w - 55
    draw.line([(ax, 80), (ax, 25)], fill=(0, 0, 0, 255), width=5)
    draw.polygon([(ax, 12), (ax-14, 40), (ax+14, 40)], fill=(0, 0, 0, 255))
    draw.text((ax-8, 85), "N", fill=(0, 0, 0, 255), font=font)
    return out


def image_download_bytes(img: Image.Image):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


st.title("Skitsiabi: Maa- ja Ruumiameti kaardi kopeerimine A4 skitsile")
st.caption("Vali ala, skitsi mõõtkava ja seade; rakendus koostab mõõtkavalise ruudustikuga abipildi.")

with st.sidebar:
    st.header("1. Seade")
    devices = load_devices()
    mode = st.radio("Seadme valik", ["Vali andmebaasist", "Sisesta käsitsi"], horizontal=False)
    if mode == "Vali andmebaasist" and not devices.empty:
        options = [f"{r.brand} {r.model}" for _, r in devices.iterrows()]
        selected = st.selectbox("Seade", options, index=0)
        row = devices.iloc[options.index(selected)]
        width_mm, height_mm = float(row.width_mm), float(row.height_mm)
        width_px, height_px = int(row.width_px), int(row.height_px)
        st.caption(str(row.notes))
    else:
        if mode == "Vali andmebaasist":
            st.warning("Seadme andmebaas on tühi või selle laadimine ebaõnnestus. Sisesta seade käsitsi.")
        width_mm = st.number_input("Ekraani laius mm", 40.0, 400.0, 64.0, 0.1)
        height_mm = st.number_input("Ekraani kõrgus mm", 40.0, 400.0, 140.0, 0.1)
        width_px = st.number_input("Ekraani laius px", 300, 5000, 1170, 1)
        height_px = st.number_input("Ekraani kõrgus px", 300, 5000, 2532, 1)
    orientation = st.radio("Orientatsioon", ["püstine", "horisontaalne"], horizontal=True)
    if orientation == "horisontaalne":
        screen_w_mm, screen_h_mm = max(width_mm, height_mm), min(width_mm, height_mm)
        screen_w_px, screen_h_px = max(width_px, height_px), min(width_px, height_px)
    else:
        screen_w_mm, screen_h_mm = min(width_mm, height_mm), max(width_mm, height_mm)
        screen_w_px, screen_h_px = min(width_px, height_px), max(width_px, height_px)

    usable_ratio = st.slider("Kaardiala osa ekraanist", 0.50, 1.00, 0.82, 0.01,
                             help="Arvestab brauseri ribasid ja Streamliti kasutajaliidest. Täpseks tööks kontrolli joonlauaga.")

    st.header("2. Ala ja mõõtkava")
    area_w_m = st.number_input("Ala laius looduses (m)", 50, 5000, 1000, 50)
    area_h_m = st.number_input("Ala kõrgus looduses (m)", 50, 5000, 1000, 50)
    scale = st.selectbox("Skitsi mõõtkava", [1000, 2000, 5000, 7500, 10000, 15000, 20000, 25000, 50000], index=2,
                         format_func=lambda x: f"1 : {x:,}".replace(",", " "))
    grid_m = st.selectbox("Ruudustiku samm looduses", [10, 20, 25, 50, 100, 250, 500], index=3,
                          format_func=lambda x: f"{x} m")

    st.header("3. Asukoht")
    coord_mode = st.radio("Keskpunkt", ["L-EST97 X/Y", "WGS84 lat/lon"], horizontal=False)
    if coord_mode == "L-EST97 X/Y":
        center_x = st.number_input("X / ida (EPSG:3301)", value=658000.0, step=100.0)
        center_y = st.number_input("Y / põhja (EPSG:3301)", value=6470000.0, step=100.0)
    else:
        lat = st.number_input("Laiuskraad", value=58.38, step=0.001, format="%.6f")
        lon = st.number_input("Pikkuskraad", value=26.72, step=0.001, format="%.6f")
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3301", always_xy=True)
        center_x, center_y = transformer.transform(lon, lat)
        st.caption(f"Teisendatud L-EST97: X={center_x:.1f}, Y={center_y:.1f}")

st.subheader("Mõõtkava ja A4 sobivuse kontroll")
col1, col2, col3 = st.columns(3)
sketch_w_cm = cm_on_sketch(area_w_m, scale)
sketch_h_cm = cm_on_sketch(area_h_m, scale)
col1.metric("Skitsil", f"{sketch_w_cm:.1f} × {sketch_h_cm:.1f} cm")
col2.metric("A4 horisontaalne kasutatav ala", f"{A4_LANDSCAPE_USABLE_CM[0]:.0f} × {A4_LANDSCAPE_USABLE_CM[1]:.0f} cm")
fits_a4 = sketch_w_cm <= A4_LANDSCAPE_USABLE_CM[0] and sketch_h_cm <= A4_LANDSCAPE_USABLE_CM[1]
col3.metric("A4 hinnang", "MAHUB" if fits_a4 else "EI MAHU")

with st.expander("Soovitatud mõõtkavad A4-le", expanded=True):
    st.dataframe(recommend_scales(area_w_m, area_h_m, A4_LANDSCAPE_USABLE_CM), use_container_width=True, hide_index=True)

st.subheader("Kaardi- ja ruudustikupildi loomine")
map_col, settings_col = st.columns([2, 1])
with settings_col:
    service_name = st.selectbox("Maa- ja Ruumiameti WMS teenus", list(WMS_SERVICES.keys()))
    base_url = WMS_SERVICES[service_name]
    layers = []
    try:
        layers = get_wms_layers(base_url)
    except Exception as e:
        st.warning(f"Kihtide laadimine ebaõnnestus: {e}")
    if layers:
        selected_layer = st.selectbox("Kiht", layers, index=0)
        layer_name = selected_layer.split(" — ")[0]
    else:
        layer_name = st.text_input("Kiht käsitsi", value="BAASKAART")
    max_px = st.slider("Loodava pildi laius px", 600, 2200, 1200, 100)

    px_per_mm = screen_w_px / screen_w_mm
    display_w_mm = screen_w_mm * usable_ratio
    display_h_mm = screen_h_mm * usable_ratio
    st.caption(f"Valitud seadme järgi: {px_per_mm:.2f} px/mm; hinnanguline kasutatav kaardiala {display_w_mm:.0f} × {display_h_mm:.0f} mm.")

bbox = bbox_from_center(center_x, center_y, area_w_m, area_h_m)
img_w = int(max_px)
img_h = max(200, int(img_w * area_h_m / area_w_m))
label = f"Ala {area_w_m:g} × {area_h_m:g} m | skits 1 : {scale:,}".replace(",", " ")
attribution = f"Aluskaart: Maa- ja Ruumiamet, väljavõte {datetime.now().strftime('%d.%m.%Y')}"

with map_col:
    if st.button("Loo ruudustikuga kaardipilt", type="primary"):
        try:
            url = wms_getmap_url(base_url, layer_name, bbox, img_w, img_h)
            img = fetch_map_image(url)
            gridded = add_grid(img, area_w_m, area_h_m, grid_m, label, attribution)
            st.session_state["gridded"] = gridded
            st.session_state["wms_url"] = url
        except Exception as e:
            st.error(f"Kaardipildi loomine ebaõnnestus: {e}")

    if "gridded" in st.session_state:
        st.image(st.session_state["gridded"], caption=label, use_container_width=True)
        st.download_button(
            "Laadi PNG alla",
            data=image_download_bytes(st.session_state["gridded"]),
            file_name="skitsiabi_ruudustik.png",
            mime="image/png",
        )
        with st.expander("WMS päringu URL"):
            st.code(st.session_state.get("wms_url", ""), language="text")

st.subheader("Kuidas seda telefonilt paberile kanda")
st.markdown(f"""
1. Kontrolli, et valitud ala skitsil oleks mõistlikus suuruses: praegu **{sketch_w_cm:.1f} × {sketch_h_cm:.1f} cm**.
2. Kasuta ruudustikku: iga ruut tähistab looduses **{grid_m:g} m**.
3. A4 millimeetripaberil joonista sama ala valitud mõõtkavas **1 : {scale:,}**.  
   Näiteks {grid_m:g} m ruut on paberil **{cm_on_sketch(grid_m, scale):.2f} cm**.
4. Kanna objektid ruutude kaupa üle: ristmikud, tee käänakud, hooned, veekogud ja piiripunktid.
5. Lisa skitsile põhjasuund, mõõtkava, legend ja andmeallika viide: **{attribution}**.
""".replace(",", " "))

st.info("Täpse füüsilise ekraanimõõdu jaoks kontrolli rakenduse kuvatud pikkuseid joonlauaga. Seadme andmebaas annab hea algväärtuse, kuid brauseri suum, süsteemi teksti suurus ja Streamliti paigutus võivad kuvamõõtu muuta.")
