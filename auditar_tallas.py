import sqlite3
import pandas as pd
import json
import re

# 1. Cargamos tu configuración actual
def cargar_config_tallas():
    try:
        with open('tallas_config.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"mapeo": {}, "blacklist": []}

CONFIG = cargar_config_tallas()

# 2. Tu función limpiadora adaptada para auditar
def limpiar_talla_pro(talla_raw):
    if not talla_raw: return None
    t = str(talla_raw).upper().strip()
    
    # Si detecta símbolos de dinero, es basura
    if any(m in t for m in ["€", "$", "â‚¬"]): return "BASURA_PRECIO"
    
    # Si está en la blacklist
    if any(p == t or f" {p} " in f" {t} " for p in CONFIG['blacklist']): return "BLACKLISTED"
    
    # Lógica de limpieza normal
    match_num = re.search(r'(\d+[\s\./]\d/\d|\d+\.?\d?)', t)
    prefijo = "EU" if "EU" in t else ("UK" if "UK" in t else ("US" if "US" in t else ("W" if "W" in t and len(t)<=5 else "")))
    if prefijo and match_num:
        val = match_num.group(1).replace('.0', '')
        if prefijo == "W" and float(val) > 60: return "BASURA"
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
    
    # Devolvemos lo que no se ha podido limpiar
    return t if len(t) <= 10 and t != "" else t 

# 3. La función fusionada
def auditar_tallas():
    print("🔍 Analizando base de datos y cruzando con el motor de limpieza...")
    conn = sqlite3.connect('radar_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT sizes FROM products WHERE sizes IS NOT NULL')
    filas = cursor.fetchall()
    conn.close()

    resultados = []
    tallas_procesadas = set() # Para no repetir en el excel

    for f in filas:
        partes = [p.strip() for p in f[0].split(',')]
        for cruda in partes:
            if cruda and cruda not in tallas_procesadas:
                tallas_procesadas.add(cruda)
                
                limpia = limpiar_talla_pro(cruda)
                
                # Clasificamos el estado
                if limpia in ["BLACKLISTED", "BASURA_PRECIO", "BASURA"]:
                    estado = "🛑 Bloqueada"
                elif limpia and len(limpia) > 5 and not any(x in limpia for x in ["EU", "US", "UK", "OS"]):
                    estado = "⚠️ Sospechosa"
                else:
                    estado = "✅ OK"
                    
                resultados.append({
                    "Talla_Cruda": cruda,
                    "Talla_Limpia": limpia,
                    "Estado": estado
                })

    # Guardamos en CSV ordenado por estado para que las sospechosas salgan juntas
    df = pd.DataFrame(resultados)
    df = df.sort_values(by=["Estado", "Talla_Cruda"], ascending=[False, True])
    df.to_csv('auditoria_tallas.csv', index=False, encoding='utf-8')
    
    sospechosas_count = len(df[df['Estado'] == '⚠️ Sospechosa'])
    
    print(f"✅ Auditoría completada. Se han procesado {len(df)} variantes únicas.")
    print(f"🚨 Se han detectado {sospechosas_count} tallas SOSPECHOSAS.")
    print("📂 Abre 'auditoria_tallas.csv' en Excel para revisar el listado.")

if __name__ == "__main__":
    auditar_tallas()