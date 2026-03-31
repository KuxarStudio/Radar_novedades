import sqlite3
import logging
import json
import time
import os

from dynamic_scraper import scrape_storefront
from shopify_backdoor import scrape_shopify_api

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def init_db():
    """Asegura que la base de datos y la tabla existan antes de empezar."""
    conn = sqlite3.connect('radar_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id TEXT,
            product_name TEXT,
            product_url TEXT UNIQUE,
            price REAL,
            image_url TEXT,
            category TEXT,
            sizes TEXT,
            tags TEXT,
            is_available BOOLEAN,
            is_new BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def load_brands(filepath='brands.json'):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("Archivo brands.json no encontrado.")
        return []

def save_new_products(brand_id, productos):
    conn = sqlite3.connect('radar_data.db')
    cursor = conn.cursor()
    nuevos_encontrados = 0
    
    for prod in productos:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO products (
                    brand_id, product_name, product_url, price, image_url, 
                    category, sizes, tags, is_available, is_new
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                brand_id, 
                prod['name'], 
                prod['url'], 
                prod['price'], 
                prod.get('image_url', ''),
                prod.get('category', ''),
                prod.get('sizes', ''),
                prod.get('tags', ''),
                prod.get('is_available', True)
            ))
            
            if cursor.rowcount > 0:
                nuevos_encontrados += 1
                logging.info(f"✨ NUEVO DROP: {prod['name']} ({prod['price']}€)")
        except sqlite3.Error as e:
            logging.error(f"Error guardando {prod['name']}: {e}")
            
    conn.commit()
    conn.close()
    return nuevos_encontrados

if __name__ == "__main__":
    logging.info("🚀 Iniciando Radar en Piloto Automático...")
    
    # 1. Preparar DB
    init_db()
    
    # 2. Cargar marcas
    marcas_objetivo = load_brands()
    
    total_ropa = 0
    total_nuevos = 0
    
    for marca in marcas_objetivo:
        print("-" * 30)
        logging.info(f"Escaneando: {marca['name']}")
        
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
            logging.info(f"Hecho: {len(productos_obtenidos)} prendas revisadas.")
        else:
            logging.warning(f"Sin datos para {marca['name']}.")
            
        time.sleep(5)
        
    print("\n" + "🌟"*15)
    logging.info(f"FIN DEL ESCANEO: {total_nuevos} drops nuevos detectados.")
    print("🌟"*15)