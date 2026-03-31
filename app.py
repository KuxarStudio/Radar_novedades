import streamlit as st
import sqlite3
import pandas as pd
import json
import re

# 1. Configuración de la página
st.set_page_config(page_title="Radar Novedades Pro", layout="wide")

# 2. Cargar configuración externa (El archivo "Padre")
def cargar_config_tallas():
    try:
        with open('tallas_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Valores por defecto si el archivo no existe aún
        return {"mapeo": {}, "blacklist": []}

CONFIG = cargar_config_tallas()

# 3. Función de Limpieza "Francotirador" (Basada en Auditoría)
def limpiar_talla_pro(talla_raw):
    if not talla_raw: return None
    t = str(talla_raw).upper().strip()
    
    # 1. ESCUDO ANTI-DINERO (Prioridad máxima)
    if any(m in t for m in ["€", "$", "â‚¬"]): return None

    # 2. BLACKLIST DE COLORES/RUIDO (Antes de los prefijos)
    # Comprobamos palabras completas para evitar que "BROWN" pase por tener una "W"
    if any(palabra == t or f" {palabra} " in f" {t} " for palabra in CONFIG['blacklist']):
        return None

    # 3. DETECCIÓN DE CALZADO Y CINTURA (CON PREFIJOS REALES)
    # Buscamos números con decimales o fracciones
    match_num = re.search(r'(\d+[\s\./]\d/\d|\d+\.?\d?)', t)
    
    # Solo ponemos prefijo si REALMENTE existe en el texto original
    prefijo = ""
    if "EU" in t: prefijo = "EU"
    elif "UK" in t: prefijo = "UK"
    elif "US" in t: prefijo = "US"
    elif "W" in t and any(char.isdigit() for char in t): 
        # Solo aceptamos W si hay números y NO es una palabra larga (como BROWN)
        if len(t) <= 5: prefijo = "W"

    if prefijo and match_num:
        val = match_num.group(1).replace('.0', '')
        # Evitar el error de los cordones 120cm
        if prefijo == "W" and float(val) > 60: return None 
        return f"{prefijo} {val}"

    # 4. LIMPIEZA DE SEPARADORES
    if '/' in t: t = t.split('/')[-1].strip()
    if '|' in t: t = t.split('|')[-1].strip()

    # 5. MAPEO ESTÁNDAR
    if t in CONFIG['mapeo']: return CONFIG['mapeo'][t]

    # 6. LÓGICA NUMÉRICA (KIDS vs ADULTOS)
    try:
        t_clean = t.replace('.0', '').replace('Y', '').strip()
        if '-' in t_clean and any(char.isdigit() for char in t_clean):
            return f"{t_clean}Y"
            
        if t_clean.replace('.','',1).isdigit():
            num = float(t_clean)
            if 1 <= num <= 15: return f"{int(num) if num.is_integer() else num}Y"
            elif 16 <= num <= 60: return str(int(num) if num.is_integer() else num)
            else: return None
    except ValueError:
        pass

    # 7. FILTRO FINAL DE LONGITUD (S, M, L, XL, XXS...)
    if len(t) > 4: return None # Las tallas de texto son cortas
    
    return t if t != "" else None

# 4. Carga de datos
@st.cache_data
def cargar_datos():
    conn = sqlite3.connect('radar_data.db')
    # Excluimos Gift Cards por nombre para limpiar la base
    df = pd.read_sql_query("SELECT * FROM products WHERE product_name NOT LIKE '%Gift Card%' ORDER BY id DESC", conn)
    conn.close()
    df['Brand'] = df['brand_id'].apply(lambda x: str(x).split('_')[0].title())
    return df

df = cargar_datos()

# --- SIDEBAR (Filtros) ---
st.sidebar.title("🎯 Filtros Élite")

# Recuperamos el buscador
search_term = st.sidebar.text_input("¿Qué buscas? (ej: hoodie, pants, kith)").lower()

st.sidebar.write("---")

# Filtro de Precio Mejorado (Input + Slider)
st.sidebar.write("Rango de Precio (€)")
max_p_db = float(df['price'].max())
p_min_in = st.sidebar.number_input("Mínimo", value=0.0, step=10.0)
p_max_in = st.sidebar.number_input("Máximo", value=max_p_db, step=10.0)
rango_p = st.sidebar.slider("Ajuste visual", 0.0, max_p_db, (p_min_in, p_max_in), label_visibility="collapsed")

# Procesamiento de Tallas para el Filtro
tallas_para_filtro = []
for s_list in df['sizes'].dropna():
    for s in s_list.split(','):
        limpia = limpiar_talla_pro(s)
        if limpia: tallas_para_filtro.append(limpia)

tallas_unicas = sorted(list(set(tallas_para_filtro)))
tallas_sel = st.sidebar.multiselect("Tallas Disponibles", tallas_unicas)

marcas_sel = st.sidebar.multiselect("Marcas", sorted(df['Brand'].unique()), default=df['Brand'].unique())
solo_stock = st.sidebar.toggle("Mostrar solo con Stock", value=True)

# --- LÓGICA DE FILTRADO ---
df_f = df[
    (df['Brand'].isin(marcas_sel)) & 
    (df['price'] >= rango_p[0]) & 
    (df['price'] <= rango_p[1])
]

if solo_stock: 
    df_f = df_f[df_f['is_available'] == 1]

if search_term:
    df_f = df_f[df_f['product_name'].str.lower().str.contains(search_term)]

if tallas_sel:
    df_f = df_f[df_f['sizes'].apply(lambda x: any(limpiar_talla_pro(s) in tallas_sel for s in str(x).split(',')))]

# --- RENDERIZADO ---
st.title("🎯 Radar Novedades")
st.write(f"Prendas encontradas: {len(df_f)}")

cols = st.columns(4)
for i, row in df_f.reset_index(drop=True).iterrows():
    with cols[i % 4]:
        if row['image_url']: 
            st.image(row['image_url'], use_container_width=True)
        
        st.caption(f"{row['Brand']} | {row['category']}")
        st.markdown(f"**{row['product_name']}**")
        st.subheader(f"{row['price']} €")
        
        # Mostrar tallas limpias en la tarjeta
        t_cards = [limpiar_talla_pro(s) for s in str(row['sizes']).split(',')]
        t_cards = ", ".join(list(dict.fromkeys([x for x in t_cards if x])))
        
        if row['is_available']:
            st.caption(f"Tallas: {t_cards}" if t_cards else "Talla Única")
        else:
            st.markdown("<span style='color:red; font-size:0.8rem;'>Agotado</span>", unsafe_allow_html=True)
            
        st.markdown(f"[Ver en Tienda]({row['product_url']})")
        st.write("---")