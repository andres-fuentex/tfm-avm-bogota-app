import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import plotly.express as px

# --- Estado inicial ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "localidad_sel" not in st.session_state:
    st.session_state.localidad_sel = None
if "uso_sel" not in st.session_state:
    st.session_state.uso_sel = None
if "manzana_sel" not in st.session_state:
    st.session_state.manzana_sel = None

# --- Función auxiliar: calcular centroide de GeoJSON ---
def get_centroid(feature):
    coords = feature["geometry"]["coordinates"]
    if feature["geometry"]["type"] == "MultiPolygon":
        pts = [pt for poly in coords for pt in poly[0]]
    else:
        pts = coords[0]
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [sum(lats)/len(lats), sum(lons)/len(lons)]

# --- Carga de GeoJSON remotos ---
@st.cache_data
def fetch_localidades():
    url = "https://raw.githubusercontent.com/andres-fuentex/tfm-avm-bogota/main/datos_visualizacion/datos_geograficos_geo/dim_localidad.geojson"
    r = requests.get(url); r.raise_for_status()
    return r.json()

@st.cache_data
def fetch_pot():
    url = "https://raw.githubusercontent.com/andres-fuentex/tfm-avm-bogota/main/datos_visualizacion/datos_geograficos_geo/dim_area.geojson"
    r = requests.get(url); r.raise_for_status()
    return r.json()

@st.cache_data
def fetch_manzanas():
    url = "https://raw.githubusercontent.com/andres-fuentex/tfm-avm-bogota/main/datos_visualizacion/datos_geograficos_geo/tabla_hechos.geojson"
    r = requests.get(url); r.raise_for_status()
    return r.json()

# Carga inicial de datos
localidades_geo = fetch_localidades()
pot_geo         = fetch_pot()
manzanas_geo    = fetch_manzanas()

# Centro de Bogotá (paso 2)
bogota_center = [4.624335, -74.063644]

# --- Bloque 1: Bienvenida ---
if st.session_state.step == 1:
    st.title("🎉 ¡Bienvenido a la Herramienta AVM Bogotá! 🎉")
    st.markdown(
        "Estimamos el valor de tu vivienda usada en Bogotá con datos abiertos.  \\n        Pulsa **Iniciar** para continuar."
    )
    if st.button("Iniciar"):
        st.session_state.step = 2
    st.stop()

# --- Bloque 2: Selección de localidad ---
if st.session_state.step == 2:
    st.header("🌆 Paso 1: Mapa de todas las localidades")
    mapa2 = folium.Map(location=bogota_center, zoom_start=11)
    folium.GeoJson(localidades_geo).add_to(mapa2)
    st_folium(mapa2, width=700, height=500)

    st.markdown("### Paso 2: Selecciona tu localidad")
    opts = sorted(f["properties"]["nombre_localidad"] for f in localidades_geo["features"])
    with st.form("form_loc"):
        sel_loc = st.selectbox("Localidad:", options=opts)
        ok      = st.form_submit_button("Confirmar localidad")
        back    = st.form_submit_button("🔙 Regresar")
    if back:
        st.session_state.step = 1
        st.stop()
    if ok:
        st.session_state.localidad_sel = sel_loc
        st.session_state.step         = 3
    st.stop()

# --- Bloque 3: POT y selección de uso ---
if st.session_state.step == 3:
    sel_loc = st.session_state.localidad_sel

    # obtener feature y centro dinámico
    feat_sel   = next(f for f in localidades_geo["features"]
                      if f["properties"]["nombre_localidad"] == sel_loc)
    centro_loc = get_centroid(feat_sel)

    st.header(f"📍 Paso 3: Mapa de {sel_loc}")
    mapa3 = folium.Map(location=centro_loc, zoom_start=13)
    for f in localidades_geo["features"]:
        name = f["properties"]["nombre_localidad"]
        style = {"fillColor": "red" if name==sel_loc else "#3388ff",
                 "color":"black","fillOpacity":0.6 if name==sel_loc else 0.1,"weight":1}
        folium.GeoJson(f, style_function=lambda _, s=style: s).add_to(mapa3)
    st_folium(mapa3, width=700, height=500)

    st.markdown(
        "**Este territorio está regido por el Plan de Ordenamiento Territorial (POT),**  \
        que define el uso del suelo y afecta el valor del m²."
    )

    # filtrar áreas POT de la localidad
    cod_loc   = feat_sel["properties"]["num_localidad"]
    pot_local = [f for f in pot_geo["features"] if f["properties"]["num_localidad"]==cod_loc]

    # colores según categoría
    cats      = []
    for f in pot_local:
        u = f["properties"]["uso_pot_simplificado"]
        if u not in cats: cats.append(u)
    palette   = px.colors.qualitative.Plotly
    color_map = {c: palette[i%len(palette)] for i,c in enumerate(cats)}

    st.header(f"🏘️ Áreas POT en {sel_loc}")
    mapa_p = folium.Map(location=centro_loc, zoom_start=13)
    for f in pot_local:
        u = f["properties"]["uso_pot_simplificado"]
        col = color_map[u]
        folium.GeoJson(
            f,
            style_function=lambda _, color=col: {"color":color,"fillColor":color,"fillOpacity":0.4,"weight":1},
            tooltip=folium.GeoJsonTooltip(fields=["uso_pot_simplificado"], labels=False)
        ).add_to(mapa_p)
    st_folium(mapa_p, width=700, height=500)

    st.subheader("4️⃣ Selecciona uso POT de tu interés")
    uso = st.selectbox("Uso POT:", options=cats)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔙 Regresar a localidad"):
            st.session_state.step = 2; st.stop()
    with c2:
        if st.button("Confirmar área POT"):
            st.session_state.uso_sel = uso
            st.session_state.step   = 4
            st.stop()

# --- Bloque 4: Manzanas filtradas y selección ---
if st.session_state.step == 4:
    sel_loc = st.session_state.localidad_sel
    sel_uso = st.session_state.uso_sel

    # recalcular centro y feat_sel
    feat_sel   = next(f for f in localidades_geo["features"]
                      if f["properties"]["nombre_localidad"]==sel_loc)
    centro_loc = get_centroid(feat_sel)

    st.header(f"🌐 Paso 4: Manzanas en {sel_loc} ({sel_uso})")
    st.markdown("Haz **click** en la manzana que quieras analizar.")

    # reconstruir area_to_uso
    pot_local   = [f for f in pot_geo["features"] if f["properties"]["num_localidad"]==feat_sel["properties"]["num_localidad"]]
    area_to_uso = {f["properties"]["id_area"]: f["properties"]["uso_pot_simplificado"] for f in pot_local}

    # reconstruir color_map y sel_color
    cats        = []
    for f in pot_local:
        u = f["properties"]["uso_pot_simplificado"]
        if u not in cats: cats.append(u)
    palette     = px.colors.qualitative.Plotly
    color_map   = {c: palette[i%len(palette)] for i,c in enumerate(cats)}
    sel_color   = color_map[sel_uso]

    # filtrar manzanas por localidad y uso
    ms = []
    for f in manzanas_geo["features"]:
        p = f["properties"]
        if p["num_localidad"]!=feat_sel["properties"]["num_localidad"]: continue
        if area_to_uso.get(p["id_area"])==sel_uso:
            ms.append(f)
    if not ms:
        st.error("No hay manzanas para ese uso POT.")
        if st.button("🔙 Regresar a área POT"):
            st.session_state.step = 3
        st.stop()

    # mapa de manzanas coloreadas con sel_color
    mapa_mz = folium.Map(location=centro_loc, zoom_start=14)
    folium.GeoJson(
        {"type":"FeatureCollection","features":ms},
        style_function=lambda _, color=sel_color: {"color":color,"fillColor":color,"fillOpacity":0.4,"weight":1},
        tooltip=folium.GeoJsonTooltip(fields=["id_manzana_unif"], labels=False),
        highlight_function=lambda f: {"weight":3,"color":"yellow"}
    ).add_to(mapa_mz)
    out       = st_folium(mapa_mz, width=700, height=500, returned_objects=["last_object_clicked"])
    click     = out.get("last_object_clicked")

    if click:
        mz = click["properties"]["id_manzana_unif"]
        st.success(f"Manzana seleccionada: **{mz}**")
        st.session_state.manzana_sel = mz
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔙 Regresar a área POT"):
                st.session_state.step = 3; st.stop()
        with c2:
            if st.button("Confirmar manzana"):
                st.session_state.step = 5; st.stop()
    else:
        st.info("👉 Haz click en una manzana para seleccionarla.")
        if st.button("🔙 Regresar a área POT"):
            st.session_state.step = 3