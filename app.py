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

# --- Función para cargar GeoJSON de localidades ---
@st.cache_data
def fetch_localidades():
    URL = (
        "https://raw.githubusercontent.com/andres-fuentex/"
        "tfm-avm-bogota/main/"
        "datos_visualizacion/datos_geograficos_geo/dim_localidad.geojson"
    )
    r = requests.get(URL)
    r.raise_for_status()
    return r.json()

# --- Función para cargar GeoJSON de áreas POT ---
@st.cache_data
def fetch_pot():
    URL = (
        "https://raw.githubusercontent.com/andres-fuentex/"
        "tfm-avm-bogota/main/"
        "datos_visualizacion/datos_geograficos_geo/dim_area.geojson"
    )
    r = requests.get(URL)
    r.raise_for_status()
    return r.json()

# Carga inicial de datos
localidades_geo = fetch_localidades()
pot_geo         = fetch_pot()
centro          = [4.624335, -74.063644]  # Bogotá

# --- Bloque 1: Bienvenida ---
if st.session_state.step == 1:
    st.title("🎉 ¡Bienvenido a la Herramienta AVM Bogotá! 🎉")
    st.markdown(
        "Estimamos el valor de tu vivienda usada en Bogotá con datos abiertos.\n\n"
        "Pulsa **Iniciar** para continuar."
    )
    if st.button("Iniciar"):
        st.session_state.step = 2
    st.stop()

# --- Bloque 2: Mapa completo + selección de localidad ---
if st.session_state.step == 2:
    st.header("🌆 Paso 1: Mapa de todas las localidades")
    mapa_todas = folium.Map(location=centro, zoom_start=11)
    folium.GeoJson(localidades_geo).add_to(mapa_todas)
    st_folium(mapa_todas, width=700, height=500)

    st.markdown("### Paso 2: Selecciona tu localidad de interés")
    localidades_list = sorted(
        feat["properties"]["nombre_localidad"]
        for feat in localidades_geo["features"]
    )
    with st.form("localidad_form"):
        loc     = st.selectbox("Localidad:", options=localidades_list)
        confirm = st.form_submit_button("Confirmar localidad")
        back    = st.form_submit_button("🔙 Regresar")
    if back:
        st.session_state.step = 1
        st.stop()
    if confirm:
        st.session_state.localidad_sel = loc
        st.session_state.step         = 3
    if st.session_state.step == 2:
        st.stop()

# --- Bloque 3: Mapa de localidad + POT + selector de uso POT ---
sel = st.session_state.localidad_sel
st.header(f"📍 Paso 3: Mapa de {sel}")

# 3.1 Mapa base de la localidad
mapa_sel = folium.Map(location=centro, zoom_start=12)
for feat in localidades_geo["features"]:
    nombre = feat["properties"]["nombre_localidad"]
    style  = {
        "fillColor": "red" if nombre == sel else "#3388ff",
        "color":     "black",
        "fillOpacity": 0.6 if nombre == sel else 0.1,
        "weight":      1
    }
    folium.GeoJson(feat, style_function=lambda f, s=style: s).add_to(mapa_sel)
st_folium(mapa_sel, width=700, height=500)

# 3.2 Explicación POT
st.markdown("""
**Este territorio está regido por el Plan de Ordenamiento Territorial (POT),**  
que define cómo puede usarse el suelo y afecta directamente  
el valor del metro cuadrado de tu inmueble.
""")

# 3.3 Filtrar áreas POT por código de localidad
codigo_loc = next(
    feat["properties"]["num_localidad"]
    for feat in localidades_geo["features"]
    if feat["properties"]["nombre_localidad"] == sel
)
pot_local = [
    feat for feat in pot_geo["features"]
    if feat["properties"]["num_localidad"] == codigo_loc
]

# 3.4 Mapa POT con paleta de colores
# Extraer categorías en orden
cats      = []
for feat in pot_local:
    uso = feat["properties"]["uso_pot_simplificado"]
    if uso not in cats:
        cats.append(uso)

palette   = px.colors.qualitative.Plotly
color_map = {cat: palette[i % len(palette)] for i, cat in enumerate(cats)}

st.header(f"🏘️ Áreas POT en {sel}")
mapa_pot = folium.Map(location=centro, zoom_start=12)
for feat in pot_local:
    uso = feat["properties"]["uso_pot_simplificado"]
    col = color_map[uso]
    folium.GeoJson(
        feat,
        style_function=lambda f, color=col: {
            "color":     color,
            "fillColor": color,
            "fillOpacity": 0.4,
            "weight":      1
        },
        tooltip=folium.GeoJsonTooltip(fields=["uso_pot_simplificado"], labels=False)
    ).add_to(mapa_pot)
st_folium(mapa_pot, width=700, height=500)

# 3.5 Selector de área POT y navegación
st.subheader("4️⃣ Selecciona el uso POT simplificado de tu interés")
uso_sel = st.selectbox("Tipo de uso según POT:", options=cats)

col1, col2 = st.columns(2)
with col1:
    if st.button("🔙 Regresar a localidad"):
        st.session_state.step = 2
        st.stop()
with col2:
    if st.button("Confirmar área POT"):
        st.session_state.uso_sel = uso_sel
        st.session_state.step   = 4
        st.stop()
