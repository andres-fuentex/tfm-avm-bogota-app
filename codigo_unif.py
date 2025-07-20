# BLOQUE 1 PREPARACION DE ENTORNO INSTALACION DE LIBRERIAS 
# EN ESTE BLOQUE QUIERO UNA LINE ADE CARGANDO Y TAL VEZ CON UN TTL MOSTRAR UN POCO DE TEXTO
# PRIMERO ESTO ES UN RABAJO DE GRADO DE BLA BLA BLA 
# UNOS SEGUNDOS DESPUES MIENSTRAS VA CARGANDO ESTE MODULO TRABAJA CON DATOS PUBLICOS 
# EL TRATAMIENTO DE LOS DATOS PUBLICOS FUE REALIZADO BASADO EN XXXXX
# MAS O MENOS CADA 30 SEG 

!apt install -y libpangocairo-1.0-0
!pip install weasyprint
!pip install -U kaleido
!pip install --upgrade plotly>=6.1.1 kaleido # este es importante para que sean compatibles
!kaleido_get_chrome # complemento necesario por la actualizacion de plotly


## Importación de librerías

import os
from datetime import datetime           
import base64                          # Para codificar imágenes a base64 en el informe final
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio                # Motor de exportación (Kaleido)
from shapely.geometry import MultiPoint # Para construir geometrías combinadas
from IPython.display import display, Markdown
from weasyprint import HTML            # Para convertir el HTML final 
from io import BytesIO                # clave para almacenar en ram las imagenes


#carga de data sets

localidades = gpd.read_file("https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_localidad.geojson")
areas = gpd.read_file("https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_area.geojson")
manzanas = gpd.read_file("https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/tabla_hechos.geojson")
transporte = gpd.read_file("https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_transporte.geojson")
colegios = gpd.read_file("https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_colegios.geojson")

# ACA CUANDO YA ESTEMOS CARGADOS MUESTRA MENSAJE DE DATOS CARGADOS ESTAMOS LISTOS PARA EL ANALISIS
# MUESTA BOTON INICIO (VERDE) O CANCELA (ROJO) 

# BLOQUE 2
# PRIMER MAPA QUE ES DE CONTEXTO MUESTRA LAS LOCALIDADES 
# POR FAVOR SELECCIONA LA LOCALIDAD
# Cálculo dinámico del centro de tus localidades
bounds = localidades.total_bounds  # [minx, miny, maxx, maxy]
center = {
    "lon": (bounds[0] + bounds[2]) / 2,
    "lat": (bounds[1] + bounds[3]) / 2
}

# Crear el mapa de contexto
fig = px.choropleth_map(
    localidades,
    geojson=localidades.geometry,
    locations=localidades.index,
    color="nombre_localidad",
    hover_name="nombre_localidad",
    hover_data=["num_localidad"]
)

# Configurar el mapa base  y centrado
fig.update_layout(
    map={
        "style": "carto-positron",  # fondo de Carto
        "center": center,
        "zoom": 9
    },
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

fig.show()

# UNA VEZ EL USUARIO SELECCIONA LA LOCALIDAD ESO SE LLEVA A UNA CAJA Y SE LE MUESTRA EL TEXTO DE LA LOCALIDAD SELECCIONADA 
# BOTON CONFIRMAR LA LOCALIDAD (VERDE), REGERESAR ( ROJO ) VUELVE A LA PANTALLA DE CARGA DE DATOS, BOTON INICIO ( REGACARGA LA APP)

# BLOQUE 3
 
# SEGUNDO MAPA SE SUPONE QUE EL USUARIO LO SELECCIONA CON UN CLICK Y SE GUARDA EN LA VARIABLE SELECCION Y CONFIRMO EN EL BOTON ANTERIOR
# UN TEXTO QUE DIRA DE ACUERDO CON EL PLAN DE ORDENAMIENTO TERRITORIAL DE LA CIUDAD DE BOGOTA LA LOCALIDAD {seleccion} DISPONE DE UNA DISTRIBUCION DE IMPACTO POR EL POT ASI 
# ENTRAN LOS DOS MAPAS SIGUIENTES

#SEGUNDO MAPA
# Simulamos que seleccionaste "Chapinero"
seleccion = "Chapinero" # ESTO SERA UNA CAPTURA DE CLICK PARA PODER GENERARLO
localidades["seleccionada"] = localidades["nombre_localidad"] == seleccion

# Cálculo dinámico del centro de la localidad seleccionada
gdf_sel = localidades[localidades["seleccionada"]]
bounds = gdf_sel.total_bounds  # [minx, miny, maxx, maxy]
center = {
    "lon": (bounds[0] + bounds[2]) / 2,
    "lat": (bounds[1] + bounds[3]) / 2
}

# uso de mapas desde plotly
fig = px.choropleth_map(
    localidades,
    geojson=localidades.geometry,
    locations=localidades.index,
    color="seleccionada",
    hover_name="nombre_localidad",
    color_discrete_map={True: "red", False: "lightgray"}
)

# Aplicar centro y zoom
fig.update_layout(
    map={
        "style": "carto-positron",
        "center": center,
        "zoom": 10
    },
    margin={"r":0,"t":0,"l":0,"b":0}
)

fig.show()

# Guardamos la figura para el informe
mapa_localidad = fig

mapa_localidad.update_layout(
    autosize=False,
    width=400,
    height=300,
    margin=dict(l=0, r=0, t=30, b=0)
)
buffer_localidad = BytesIO()
mapa_localidad.write_image(buffer_localidad, format='png')  # CON ESTO LO GUARDO PARA EL INFORME DESCARGABLE

# TERCER MAPA EN ESTE SE MUESTRA COMO EL POT SE VISUALIZA EN ESA LOCALIDAD MEDIANTE COLORES SE PUEDE VER DONDE ESTA EL POT ACTUANDO Y COMO

localidad_sel = localidades[localidades["nombre_localidad"] == seleccion]

codigo_localidad = localidad_sel["num_localidad"].values[0]

# Filtrar áreas que pertenecen a esa localidad
areas_sel = areas[areas["num_localidad"] == codigo_localidad]

# se define paleta

# Determinamos categorías únicas y asignamos colores
cats = areas_sel["uso_pot_simplificado"].unique().tolist()
palette = px.colors.qualitative.Plotly  # lista de colores
color_map = {cat: palette[i % len(palette)] for i, cat in enumerate(cats)}

# Aseguramos que "Sin clasificación" esté también en el mapa
if "Sin clasificación" not in color_map:
    color_map["Sin clasificación"] = "#2b2b2b"

b = areas_sel.total_bounds  # [minx, miny, maxx, maxy]
center = {"lon": (b[0] + b[2]) / 2, "lat": (b[1] + b[3]) / 2}

# MAPA DE MANZANAS CREO QUE SE PODRIA UNIFICAR CON EL ANTERIOR PUESTO QUE ESTE HACE O MISMO SOLO QUE CARGA LOS POLIGONOS DE LAS MANZANAS PERO CON LOS COLORES DEL AREA 
# ACA ES DONDE EL USUARIO DEBERIA CLICKEAR Y SELEIONAR LA MANZANA 
# COMO EN ESTE MAPA SE MUESTRAN LOS POLIGONOS DE LAS MANZANAS SE MOSTRARA TEXTO DE SELECCIONE LA MANZANA DE INTERES O LA UBICAION DE DONDE DESEA CONOCER INFORMACION
# ESE CLICK DE SELECCION SOBRE UN POLIGONO DE MANZANA DE IGUAL FORMA SE LLEVA A UNA CAJA BAJO LA MISMA DINAMICA CUANDO SELECCIONO LA LOCALIDAD
# UNA VEZ EL USUARIO SELECCIONA LA MANZANA ESO SE LLEVA A UNA CAJA Y SE LE MUESTRA EL TEXTO DE LA MANZANA SELECCIONADA
# BOTONES DE CONFIRMAR MANZANA (VERDE) VA AL BLOQUE SIGUIENTE, REGRESAR ( ROJO) VA AL BLOQUE ANTERIOR,  AZUL (RECARGA LA APP)

# Filtrar manzanas en la localidad seleccionada
manzanas_chapinero = manzanas[manzanas["num_localidad"] == codigo_localidad].copy()

# Merge para traer `uso_pot_simplificado` desde areas_sel
manzanas_chapinero = manzanas_chapinero.merge(
    areas_sel[["id_area", "uso_pot_simplificado"]],
    on="id_area",
    how="left"
)

# Rellenar con categoría por defecto donde falte
manzanas_chapinero["uso_pot_simplificado"] = (
    manzanas_chapinero["uso_pot_simplificado"]
    .fillna("Sin clasificación")
)

#  Cálculo dinámico del centro de las manzanas en Chapinero
bounds_m = manzanas_chapinero.total_bounds  # [minx, miny, maxx, maxy]
center_m = {
    "lon": (bounds_m[0] + bounds_m[2]) / 2,
    "lat": (bounds_m[1] + bounds_m[3]) / 2
}

#  Crear el mapa con maplibre la actualizacion de plotly 
fig = px.choropleth_map(
    manzanas_chapinero,
    geojson=manzanas_chapinero.geometry,
    locations=manzanas_chapinero.index,
    color="uso_pot_simplificado",
    hover_name="id_manzana_unif",
    hover_data=["estrato", "valor_m2"],
    color_discrete_map=color_map
)

# Aplicar estilo, centro y título
fig.update_layout(
    map={
        "style": "carto-positron",
        "center": center_m,
        "zoom": 12
    },
    title="Manzanas en Chapinero coloreadas por uso POT simplificado",
    margin={"r":0, "t":30, "l":0, "b":0}
)

#  Mostrar y guardar para el informe
fig.show()
mapa_manzanas = fig


mapa_manzanas.update_layout(
    autosize=False,
    width=600,
    height=500,
    margin=dict(l=0, r=0, t=30, b=0)
)
buffer_manzanas = BytesIO()
mapa_manzanas.write_image(buffer_manzanas, format='png') # ME LO GUARDO PARA EL INFORME



# BOTONES DE CONTINUAR (VERDE) VA AL BLOQUE SIGUIENTE REGRESAR ( ROJO) VA AL BLOQUE ANTERIOR AZUL (RECARGA LA APP)

#BLOQUE 4 
# COMO TENEMOS UN CLICK DE ATRAS ESE DATO SERA EL QUE REEMPLAZA A manzana_sel Y ENTRANDO A LA EJECUCION DE ESTE BLOQUE 
# TEXTO A CONTINUACION SE MUESTRA EL CONTEXTO DE TRANSPORTE Y EDUCACION PARA LA MANZANA QUE UD SELECCIONO PERMITIENDO CONOCER INFORMACION BLA BLA BLA
# TEXTO PARA TRANSPORTE SE MUESTRA UN RADIO DE 800 METROS Y EN COLOR ROJO LAS ESTACIONES QUE SE ENCUENTRAN PROXIMAS A SU MANZANA XXXX
#  Seleccionar una manzana de ejemplo
manzana_sel = manzanas_chapinero.sample(1) # ES EL DATO id_manzana_unif QUE SE CAPTURO EN LA CAJA CONTINUAR AL FINAL DEL BLOQUE 3

#  Reproyectar a CRS métrico y calcular centroid en ese CRS
manzana_proj = manzana_sel.to_crs(epsg=3116)
centroide_proj = manzana_proj.geometry.centroid.iloc[0]

#  Reproyectar el centroide a WGS84 para Plotly
centroide = gpd.GeoSeries([centroide_proj], crs=3116).to_crs(epsg=4326).iloc[0]
lon0, lat0 = centroide.x, centroide.y

#  Coordenadas de la manzana y del buffer
#  Manzana en WGS84
manzana_wgs = manzana_proj.to_crs(epsg=4326)
coords_m = list(manzana_wgs.geometry.iloc[0].exterior.coords)
lon_m, lat_m = zip(*coords_m)

#  Buffer 800 m
buffer_proj = manzana_proj.buffer(800)
buffer_wgs = gpd.GeoSeries([buffer_proj.iloc[0]], crs=3116).to_crs(epsg=4326).iloc[0]
coords_b = list(buffer_wgs.exterior.coords)
lon_b, lat_b = zip(*coords_b)

#  Extraer puntos de estaciones asociadas
id_combi = manzana_sel["id_combi_acceso"].iloc[0]
multipunto = transporte.loc[transporte["id_combi_acceso"] == id_combi, "geometry"].iloc[0]
pts = gpd.GeoDataFrame(geometry=list(multipunto.geoms), crs=transporte.crs).to_crs(epsg=4326)
lon_p, lat_p = pts.geometry.x, pts.geometry.y

#  Construcción del mapa con plotly
fig = go.Figure()

# Manzana
fig.add_trace(go.Scattermap(
    lon=lon_m, lat=lat_m,
    mode="lines",
    fill="toself",
    fillcolor="rgba(0,128,0,0.3)",
    line=dict(color="darkgreen", width=2),
    name="Manzana seleccionada"
))

# Buffer
fig.add_trace(go.Scattermap(
    lon=lon_b, lat=lat_b,
    mode="lines",
    fill="toself",
    fillcolor="rgba(255,0,0,0.1)",
    line=dict(color="red", width=1),
    name="Buffer 800 m"
))

# Puntos estaciones
fig.add_trace(go.Scattermap(
    lon=lon_p, lat=lat_p,
    mode="markers",
    marker=dict(size=10, color="red"),
    name="Estaciones TM"
))

# Layout usando maplibre
fig.update_layout(
    map=dict(
        style="carto-positron",
        center=dict(lon=lon0, lat=lat0),
        zoom=14
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    title="Detalle de Manzana con Buffer y Estaciones de TM"
)

fig.show()

mapa_transporte = fig

mapa_transporte.update_layout(
    autosize=False,
    width=600,
    height=500,
    margin=dict(l=0, r=0, t=30, b=0)
)
buffer_transporte = BytesIO()
mapa_transporte.write_image(buffer_transporte, format='png') # SE GUARDA PARA EL INFORME DESCARGABLE 

# ENTRA MAPA COLEGIOS
# TEXTO PARA CONTEXTO EDUCATIVO SE MUESTRA EN UN RADIO DE 1000 METROS DE COLOR AZUL LA CANTIDAD DE COLEGIOS QUE SE ENCUENTRAN CERCA DE SU MANZANA

#  Identificadores de la manzana y combinación de colegios
id_seleccionado = manzana_sel["id_manzana_unif"].iloc[0]
id_colegios     = manzana_sel["id_com_colegios"].iloc[0]

#  Calcular centroide de la manzana en WGS84
manzana_proj  = manzana_sel.to_crs(epsg=3116)
centroide_proj = manzana_proj.geometry.centroid.iloc[0]
centroide      = gpd.GeoSeries([centroide_proj], crs=3116).to_crs(epsg=4326).iloc[0]

#  Coordenadas de la manzana en WGS84
manzana_wgs = manzana_proj.to_crs(epsg=4326)
coords      = list(manzana_wgs.geometry.iloc[0].exterior.coords)
lon, lat    = zip(*coords)

# Buffer de 1000 m en WGS84
buffer_proj  = manzana_proj.buffer(1000)
buffer_wgs   = gpd.GeoSeries([buffer_proj.iloc[0]], crs=3116).to_crs(epsg=4326).iloc[0]
coords_buff  = list(buffer_wgs.exterior.coords)
lon_buff_col, lat_buff_col = zip(*coords_buff)

#  Extraer y reproyectar geometrías de colegios asociados
filtered = colegios[colegios["id_com_colegios"] == id_colegios]

lon_p, lat_p = [], []
if not filtered.empty:
    geom = filtered.geometry.iloc[0]
    if isinstance(geom, MultiPoint):
        geoms = list(geom.geoms)
    elif isinstance(geom, Point):
        geoms = [geom]
    else:
        # Intentar iterar en caso de GeometryCollection u otro
        try:
            geoms = [g for g in geom]
        except:
            geoms = []
    pts = gpd.GeoDataFrame(geometry=geoms, crs=colegios.crs).to_crs(epsg=4326)
    lon_p = pts.geometry.x.tolist()
    lat_p = pts.geometry.y.tolist()
else:
    print("No se encontraron geometrías de colegios para esta manzana.")

#  Construcción del mapa 
fig = go.Figure()

#  Polígono de la manzana (verde)
fig.add_trace(go.Scattermap(
    lon=lon, lat=lat,
    mode="lines", fill="toself",
    fillcolor="rgba(0,128,0,0.3)",
    line=dict(color="darkgreen", width=2),
    name="Manzana seleccionada"
))

#  Buffer 1000 m (azul tenue)
fig.add_trace(go.Scattermap(
    lon=lon_buff_col, lat=lat_buff_col,
    mode="lines", fill="toself",
    fillcolor="rgba(0,0,255,0.1)",
    line=dict(color="blue", width=1),
    name="Buffer 1000 m"
))

#  Puntos de colegios
if lon_p:
    fig.add_trace(go.Scattermap(
        lon=lon_p, lat=lat_p,
        mode="markers+text",
        marker=dict(size=10, color="blue"),
        textposition="top right",
        name="Colegios cercanos"
    ))

# Configuración del layout 
fig.update_layout(
    map=dict(
        style="carto-positron",
        center=dict(lon=centroide.x, lat=centroide.y),
        zoom=14
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    title=f"Manzana {id_seleccionado} con buffer y colegios cercanos"
)

#  Mostrar 
fig.show()
mapa_colegios      = fig

mapa_colegios.update_layout(
    autosize=False,
    width=600,
    height=500,
    margin=dict(l=0, r=0, t=30, b=0)
)
buffer_colegios = BytesIO()
mapa_colegios.write_image(buffer_colegios, format='png') # SE GUARDA PARA INFORME DESCARGABLE 


# BOTONES DE CONTINUAR (VERDE) VA AL BLOQUE SIGUIENTE REGRESAR ( ROJO) VA AL BLOQUE ANTERIOR AZUL (RECARGA LA APP)

# BLOQUE 5 

# TEXTO ANALISIS COMPARATIVO DE SU MANZANA FRENTE AL POT 

# Buscar su id_area (puede ser NaN)
id_area_manzana = manzana_sel["id_area"].values[0]

# Filtrar manzanas en esa misma área
if pd.notna(id_area_manzana):
    manzanas_area = manzanas_chapinero[manzanas_chapinero["id_area"] == id_area_manzana]
else:
    manzanas_area = manzanas_chapinero[manzanas_chapinero["id_area"].isna()]

# Calcular valor promedio m²
promedio_area = manzanas_area["valor_m2"].mean()
valor_manzana = manzana_sel["valor_m2"].values[0]

# TEXTO EL VALOR DEL PRECIO DEL METRO CUADRADO EN UN RADIO DE 300 METROS A PARTIR DE LA MANZANA SELECCIONADA ES DE 

# Crear buffer de 300 m en CRS proyectado
buffer_300_proj = manzana_sel.to_crs(epsg=3116).buffer(300).to_crs(epsg=4326)

# Filtrar manzanas dentro del buffer
manzanas_buffer = manzanas_chapinero[manzanas_chapinero.geometry.intersects(buffer_300_proj.iloc[0])]

# Calcular valor promedio
promedio_buffer = manzanas_buffer["valor_m2"].mean()

print(f"Promedio m² en buffer de 300m: ${promedio_buffer:,.0f}")

# TEXTO ESTE GRAFICO LE PERMITE VER UNA COMPARACION ENTRE EL VALOR DEL METRO CUADRADO ASIGNADO A SU MANZANA CON EL VALOR DEL METRO CUADRADO SEGUN LAS OTRAS MANZANAS ASIGNADAS AL MOSMO POT Y AL VALOR MER METRO CUADRADO EN UN RADIO DE 300 MTS CON OTRAS MANZANAS
fig = go.Figure()
fig.add_trace(go.Bar(
    x=["Manzana seleccionada"],
    y=[valor_manzana],
    name="Manzana",
    text=[f"${valor_manzana:,.0f}"],
    textposition="outside",
    marker_color='rgba(0, 102, 204, 0.8)'
))
fig.add_trace(go.Bar(
    x=["Promedio área POT"] if pd.notna(id_area_manzana) else ["Promedio sin área"],
    y=[promedio_area],
    name="Área POT",
    text=[f"${promedio_area:,.0f}"],
    textposition="outside",
    marker_color='rgba(0, 102, 204, 0.6)'
))
fig.add_trace(go.Bar(
    x=["Promedio 300m"],
    y=[promedio_buffer],
    name="Buffer 300m",
    text=[f"${promedio_buffer:,.0f}"],
    textposition="outside",
    marker_color='rgba(0, 102, 204, 0.4)'
))

fig.update_layout(
    title="Comparativo de valor m² respecto al promedio del área POT y respecto a 300 metros a la redonda",
    yaxis_title="Valor por metro cuadrado",
    barmode="group",
    template="simple_white"
)

fig.show()


fig_valor_m2 = fig

fig_valor_m2.update_layout(
    autosize=False,
    width=600,
    height=500,
    margin=dict(l=0, r=0, t=30, b=0)
)
buffer_valorm2 = BytesIO()
fig_valor_m2.write_image(buffer_valorm2, format='png') # SE GUARDA PARA EL INFORME DESCARGABLE 

# SE PROYECTA UNA DISTRIBUCION DENTRO DE LOS 500 METROS COMO ESTA EL TEMA POT
buffer_uso = manzana_sel.to_crs(epsg=3116).buffer(500).to_crs(epsg=4326)
manzanas_buffer_uso = manzanas_chapinero[manzanas_chapinero.geometry.intersects(buffer_uso.iloc[0])]

# Validación columna 'uso_pot_simplificado'
if "uso_pot_simplificado_y" in manzanas_chapinero.columns and "uso_pot_simplificado_x" in manzanas_chapinero.columns:
    manzanas_chapinero["uso_pot_simplificado"] = (
        manzanas_chapinero["uso_pot_simplificado_y"]
        .combine_first(manzanas_chapinero["uso_pot_simplificado_x"])
        .fillna("Sin clasificación POT")
    )
elif "uso_pot_simplificado" in manzanas_chapinero.columns:
    # Ya existe una columna única correcta
    manzanas_chapinero["uso_pot_simplificado"] = (
        manzanas_chapinero["uso_pot_simplificado"].fillna("Sin clasificación POT")
    )
else:
    # Crear columna vacía si no hay ninguna fuente
    manzanas_chapinero["uso_pot_simplificado"] = "Sin clasificación POT"

# TEXTO EN UN RADIO DE 500 METROS SE PUEDE APRECIAR UNA DISTRIBUCION DEL IMPACTO POT ASI

# Conteo de usos dentro del buffer
conteo_uso = (
    manzanas_buffer_uso["uso_pot_simplificado"]
    .value_counts()
    .reset_index()
)
conteo_uso.columns = ["uso", "cantidad"]

# Construir la lista de colores según el orden de 'uso'
colores = [color_map[uso] for uso in conteo_uso["uso"]]

import plotly.express as px
fig = px.pie(
    conteo_uso,
    values="cantidad",
    names="uso",
    title=(
        f"Distribución de usos POT en buffer de 500m<br>"
        f"Manzana {manzana_sel['id_manzana_unif'].values[0]}"
    ),
    color_discrete_sequence=colores
)

fig.update_traces(textinfo='percent+label')
fig.update_layout(template="simple_white")
fig.show()

dist_pot_500m = fig

dist_pot_500m.update_layout(
    autosize=False,
    width=600,
    height=500,
    margin=dict(l=0, r=0, t=30, b=0)
)
buffer_dist_pot = BytesIO()
dist_pot_500m.write_image(buffer_dist_pot, format='png')

# TEXTO AHORA BIEN TOMANDO COMO REFERENCIA EL INDICE DE PRECIOS DE VIVIENDA USADA DEL BANCO DE LA REPUBLICA SE PROYECTA UN VALOR DEL METRO CUADRADO PARA LA MANZANA SELECCIONADA EN LOS PROXIMOS AÑOS ASI

serie_proyeccion = manzana_sel[
    ["valor_m2","valor_2025_s1", "valor_2025_s2", "valor_2026_s1", "valor_2026_s2"]
].values.flatten()

fechas = ["2024-S2","2025-S1", "2025-S2", "2026-S1", "2026-S2"]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=fechas,
    y=serie_proyeccion,
    mode="lines+markers+text",
    line=dict(color="royalblue", width=3),
    marker=dict(size=8),
    text=[f"${v:,.0f}" for v in serie_proyeccion],
    textposition="top center",
    name="Proyección valor m²"
))

fig.update_layout(
    title=f"Evolución proyectada del valor m² - Manzana {manzana_sel['id_manzana_unif'].values[0]}",
    xaxis_title="Periodo",
    template="simple_white"
)

fig.show()

proyeccion_m2 = fig

proyeccion_m2.update_layout(
    autosize=False,
    width=600,
    height=500,
    margin=dict(l=0, r=0, t=30, b=0)
)
buffer_proyeccion = BytesIO()
proyeccion_m2.write_image(buffer_proyeccion, format='png') # SE GUARDA PARA EL INFORME DESCARGABLE 

# OJO OJO OJO 
# ESTO VA POR DEBAJO SOLO ES PARA EL INFORME NO SE MUESTRA EN PANTALLA 

#  Traer nombre de localidad
codigo_localidad = manzana_sel["num_localidad"].values[0]
nombre_localidad = localidades.loc[
    localidades["num_localidad"] == codigo_localidad, 
    "nombre_localidad"
].values[0]

#  Crear la tabla ficha una sola vez
ficha = pd.DataFrame({
    "ID Manzana":          [manzana_sel["id_manzana_unif"].values[0]],
    "Localidad":           [nombre_localidad],
    "Estrato":             [int(manzana_sel["estrato"].values[0])],
    "Valor m²":            [manzana_sel["valor_m2"].values[0]],
    "Colegios cercanos":   [manzana_sel["colegio_cerca"].values[0]],
    "Estaciones cercanas": [manzana_sel["estaciones_cerca"].values[0]],
    "Rentabilidad":        [manzana_sel["rentabilidad"].values[0]]
})

#  Función de estilo para Rentabilidad
def estilo_rentabilidad(val):
    if val == "alta":
        return "font-weight: bold; color: green"
    elif val == "media":
        return "font-weight: bold; color: orange"
    elif val == "baja":
        return "font-weight: bold; color: red"
    else:
        return ""

#  Aplicar el estilo solo a la columna "Rentabilidad" y ocultar índice
ficha_estilizada = (
    ficha
    .style
    .set_properties(**{"text-align": "center"})
    .map(estilo_rentabilidad, subset=["Rentabilidad"])
    .hide(axis="index")
)
# BOTONES DE CONTINUAR (VERDE) VA AL BLOQUE SIGUIENTE REGRESAR ( ROJO) VA AL BLOQUE ANTERIOR AZUL (RECARGA LA APP)

# BLOQUE 6

# TEXTO CONTECTO DE SEGURIDAD CON BASE EN INFORMACION REPORTADA POR LA SECRETARIA DE CONVIVENCIA Y SEGURIDAD CIUDADANA LA LOCALIDAD DONDE SE UBICA SU MANZANA SE PUEDE CLASIFICAR ASI

# Crear copia del dataframe de localidades
df_seguridad = localidades[["nombre_localidad", "num_localidad", "cantidad_delitos", "nivel_riesgo_delictivo"]].copy()

# Marcar la localidad activa
cod_loc = manzana_sel["num_localidad"].values[0]
df_seguridad["es_localidad_actual"] = df_seguridad["num_localidad"] == cod_loc

df_seguridad["etiqueta"] = df_seguridad.apply(
    lambda row: row["nivel_riesgo_delictivo"] if row["es_localidad_actual"] else "",
    axis=1
)

df_seguridad.sort_values("cantidad_delitos", ascending=True, inplace=True)

fig = px.bar(
    df_seguridad,
    x="cantidad_delitos",
    y="nombre_localidad",
    orientation="h",
    color="es_localidad_actual",
    color_discrete_map={True: "darkgreen", False: "rgba(0,100,0,0.3)"},
    text="etiqueta"
)

fig.update_traces(textposition="outside")

fig.update_layout(
    title="Contexto de seguridad por localidad\nFuente: Secretaría Distrital de Seguridad y Convivencia",
    xaxis_title="Cantidad de delitos",
    yaxis_title=" ",
    showlegend=False,
    template="simple_white"
)

# <<< Agregar esto para preservar el orden según cantidad_delitos >>>
fig.update_yaxes(categoryorder="total ascending")

fig.show()

contexto_seguridad = fig

contexto_seguridad.update_layout(
    autosize=False,
    width=600,
    height=500,
    margin=dict(l=0, r=0, t=30, b=0)
)
buffer_seguridad = BytesIO()
contexto_seguridad.write_image(buffer_seguridad, format='png') # SE GUARDA PARA EL INFORME DESCARGABLE

# NO TENGO CLARO DONDE LO USO
uso_pot_mayoritario = manzanas_buffer_uso["uso_pot_simplificado"].value_counts().idxmax()

# TEXTO FIN DEL ANALISIS DE SU MANZANA CON EL USO DE DATOS ABIERTOS DEJES DESCARGAR EL INFORME EJECUTIVO?

# BOTONES DE DESCARGAR (VERDE) VA AL BLOQUE SIGUIENTE, REGRESAR ( ROJO) VA AL BLOQUE ANTERIOR, AZUL SALIR (RECARGA LA APP)

# BLOQUE 7
# GENERANDO INFORME
# BARRA SIMULADA DE CREANDO INFORME 

texto0 = (
    f"El presente informe ha sido generado automáticamente como parte del trabajo final del Máster en Visual Analytics y Big Data "
    f"de la Universidad Internacional de La Rioja. Este documento es el resultado del proyecto desarrollado por "
    f"<strong>Sergio Andrés Fuentes Gómez</strong> y <strong>Miguel Alejandro González</strong>, bajo la dirección de "
    f"<strong>Mariana Ríos Ortegón</strong>. Forma parte de un piloto experimental orientado a la aplicación práctica de técnicas "
    f"de análisis visual y ciencia de datos en contextos urbanos reales."
)

# Variables para texto de contexto territorial
estrato       = int(manzana_sel["estrato"].values[0])
id_manzana    = manzana_sel["id_manzana_unif"].values[0]
nombre_localidad = nombre_localidad 

texto1 = (
    f"De acuerdo con su selección, es importante resaltar que la manzana identificada con el código "
    f"<strong>{id_manzana}</strong>, ubicada en la localidad <strong>{nombre_localidad}</strong>, "
    f"correspondiente al <strong>estrato {estrato}</strong>, presenta condiciones clave para evaluar "
    f"su potencial de valorización en el contexto urbano de Bogotá.<br><br>"
    f"En el mapa general se puede observar su ubicación espacial dentro del límite urbano, así como su "
    f"disposición relativa frente a otras unidades de análisis catastral. Este contexto geográfico es "
    f"fundamental para la comprensión de las dinámicas socioespaciales y normativas que afectan "
    f"el comportamiento del valor del suelo urbano."
)

# Variables para texto de entorno de servicios
colegios   = int(manzana_sel["colegio_cerca"].values[0])
estaciones = int(manzana_sel["estaciones_cerca"].values[0])

texto2 = (
    f"Desde la perspectiva del entorno inmediato, la manzana seleccionada cuenta con "
    f"<strong>{colegios} colegios</strong> ubicados a menos de <strong>1.000 metros</strong>, "
    f"lo que sugiere la accesibilidad educativa para esa manzana. Esta información proviene de los datos "
    f"publicados por la <strong>Secretaría Distrital de Educación</strong> en el marco de los registros "
    f"de instituciones oficiales y privadas del Distrito Capital.<br><br>"

    f"En términos de movilidad, se identifican <strong>{estaciones} estaciones de TransMilenio</strong> "
    f"dentro de un radio de <strong>500 metros</strong>, de acuerdo con la georreferenciación oficial "
    f"del sistema TransMilenio, procesada por la <strong>Secretaría Distrital de Movilidad</strong>. "
    f"Este indicador refleja la conectividad y accesibilidad al sistema de transporte masivo, factor clave "
    f"en los modelos de valoración urbana.<br><br>"

    f"Ambos factores evidencian la posición de esta manzana dentro del tejido urbano y aportan a su potencial "
    f"de valorización futura."
)

# Obtener datos POT desde dataframe 'areas'
id_area_manzana = manzana_sel["id_area"].values[0]
area_info = areas[areas["id_area"] == id_area_manzana]

area_pot = area_info["area_pot"].values[0]
uso_pot = area_info["uso_pot_simplificado"].values[0]

# Añadirlos manualmente a manzana_sel para que la función funcione sin cambio
manzana_sel["area_pot"] = area_pot
manzana_sel["uso_pot_simplificado"] = uso_pot

# Variables para texto de normativa POT
area_pot           = manzana_sel["area_pot"].values[0]
uso_asignado       = manzana_sel["uso_pot_simplificado"].values[0]
uso_pot_mayoritario = uso_pot_mayoritario  # Variable que calculaste previamente
valor_area         = f"${promedio_area:,.0f}"

texto3 = (
    f"Desde el punto de vista normativo, la manzana se encuentra asignada al área denominada "
    f"<strong>{area_pot}</strong> dentro del marco del <strong>Plan de Ordenamiento Territorial (POT)</strong> "
    f"de Bogotá, lo cual implica un conjunto de restricciones y oportunidades en el uso del suelo. "
    f"Su uso principal ha sido clasificado como <strong>{uso_asignado}</strong>, según el modelo de "
    f"simplificación normativa aplicado al dataset de áreas de actividad.<br><br>"

    f"Al observar el entorno de la manzana en un radio de <strong>500 metros</strong>, se encuentra que el uso "
    f"<strong>predominante</strong> en esa zona es <strong>{uso_pot_mayoritario}</strong>, lo que evidencia "
    f"una coherencia o posible tensión entre el uso individual asignado y la estructura funcional del "
    f"entorno inmediato.<br><br>"

    f"El valor promedio del metro cuadrado dentro del área de afectación POT asignada a esta manzana es de "
    f"<strong>{valor_area}</strong>, lo que permite comparar la posición relativa del inmueble frente al "
    f"promedio normativo de su zona, contribuyendo al análisis integral de su potencial de valorización."
)

# Variables para texto de valor del suelo y rentabilidad
valor_m2         = manzana_sel["valor_m2"].values[0]
rentabilidad     = manzana_sel["rentabilidad"].values[0]
promedio_buffer = float(promedio_buffer)
valor_area = valor_area


texto4 = (
    f"Según datos del <strong>Observatorio Técnico Catastral</strong> de Bogotá, el valor actual del metro "
    f"cuadrado en esta manzana es de <strong>${valor_m2:,.0f}</strong>. Este valor fue comparado con el "
    f"promedio del entorno inmediato, calculado a partir de las manzanas ubicadas en un radio de "
    f"<strong>300 metros</strong>, obteniendo un valor promedio de <strong>${promedio_buffer:,.0f}</strong>.<br><br>"

    f"Asímismo, se analizó el valor promedio del metro cuadrado dentro del área de asignación normativa del POT "
    f"(área POT), cuyo promedio registrado es de <strong>{valor_area}</strong>.<br><br>"

    f"Con base en estas comparaciones y en los factores de accesibilidad y normatividad descritos previamente, "
    f"el modelo de evaluación automática estima que esta manzana presenta una rentabilidad "
    f"<strong>{rentabilidad}</strong>."
)

# Variables para texto de contexto de seguridad
cod_loc = manzana_sel["num_localidad"].values[0]
info_seguridad = df_seguridad[df_seguridad["num_localidad"] == cod_loc].iloc[0]

nombre_localidad = info_seguridad["nombre_localidad"]
nivel_riesgo     = info_seguridad["nivel_riesgo_delictivo"]
delitos          = int(info_seguridad["cantidad_delitos"])

texto5 = (
    f"En lo referente al contexto de seguridad, la manzana se encuentra ubicada en la localidad "
    f"<strong>{nombre_localidad}</strong> (código {cod_loc}), la cual ha sido clasificada como de "
    f"<strong>riesgo {nivel_riesgo}</strong>, según los datos de criminalidad reportados por la "
    f"<strong>Secretaría Distrital de Seguridad, Convivencia y Justicia</strong>. Durante el último año, "
    f"se registró un total de <strong>{delitos} delitos</strong> en esta jurisdicción.<br><br>"

    f"Esta información permite identificar posibles factores de afectación o valorización asociados a la "
    f"percepción de seguridad del entorno inmediato, elemento relevante en las decisiones de inversión inmobiliaria."
)


# Variables para texto de proyección del valor m²
v_2025_1 = manzana_sel["valor_2025_s1"].values[0]
v_2025_2 = manzana_sel["valor_2025_s2"].values[0]
v_2026_1 = manzana_sel["valor_2026_s1"].values[0]
v_2026_2 = manzana_sel["valor_2026_s2"].values[0]

# Formatear los valores en moneda
v_2025_1_fmt = f"${v_2025_1:,.0f}"
v_2025_2_fmt = f"${v_2025_2:,.0f}"
v_2026_1_fmt = f"${v_2026_1:,.0f}"
v_2026_2_fmt = f"${v_2026_2:,.0f}"

texto6 = (
    f"Con base en las proyecciones del <strong>Índice de Precios de Vivienda Usada (IPVU)</strong>, publicado por el "
    f"<strong>Banco de la República</strong>, se estima que el valor del metro cuadrado en esta manzana podría alcanzar "
    f"los siguientes niveles en los próximos periodos:<br><br>"
    f"- <strong>{v_2025_1_fmt}</strong> en el primer semestre de 2025,<br>"
    f"- <strong>{v_2025_2_fmt}</strong> en el segundo semestre de 2025,<br>"
    f"- <strong>{v_2026_1_fmt}</strong> en el primer semestre de 2026,<br>"
    f"- <strong>{v_2026_2_fmt}</strong> en el segundo semestre de 2026.<br><br>"
    f"Estas cifras permiten anticipar una evolución favorable del valor del suelo en esta unidad catastral, "
    f"lo cual puede ser aprovechado para fines de inversión, teniendo en cuenta tanto la dinámica histórica "
    f"como el entorno normativo y funcional previamente descrito."
)

titulo = "Informe de Análisis de Inversión Inmobiliaria"

# Convertir buffer de imagenes a base64
def buffer_a_base64(buffer):
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

# Aplicar a tus buffers
img_colegios_base64 = buffer_a_base64(buffer_colegios)
img_transporte_base64 = buffer_a_base64(buffer_transporte)
img_distribucion_base64 = buffer_a_base64(buffer_dist_pot)
img_mapapot_base64 = buffer_a_base64(buffer_mapa_pot)
img_manzanas_base64 = buffer_a_base64(buffer_manzanas)
img_valorm2_base64 = buffer_a_base64(buffer_valorm2)
img_seguridad_base64 = buffer_a_base64(buffer_seguridad)
img_proyeccion_base64 = buffer_a_base64(buffer_proyeccion)
img_localidad_base64 = buffer_a_base64(buffer_localidad)

html_ficha = ficha_estilizada.to_html()

from IPython.core.display import HTML

HTML("""
<style>
body {
    font-family: Arial, sans-serif;
    margin: 20px;
    background-color: #f9f9f9;
}
h1 {
    color: #2c3e50;
    text-align: center;
}
.container {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.text {
    text-align: justify;
    margin: 20px 0;
    max-width: 900px;
    font-size: 16px;
    color: #333;
}
.images {
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
    max-width: 900px;
    margin: 0 auto;

}
.image {
    flex: 1;
    max-width: 600px;
}
.image img {
    width: 100%;
    height: auto;
    border: 1px solid #ccc;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
}
</style>
""")

html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{titulo}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f9f9f9;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
        }}
        .container {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .text {{
            text-align: justify;
            margin: 20px 0;
            max-width: 900px;
            font-size: 16px;
            color: #333;
        }}
        .images {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            max-width: 900px;
            margin: 0 auto;
        }}
        .image {{
            flex: 1;
            max-width: 600px;
        }}
        .image img {{
            width: 100%;
            height: auto;
            border: 1px solid #ccc;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{titulo}</h1>

        <div class="text">{html_ficha}</div>
        <div class="text">{texto0}</div>

        <div class="images">
            <div class="image"><img src="data:image/png;base64,{img_localidad_base64}" alt="Mapa Localidad"></div>
        </div>

        <div class="text">{texto1}</div>
        <div class="images">
            <div class="image"><img src="data:image/png;base64,{img_manzanas_base64}" alt="Mapa Manzanas"></div>
        </div>

        <div class="text">{texto2}</div>
        <div class="images">
            <div class="image"><img src="data:image/png;base64,{img_colegios_base64}" alt="Mapa Colegios"></div>
            <div class="image"><img src="data:image/png;base64,{img_transporte_base64}" alt="Mapa Transporte"></div>
        </div>

        <div class="text">{texto3}</div>
        <div class="images">
            <div class="image"><img src="data:image/png;base64,{img_distribucion_base64}" alt="Distribución"></div>
            <div class="image"><img src="data:image/png;base64,{img_mapapot_base64}" alt="Mapa Potencial"></div>
        </div>

        <div class="text">{texto4}</div>
        <div class="images">
            <div class="image"><img src="data:image/png;base64,{img_valorm2_base64}" alt="Valor m2"></div>
        </div>

        <div class="text">{texto5}</div>
        <div class="images">
            <div class="image"><img src="data:image/png;base64,{img_seguridad_base64}" alt="Seguridad"></div>
        </div>

        <div class="text">{texto6}</div>
        <div class="images">
            <div class="image"><img src="data:image/png;base64,{img_proyeccion_base64}" alt="Proyección"></div>
        </div>
    </div>
</body>
</html>
"""

with open("informe_final.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# SERGIO ANDRES FUENTES