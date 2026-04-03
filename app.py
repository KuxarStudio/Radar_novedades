import streamlit as st
import sqlite3
import pandas as pd
import json
import re
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="RADAR | Fashion Hub", layout="wide")

# --- CSS NUCLEAR: PESTAÑAS INMOVILIZADAS AL 100% (MÉTODO BRUTO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:wght@700&family=Inter:wght@300;400;600&display=swap');
    
    /* Tipografía y Colores */
    h1, h2, .section-title { font-family: 'Bodoni Moda', serif !important; text-transform: uppercase; color: #111; }
    body, p, span, div, .stSlider, .stMultiSelect { font-family: 'Inter', sans-serif !important; color: #111; }

    /* Fondo Crema Zara */
    [data-testid="stAppViewContainer"] { background-color: #FAF5EF; }
    [data-testid="stSidebar"] { background-color: #F5EFE6; border-right: 1px solid #EAE0D5; }
    [data-testid="stHeader"] { background-color: rgba(250, 245, 239, 0.95); backdrop-filter: blur(10px); z-index: 100000; }

    /* --- PARCHE PARA INMOVILIZAR CABECERA (VUELTA A LO SEGURO) --- */
    .stTabs [data-baseweb="tab-list"] {
        position: fixed !important;
        top: 2.875rem; /* Ajuste para debajo de la barra de Streamlit */
        z-index: 1000;
        width: 100%;
        background-color: #FAF5EF;
        padding: 10px 0 0 0;
        border-bottom: 1px solid #D9CFC1;
    }

    /* Margen para que el contenido no quede oculto bajo las pestañas fijas */
    [data-testid="stVerticalBlock"] > div:nth-child(2) {
        margin-top: 60px;
    }

    /* Pestañas Estilizadas */
    .stTabs [data-baseweb="tab"] { 
        height: 50px; font-weight: 600; font-size: 0.85rem; 
        color: #777; text-transform: uppercase; letter-spacing: 1px; border: none !important;
    }
    .stTabs [aria-selected="true"] { color: #000 !important; border-bottom: 2px solid #000 !important; }

    /* Grid de Productos */
    .img-container {
        height: 480px; display: flex; align-items: center; justify-content: center;
        overflow: hidden; background-color: #FFFFFF; margin-bottom: 15px;
        border: 1px solid #EAE0D5; transition: 0.3s;
    }
    .img-container:hover { border-color: #000; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .img-container img { max-height: 95%; width: auto; object-fit: contain; }

    .brand-label { text-transform: uppercase; font-size: 0.6rem; color: #888; letter-spacing: 1.5px; margin-bottom: 2px; }
    .product-title { height: 45px; overflow: hidden; font-weight: 400; font-size: 0.95rem; line-height: 1.3; margin-bottom: 5px; }
    .price-label { font-weight: 600; font-size: 1rem; margin-bottom: 5px; color: #000; }
    .size-label { font-size: 0.7rem; color: #888; margin-bottom: 15px; }

    .badge-new {
        background-color: #000; color: #fff; padding: 2px 8px; font-size: 0.6rem;
        font-weight: 600; letter-spacing: 2px; display: inline-block; margin-bottom: 8px;
    }

    .stButton>button {
        border: 1px solid #000 !important; background: transparent !important;
        color: #000 !important; border-radius: 0px !important;
        font-size: 0.65rem; letter-spacing: 2px; width: 100%; height: 40px; text-transform: uppercase;
    }
    .stButton>button:hover { background: #000 !important; color: #fff !important; }
    
    .block-container { padding-top: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIONES CORE
@st.cache_data
def cargar_config_tallas():
    try:
        with open('tallas_config.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"mapeo": {}, "blacklist": []}

CONFIG = cargar_config_tallas()

def limpiar_talla_pro(talla_raw):
    if not talla_raw: return None
    t = str(talla_raw).upper().strip()
    if any(m in t for m in ["€", "$", "â‚¬"]): return None
    if any(p == t or f" {p} " in f" {t} " for p in CONFIG['blacklist']): return None
    match_num = re.search(r'(\d+[\s\./]\d/\d|\d+\.?\d?)', t)
    prefijo = "EU" if "EU" in t else ("UK" if "UK" in t else ("US" if "US" in t else ("W" if "W" in t and len(t)<=5 else "")))
    if prefijo and match_num:
        val = match_num.group(1).replace('.0', '')
        if prefijo == "W" and float(val) > 60: return None
        return f"{prefijo} {val}"
    if '/' in t: t = t.split('/')[-1].strip()
    if t in CONFIG['mapeo']: return CONFIG['mapeo'][t]
    try:
        t_c = t.replace('.0', '').replace('Y', '').strip()
        if '-' in t_c and any(c.isdigit() for c in t_c): return f"{t_c}Y"
        if t_c.replace('.','',1).isdigit():
            num = float(t_c)
            if 1 <= num <= 15: return f"{int(num) if num.is_integer() else num}Y"
            elif 16 <= num <= 60: return str(int(num) if num.is_integer() else num)
    except: pass
    return t if len(t) <= 4 and t != "" else None

def clasificar_producto_pro(row):
    texto = (str(row['product_name']) + " " + str(row['category'])).lower()
    
    # 1. GÉNERO (Mantenemos la búsqueda estricta para no confundir men/women)
    tokens = set(re.findall(r'\b\w+\b', texto))
    
    p_niños = {'kids', 'niños', 'youth', 'child', 'boy', 'girl', 'toddler', 'infant', 'baby', 'bebe', 'junior'}
    p_mujer = {'sujetador', 'bra', 'bralette', 'leggings', 'dress', 'vestido', 'skirt', 'falda', 'blouse', 'blusa', 'heels', 'tacones', 'lingerie', 'woman', 'women'}
    p_hombre = {'suit', 'traje', 'tie', 'corbata', 'briefs', 'boxers', 'barba', 'man', 'men'}
    
    # 2. TIPOS (Búsqueda FLEXIBLE por fragmentos de texto)
    zapas_keys = ['shoe', 'sneaker', 'zapatil', 'footwear', 'samba', 'gazelle', 'dunk', 'jordan', 'vans', 'sk8', 'bota', 'boot', 'yeezy', 'campus', 'converse', 'asics', 'salomon', 'trainer', 'kicks', 'clog', 'slide', 'sandal', 'mule', 'new balance', 'puma']
    acc_keys = ['bag', 'sock', 'hat', 'cap', 'accessory', 'jewelry', 'wallet', 'pin', 'gafa', 'sunglass', 'mochila', 'backpack', 'belt', 'cinturon', 'scarf', 'bufanda', 'gorra', 'beanie']

    # --- LÓGICA TIPO (¡Aquí estaba el error!) ---
    if any(x in texto for x in zapas_keys): 
        tipo = "SNEAKERS"
    elif any(x in texto for x in acc_keys): 
        tipo = "ACCESORIOS"
    else: 
        tipo = "ROPA"

    # --- LÓGICA GÉNERO ---
    if tokens & p_niños or re.search(r'\d+y\b|\d+t\b', texto): genero = "NIÑOS"
    elif tokens & p_mujer: genero = "MUJER"
    elif tokens & p_hombre: genero = "HOMBRE"
    elif re.search(r'\bmen\b|\bhombre\b|\bhim\b', texto): genero = "HOMBRE"
    elif re.search(r'\bwomen\b|\bmujer\b|\bher\b', texto): genero = "MUJER"
    else: genero = "GENERAL"
        
    return genero, tipo

@st.cache_data
def cargar_datos_pro():
    conn = sqlite3.connect('radar_data.db')
    df = pd.read_sql_query("SELECT * FROM products WHERE product_name NOT LIKE '%Gift Card%'", conn)
    conn.close()
    df['Brand'] = df['brand_id'].apply(lambda x: str(x).split('_')[0].title())
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df[['Genero_Auto', 'Tipo_Auto']] = df.apply(lambda r: pd.Series(clasificar_producto_pro(r)), axis=1)
    return df

df_raw = cargar_datos_pro()

# --- INTERFAZ ---
st.markdown("<h1 style='text-align: center; font-size: 4rem; margin-top: 1rem; letter-spacing: -3px;'>RADAR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; letter-spacing: 5px; font-size: 0.6rem; color: #777; margin-bottom: 2rem;'>SNEAKERS & STREETWEAR INTELLIGENCE</p>", unsafe_allow_html=True)

# PESTAÑAS
tab_nov, tab_sneakers, tab_mujer, tab_hombre, tab_ninos, tab_acc = st.tabs([
    "🆕 NEW", "👟 SNEAKERS", "👠 MUJER", "🎩 HOMBRE", "🧒 NIÑOS", "👜 ACCESORIOS"
])

# --- SIDEBAR & FILTROS DINÁMICOS ---
with st.sidebar:
    st.markdown("### 🔍 SEARCH")
    search_term = st.text_input("PRODUCTO...", placeholder="Ej: Samba...").lower()
    st.write("---")
    
    st.markdown("### 🎯 FILTERS")
    solo_novedades = st.toggle("🆕 ÚLTIMAS 24H", value=False)
    solo_stock = st.toggle("✅ SOLO EN STOCK", value=True)
    
    # 1. Creamos un DF temporal solo con los filtros básicos
    df_temp = df_raw.copy()
    if search_term: df_temp = df_temp[df_temp['product_name'].str.lower().str.contains(search_term)]
    if solo_novedades: df_temp = df_temp[df_temp['created_at'] >= (datetime.now() - timedelta(hours=24))]
    if solo_stock: df_temp = df_temp[df_temp['is_available'] == 1]
    
    # 2. Selector de Marcas Dinámico
    marcas_sel = st.multiselect("MARCAS", sorted(df_temp['Brand'].unique()))
    if marcas_sel: df_temp = df_temp[df_temp['Brand'].isin(marcas_sel)]
    
    # 3. Rango de Precio Dinámico
    if not df_temp.empty:
        min_p, max_p = float(df_temp['price'].min()), float(df_temp['price'].max())
        rango_p = st.slider("PRECIO (€)", min_p, max_p, (min_p, max_p)) if min_p != max_p else (min_p, max_p)
    else:
        rango_p = (0.0, 1000.0)

    # 4. Tallas Dinámicas
    tallas_dinamicas = set()
    for s_list in df_temp['sizes'].dropna():
        for s in str(s_list).split(','):
            l = limpiar_talla_pro(s)
            if l: tallas_dinamicas.add(l)
    tallas_sel = st.multiselect("TALLAS", sorted(list(tallas_dinamicas)))

# --- FUNCIÓN FINAL DE APLICACIÓN DE FILTROS ---
def filtrar_df_final(df_input, tipo_target=None, genero_target=None, solo_nov=False):
    dff = df_input.copy()
    
    # Filtros de Tab
    if genero_target:
        dff = dff[dff['Genero_Auto'].isin([genero_target, "GENERAL"])]
        dff = dff[dff['Tipo_Auto'] == "ROPA"]
    if tipo_target:
        dff = dff[dff['Tipo_Auto'] == tipo_target]
    if solo_nov:
        dff = dff[dff['created_at'] >= (datetime.now() - timedelta(hours=24))]

    # Filtros de Sidebar
    if search_term: dff = dff[dff['product_name'].str.lower().str.contains(search_term)]
    if solo_novedades: dff = dff[dff['created_at'] >= (datetime.now() - timedelta(hours=24))]
    if solo_stock: dff = dff[dff['is_available'] == 1]
    if marcas_sel: dff = dff[dff['Brand'].isin(marcas_sel)]
    dff = dff[dff['price'].between(rango_p[0], rango_p[1])]
    if tallas_sel:
        dff = dff[dff['sizes'].apply(lambda x: any(limpiar_talla_pro(s) in tallas_sel for s in str(x).split(',')))]
        
    return dff

def render_editorial_grid(df_grid):
    if df_grid.empty:
        st.info("NO SE HAN ENCONTRADO PIEZAS CON ESTOS FILTROS.")
        return
    cols = st.columns(3)
    hace_24h = datetime.now() - timedelta(hours=24)
    for i, row in df_grid.reset_index(drop=True).iterrows():
        with cols[i % 3]:
            img = row['image_url'] if row['image_url'] else "https://via.placeholder.com/500"
            st.markdown(f"<div class='img-container'><img src='{img}'></div>", unsafe_allow_html=True)
            if row['created_at'] >= hace_24h:
                st.markdown("<span class='badge-new'>NEW ARRIVAL</span>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            
            st.markdown(f"<div class='brand-label'>{row['Brand']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='product-title'>{row['product_name']}</div>", unsafe_allow_html=True)
            p_display = int(row['price']) if row['price'] % 1 == 0 else row['price']
            st.markdown(f"<div class='price-label'>{p_display} EUR</div>", unsafe_allow_html=True)
            
            # Recuperamos visualización de tallas limpia
            t_cards = [limpiar_talla_pro(s) for s in str(row['sizes']).split(',')]
            t_limpias = ", ".join(list(dict.fromkeys([x for x in t_cards if x])))
            st.markdown(f"<div class='size-label'>Tallas: {t_limpias if t_limpias else 'OS'}</div>", unsafe_allow_html=True)
            
            st.link_button("EXPLORAR", row['product_url'])
            st.write("")

# --- RENDERIZADO POR PESTAÑAS ---
with tab_nov:
    st.markdown("<h2 class='section-title'>THE NEW</h2>", unsafe_allow_html=True)
    render_editorial_grid(filtrar_df_final(df_raw, solo_nov=True))

with tab_sneakers:
    st.markdown("<h2 class='section-title'>SNEAKERS</h2>", unsafe_allow_html=True)
    render_editorial_grid(filtrar_df_final(df_raw, tipo_target="SNEAKERS"))

with tab_mujer:
    st.markdown("<h2 class='section-title'>WOMEN COLLECTION</h2>", unsafe_allow_html=True)
    render_editorial_grid(filtrar_df_final(df_raw, genero_target="MUJER"))

with tab_hombre:
    st.markdown("<h2 class='section-title'>MEN COLLECTION</h2>", unsafe_allow_html=True)
    render_editorial_grid(filtrar_df_final(df_raw, genero_target="HOMBRE"))

with tab_ninos:
    st.markdown("<h2 class='section-title'>KIDS</h2>", unsafe_allow_html=True)
    render_editorial_grid(filtrar_df_final(df_raw, genero_target="NIÑOS"))

with tab_acc:
    st.markdown("<h2 class='section-title'>ACCESSORIES</h2>", unsafe_allow_html=True)
    render_editorial_grid(filtrar_df_final(df_raw, tipo_target="ACCESORIOS"))