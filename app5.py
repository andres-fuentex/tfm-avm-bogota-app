import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import plotly.express as px
from shapely.geometry import Point, shape

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
    coords = feature.get("geometry", {}).get("coordinates", [])
    if not coords:
        return [4.624335, -74.063644]
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

# Centro de Bogotá (para paso 2)
bogota_center = [4.624335, -74.063644]

# --- Bloque 1: Bienvenida ---
if st.session_state.step == 1:
    st.title("🎉 ¡Bienvenido a la Herramienta AVM Bogotá! 🎉")
    st.markdown("Estimamos el valor de tu vivienda usada en Bogotá con datos abiertos. Pulsa **Iniciar** para comenzar.")
    if st.button("Iniciar"):
        st.session_state.step = 2
    st.stop()

# --- Bloque 2: Selección de localidad por clic con hover ---
if st.session_state.step == 2:
    st.header("🌆 Paso 1: Haz clic en tu localidad de interés")
    mapa2 = folium.Map(location=bogota_center, zoom_start=11)
    folium.GeoJson(
        localidades_geo,
        style_function=lambda feature: {"fillColor": "#3388ff", "color": "black", "fillOpacity": 0.1, "weight": 1},
        highlight_function=lambda feature: {"fillColor": "red", "color": "red", "fillOpacity": 0.5, "weight": 2},
        tooltip=folium.GeoJsonTooltip(fields=["nombre_localidad"], labels=False)
    ).add_to(mapa2)

    result = st_folium(mapa2, width=700, height=500, returned_objects=["last_clicked"])
    clicked = result.get("last_clicked") if result else None

    if clicked and "lat" in clicked and "lng" in clicked:
        pt = Point(clicked["lng"], clicked["lat"])
        for feat in localidades_geo.get("features", []):
            if feat.get("geometry") and shape(feat["geometry"]).contains(pt):
                loc = feat["properties"].get("nombre_localidad")
                st.success(f"Localidad seleccionada: **{loc}**")
                st.session_state.localidad_sel = loc
                st.session_state.step = 3
                break
    else:
        st.info("👉 Haz clic dentro del polígono de la localidad.")
    st.stop()

# --- Bloque 3: Selección de uso POT por clic con borde de localidad ---
if st.session_state.step == 3:
    sel_loc = st.session_state.localidad_sel
    feat_loc = next(f for f in localidades_geo["features"] if f["properties"]["nombre_localidad"] == sel_loc)
    centro_loc = get_centroid(feat_loc)

    st.header(f"📍 Paso 2: Haz clic en el POT de {sel_loc} que te interesa")
    mapa3 = folium.Map(location=centro_loc, zoom_start=13)
    # borde rojo de la localidad
    folium.GeoJson(
        feat_loc,
        style_function=lambda f: {"color": "red", "weight": 3, "fillOpacity": 0}
    ).add_to(mapa3)

    cod_loc = feat_loc["properties"]["num_localidad"]
    pot_local = [f for f in pot_geo["features"] if f["properties"]["num_localidad"] == cod_loc]

    # paleta de colores
    cats = []
    for f in pot_local:
        u = f["properties"]["uso_pot_simplificado"]
        if u not in cats: cats.append(u)
    palette = px.colors.qualitative.Plotly
    color_map = {c: palette[i % len(palette)] for i,c in enumerate(cats)}

    for f in pot_local:
        u = f["properties"]["uso_pot_simplificado"]
        col = color_map[u]
        folium.GeoJson(
            f,
            style_function=lambda feature, color=col: {"color": color, "fillColor": color, "fillOpacity": 0.4, "weight": 1},
            highlight_function=lambda feature: {"weight": 3, "color": "yellow"},
            tooltip=folium.GeoJsonTooltip(fields=["uso_pot_simplificado"], labels=False)
        ).add_to(mapa3)

    result = st_folium(mapa3, width=700, height=500, returned_objects=["last_clicked"])
    clicked = result.get("last_clicked") if result else None

    if clicked and "lat" in clicked and "lng" in clicked:
        pt = Point(clicked["lng"], clicked["lat"])
        for f in pot_local:
            if shape(f["geometry"]).contains(pt):
                uso = f["properties"]["uso_pot_simplificado"]
                st.success(f"Uso POT seleccionado: **{uso}**")
                st.session_state.uso_sel = uso
                st.session_state.step = 4
                break
    else:
        st.info("👉 Haz clic dentro del polígono del POT que te interesa.")
    st.stop()

# --- Bloque 4: Manzanas filtradas y selección por clic ---
if st.session_state.step == 4:
    sel_loc = st.session_state.localidad_sel
    sel_uso = st.session_state.uso_sel

    # Recalcular feature y centro
    feat_loc = next(f for f in localidades_geo["features"] if f["properties"]["nombre_localidad"] == sel_loc)
    centro_loc = get_centroid(feat_loc)

    st.header(f"🌐 Paso 3: Haz clic en la manzana de {sel_loc} ({sel_uso})")

    # Filtrar pot_local y construir area_to_uso como antes
    cod_loc = feat_loc["properties"]["num_localidad"]
    pot_local = [f for f in pot_geo["features"] if f["properties"]["num_localidad"] == cod_loc]
    area_to_uso = {f["properties"]["id_area"]: f["properties"]["uso_pot_simplificado"] for f in pot_local}

    # Reconstruir paleta y color_map para usar en el bloque 4
    cats = []
    for f in pot_local:
        u = f["properties"]["uso_pot_simplificado"]
        if u not in cats:
            cats.append(u)
    palette = px.colors.qualitative.Plotly
    color_map = {c: palette[i % len(palette)] for i, c in enumerate(cats)}
    sel_color = color_map.get(sel_uso, "#3388ff")

    # Filtrar manzanas por localidad y uso POT
    manzanas_local = []
    for f in manzanas_geo["features"]:
        p = f.get("properties", {})
        if p.get("num_localidad") != cod_loc:
            continue
        if area_to_uso.get(p.get("id_area")) == sel_uso:
            manzanas_local.append(f)
    if not manzanas_local:
        st.error("No se encontraron manzanas para esa localidad y uso POT.")
        st.stop()

    # Mostrar mapa de manzanas
    mapa_mz = folium.Map(location=centro_loc, zoom_start=14)
    for f in manzanas_local:
        folium.GeoJson(
            f,
            style_function=lambda feature, color=sel_color: {
                "color": color,
                "fillColor": color,
                "fillOpacity": 0.4,
                "weight": 1
            },
            highlight_function=lambda feature: {"weight": 3, "color": "yellow"},
            tooltip=folium.GeoJsonTooltip(fields=["id_manzana_unif"], labels=False)
        ).add_to(mapa_mz)

    result = st_folium(mapa_mz, width=700, height=500, returned_objects=["last_clicked"])
    clicked = result.get("last_clicked") if result else None

    if clicked and "lat" in clicked and "lng" in clicked:
        pt = Point(clicked["lng"], clicked["lat"])
        for f in manzanas_local:
            if shape(f.get("geometry", {})).contains(pt):
                mz = f["properties"].get("id_manzana_unif")
                st.success(f"Manzana seleccionada: **{mz}**")
                st.session_state.manzana_sel = mz
                st.session_state.step = 5
                break
    else:
        st.info("👉 Haz clic en la manzana que te interesa.")
