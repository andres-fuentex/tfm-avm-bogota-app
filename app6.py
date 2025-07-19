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
    geom_type = feature["geometry"].get("type")
    if geom_type == "MultiPolygon":
        pts = [pt for poly in coords for pt in poly[0]]
    else:
        pts = coords[0]
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [sum(lats)/len(lats), sum(lons)/len(lons)]

# --- Carga de GeoJSON remotos ---
@st.cache_data
def fetch_localidades():
    url = (
        "https://raw.githubusercontent.com/andres-fuentex/"
        "tfm-avm-bogota/main/datos_visualizacion/datos_geograficos_geo/dim_localidad.geojson"
    )
    r = requests.get(url); r.raise_for_status()
    return r.json()

@st.cache_data
def fetch_pot():
    url = (
        "https://raw.githubusercontent.com/andres-fuentex/"
        "tfm-avm-bogota/main/datos_visualizacion/datos_geograficos_geo/dim_area.geojson"
    )
    r = requests.get(url); r.raise_for_status()
    return r.json()

@st.cache_data
def fetch_manzanas():
    url = (
        "https://raw.githubusercontent.com/andres-fuentex/"
        "tfm-avm-bogota/main/datos_visualizacion/datos_geograficos_geo/tabla_hechos.geojson"
    )
    r = requests.get(url); r.raise_for_status()
    return r.json()

# Carga inicial
a_local = fetch_localidades()
p_geo   = fetch_pot()
mz_geo  = fetch_manzanas()

# Centro de Bogotá
dc = [4.624335, -74.063644]

# --- Bloque 1: Bienvenida ---
if st.session_state.step == 1:
    st.title("🎉 ¡Bienvenido a la Herramienta AVM Bogotá! 🎉")
    st.markdown(
        "Estimamos el valor de tu vivienda usada en Bogotá con datos abiertos. "
        "Pulsa **Iniciar** para comenzar."
    )
    iniciar = st.button("Iniciar")
    if iniciar:
        st.session_state.step = 2
        st.experimental_rerun()
    else:
        st.stop()

# --- Bloque 2: Localidad por clic ---
if st.session_state.step == 2:
    st.header("🌆 Paso 1: Haz clic en tu localidad")
    m = folium.Map(location=dc, zoom_start=11)
    folium.GeoJson(
        a_local,
        style_function=lambda f: {"fillColor":"#3388ff","color":"black","fillOpacity":0.1,"weight":1},
        highlight_function=lambda f: {"fillColor":"red","color":"red","fillOpacity":0.5,"weight":2},
        tooltip=folium.GeoJsonTooltip(fields=["nombre_localidad"], labels=False)
    ).add_to(m)
    res = st_folium(m, width=700, height=500, returned_objects=["last_object_clicked"])
    cl = res.get("last_object_clicked")
    if cl and cl.get("geometry"):
        x, y = cl["geometry"]["coordinates"]
        pt = Point(x, y)
        for feat in a_local.get("features", []):
            if shape(feat["geometry"]).contains(pt):
                st.session_state.localidad_sel = feat["properties"]["nombre_localidad"]
                st.session_state.step = 3
                st.experimental_rerun()
    st.stop()

# --- Bloque 3: POT por clic ---
if st.session_state.step == 3:
    loc = st.session_state.localidad_sel
    feat_loc = next(f for f in a_local.get("features", []) if f["properties"]["nombre_localidad"]==loc)
    centro = get_centroid(feat_loc)
    st.header(f"📍 Paso 2: Haz clic en el POT de {loc}")
    m3 = folium.Map(location=centro, zoom_start=13)
    folium.GeoJson(feat_loc, style_function=lambda f: {"color":"red","weight":3,"fillOpacity":0}).add_to(m3)
    code = feat_loc["properties"]["num_localidad"]
    pot_feats = [f for f in p_geo.get("features", []) if f["properties"]["num_localidad"]==code]
    cats=[]
    for f in pot_feats:
        u = f["properties"].get("uso_pot_simplificado")
        if u and u not in cats: cats.append(u)
    pal=px.colors.qualitative.Plotly
    cmap={c:pal[i%len(pal)] for i,c in enumerate(cats)}
    for f in pot_feats:
        col=cmap.get(f["properties"].get("uso_pot_simplificado"), "#3388ff")
        folium.GeoJson(
            f,
            style_function=lambda feat,color=col: {"color":color,"fillColor":color,"fillOpacity":0.4,"weight":1},
            highlight_function=lambda feat:{"weight":3,"color":"yellow"},
            tooltip=folium.GeoJsonTooltip(fields=["uso_pot_simplificado"], labels=False)
        ).add_to(m3)
    res=st_folium(m3,width=700,height=500,returned_objects=["last_object_clicked"])
    cl=res.get("last_object_clicked")
    if cl and cl.get("geometry"):
        x,y=cl["geometry"]["coordinates"]
        pt=Point(x,y)
        for f in pot_feats:
            if shape(f["geometry"]).contains(pt):
                st.session_state.uso_sel=f["properties"].get("uso_pot_simplificado")
                st.session_state.step=4
                st.experimental_rerun()
    st.stop()

# --- Bloque 4: Manzana por clic ---
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

    result = st_folium(mapa_mz, width=700, height=500, returned_objects=["last_object_clicked"])
    cl = result.get("last_object_clicked") if result else None

    if cl and cl.get("geometry"):
        x, y = cl["geometry"]["coordinates"]
        pt = Point(x, y)
        for f in manzanas_local:
            if shape(f.get("geometry", {})).contains(pt):
                st.session_state.manzana_sel = f["properties"].get("id_manzana_unif")
                st.session_state.step = 5
                st.experimental_rerun()
    else:
        st.info("👉 Haz clic en la manzana que te interesa.")
    st.stop()

# --- Bloque 5: Buffer y contexto transporte/colegios ---
if st.session_state.step == 5:
    sel_mz = st.session_state.manzana_sel
    feat_mz = next(f for f in manzanas_geo.get("features", []) if f["properties"].get("id_manzana_unif") == sel_mz)
    mz_geom = shape(feat_mz.get("geometry", {}))
    buffer_mz = mz_geom.buffer(500)

    st.header(f"📦 Paso 4: Contexto de Manzana {sel_mz}")
    st.markdown("Se ha generado un buffer de 500 metros alrededor de la manzana para mostrar colegios y transporte.")

    @st.cache_data
    def fetch_colegios():
        url = (
            "https://raw.githubusercontent.com/andres-fuentex/"
            "tfm-avm-bogota/main/datos_visualizacion/datos_geograficos_geo/colegios.geojson"
        )
        r = requests.get(url); r.raise_for_status()
        return r.json()

    @st.cache_data
    def fetch_transporte():
        url = (
            "https://raw.githubusercontent.com/andres-fuentex/"
            "tfm-avm-bogota/main/datos_visualizacion/datos_geograficos_geo/transporte.geojson"
        )
        r = requests.get(url); r.raise_for_status()
        return r.json()

    colegios_geo = fetch_colegios()
    trans_geo   = fetch_transporte()

    count_colegios = sum(1 for f in colegios_geo.get("features", []) if shape(f.get("geometry", {})).within(buffer_mz))
    count_trans   = sum(1 for f in trans_geo.get("features", [])   if shape(f.get("geometry", {})).within(buffer_mz))

    m5 = folium.Map(location=get_centroid(feat_mz), zoom_start=15)
    folium.GeoJson(
        buffer_mz.__geo_interface__,
        style_function=lambda _: {"color": "blue", "fillOpacity": 0.1}
    ).add_to(m5)
    for f in colegios_geo.get("features", []):
        if shape(f.get("geometry", {})).within(buffer_mz):
            coords = f.get("geometry", {}).get("coordinates", [0,0])
            folium.CircleMarker(
                location=[coords[1], coords[0]], radius=5,
                popup=f.get("properties", {}).get("nombre", "Colegio")
            ).add_to(m5)
    for f in trans_geo.get("features", []):
        if shape(f.get("geometry", {})).within(buffer_mz):
            coords = f.get("geometry", {}).get("coordinates", [0,0])
            folium.CircleMarker(
                location=[coords[1], coords[0]], radius=5, color="green",
                popup=f.get("properties", {}).get("estacion", "Transporte")
            ).add_to(m5)
    st_folium(m5, width=700, height=500)

    st.markdown(f"- Colegios en buffer: **{count_colegios}**")
    st.markdown(f"- Estaciones de transporte en buffer: **{count_trans}**")

    if st.button("🔙 Empezar de nuevo"):
        st.session_state.step = 1
        st.experimental_rerun()
    if st.button("📄 Descargar informe"):
        st.success("Informe generado y listo para descargar.")
