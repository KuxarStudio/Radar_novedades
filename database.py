import sqlite3
import logging

# Configuración básica para que la consola nos dé mensajes claros
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def init_db():
    """
    Inicializa la base de datos SQLite y crea la tabla principal 'products'
    siguiendo la Estructura de Datos Maestra de Radar Novedades.
    """
    # Se conecta a la base de datos (y crea el archivo si no existe)
    conn = sqlite3.connect('radar_data.db')
    cursor = conn.cursor()

    # Diseño de la tabla principal
    # Usamos UNIQUE en product_url para evitar guardar el mismo producto dos veces
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price REAL,
            currency TEXT,
            product_url TEXT UNIQUE,
            image_url TEXT,
            category TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_new BOOLEAN DEFAULT 1
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("Base de datos SQLite inicializada correctamente. Tabla 'products' lista.")

if __name__ == "__main__":
    # Esto ejecuta la función cuando corremos el script directamente
    init_db()