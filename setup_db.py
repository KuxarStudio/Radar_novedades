import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def crear_base_datos():
    conn = sqlite3.connect('radar_data.db')
    cursor = conn.cursor()
    
    # Hemos añadido: category, sizes, tags y is_available
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
            is_available BOOLEAN DEFAULT 1,
            is_new BOOLEAN DEFAULT 1,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("🏗️ Base de datos V3 construida. Lista para Tallas, Categorías y Stock.")

if __name__ == "__main__":
    crear_base_datos()