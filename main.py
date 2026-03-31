import sqlite3
import logging
import json
import time

from dynamic_scraper import scrape_storefront
from shopify_backdoor import scrape_shopify_api

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_brands(filepath='brands.json'):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_new_products(brand_id, productos):
    conn = sqlite3.connect('radar_data.db')
    cursor = conn.cursor()
    nuevos_encontrados = 0
    
    # Ahora 'productos' es una lista de diccionarios, no solo URLs
    for prod in productos:
        try:
            # Insertamos todos los datos enriquecidos
            cursor.execute('''
                INSERT OR IGNORE INTO products (brand_id, product_name, product_url, price, image_url, is_new)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (brand_id, prod['name'], prod['url'], prod['price'], prod['image_url']))
            
            if cursor.rowcount > 0:
                nuevos_encontrados += 1
                # Imprimimos el nombre y el precio para verlo en directo
                logging.info(f"✨ ¡NUEVO DROP!: {prod['name']} | Precio: {prod['price']}€")
        except sqlite3.Error as e:
            logging.error(f"Error guardando {prod['name']}: {e}")
            
    conn.commit()
    conn.close()
    return nuevos_encontrados

if __name__ == "__main__":
    logging.info("Iniciando Radar Híbrido de Novedades (V2 Enriquecida)...")
    marcas_objetivo = load_brands()
    
    total_ropa = 0
    total_nuevos = 0
    
    for marca in marcas_objetivo:
        print("\n" + "="*50)
        logging.info(f"🚀 OBJETIVO: {marca['name']} | ESTRATEGIA: {marca.get('strategy', 'visual').upper()}")
        print("="*50)
        
        productos_obtenidos = []
        estrategia = marca.get('strategy', 'visual')
        
        if estrategia == 'api_shopify':
            productos_obtenidos = scrape_shopify_api(marca['url'])
        else:
            productos_obtenidos = scrape_storefront(marca['url'])
        
        if productos_obtenidos:
            nuevos = save_new_products(marca['id'], productos_obtenidos)
            total_ropa += len(productos_obtenidos)
            total_nuevos += nuevos
            logging.info(f"Reporte {marca['name']}: {len(productos_obtenidos)} analizados | {nuevos} nuevos drops.")
        else:
            logging.warning(f"Fallo al obtener datos de {marca['name']}.")
            
        logging.info("Descansando 5 segundos...")
        time.sleep(5)
        
    print("\n" + "🌟"*25)
    print("📡 REPORTE GLOBAL RADAR NOVEDADES (SISTEMA ENRIQUECIDO)")
    print(f"Marcas escaneadas: {len(marcas_objetivo)}")
    print(f"Total prendas analizadas: {total_ropa}")
    print(f"Total drops nuevos hoy: {total_nuevos}")
    print("🌟"*25 + "\n")