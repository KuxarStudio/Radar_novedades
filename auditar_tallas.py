import sqlite3
import pandas as pd

def auditar_tallas():
    conn = sqlite3.connect('radar_data.db')
    # Traemos todas las tallas crudas
    cursor = conn.cursor()
    cursor.execute('SELECT sizes FROM products')
    filas = cursor.fetchall()
    conn.close()

    tallas_crudas = set()
    for f in filas:
        if f[0]:
            # Separamos por comas y limpiamos espacios
            partes = [p.strip() for p in f[0].split(',')]
            for p in partes:
                if p: tallas_crudas.add(p)

    # Lo guardamos en un CSV para que lo abras en Excel
    df = pd.DataFrame(sorted(list(tallas_crudas)), columns=['Talla_Cruda'])
    df.to_csv('auditoria_tallas.csv', index=False, encoding='utf-8')
    print(f"✅ Auditoría completada. Se han encontrado {len(df)} variantes únicas.")
    print("Abre 'auditoria_tallas.csv' para ver el listado completo del ruido.")

if __name__ == "__main__":
    auditar_tallas()