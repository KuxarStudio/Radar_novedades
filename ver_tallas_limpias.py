import sqlite3
import json
import re

# 1. Cargar configuración
try:
    with open('tallas_config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    CONFIG = {"mapeo": {}, "blacklist": []}

def limpiar_talla_pro(talla_raw):
    if not talla_raw: return None
    t = str(talla_raw).upper().strip()
    
    # 1. ESCUDO ANTI-DINERO
    if any(m in t for m in ["€", "$", "â‚¬"]): return None

    # 2. BLACKLIST MEJORADA
    # Ahora comprobamos si alguna palabra prohibida aparece en CUALQUIER parte del texto
    # antes de hacer nada más (ej: filtra "BROWN / M" o "BROWN" directamente)
    if any(palabra in t for palabra in CONFIG['blacklist']):
        # Solo indultamos si es calzado explícito (EU/UK/US)
        if not any(x in t for x in ["EU", "UK", "US"]):
            return None

    # 3. DETECCIÓN DE CALZADO Y CINTURA
    match_num = re.search(r'(\d+[\s\./]\d/\d|\d+\.?\d?)', t)
    
    prefijo = ""
    if "EU" in t: prefijo = "EU"
    elif "UK" in t: prefijo = "UK"
    elif "US" in t: prefijo = "US"
    elif "W" in t and any(char.isdigit() for char in t): 
        # Filtro de longitud para evitar que "BROWN" entre aquí
        if len(t) <= 5: prefijo = "W"

    if prefijo and match_num:
        val = match_num.group(1).replace('.0', '')
        # El escudo de los cordones 120cm
        try:
            if prefijo == "W" and float(val) > 60: return None 
        except: pass
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

    # 7. FILTRO FINAL DE LONGITUD
    if len(t) > 4: return None 
    
    return t if t != "" else None

# 3. EJECUCIÓN
conn = sqlite3.connect('radar_data.db')
cursor = conn.cursor()
cursor.execute('SELECT sizes FROM products')
filas = cursor.fetchall()
conn.close()

limpias = set()
for f in filas:
    if f[0]:
        for s in f[0].split(','):
            res = limpiar_talla_pro(s)
            if res: limpias.add(res)

print("\n" + "=" * 40)
print("💎 RESULTADO DEL FILTRADO PRO V4.2 (Sincronizado)")
print("=" * 40)
listado = sorted(list(limpias))
for talla in listado:
    print(f"-> {talla}")

print("\n" + "=" * 40)
print(f"Total tallas únicas: {len(listado)}")