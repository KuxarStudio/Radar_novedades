import sqlite3
import webbrowser
import os

def crear_reporte_html():
    # 1. Conectamos a la base de datos y sacamos todo
    conn = sqlite3.connect('radar_data.db')
    cursor = conn.cursor()
    
    # Sacamos los productos (primero los más recientes)
    cursor.execute('SELECT product_name, product_url, price, image_url, brand_id FROM products ORDER BY id DESC')
    productos = cursor.fetchall()
    conn.close()

    # 2. Creamos el archivo HTML
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Radar Novedades - MVP</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; padding: 20px; }
            h1 { text-align: center; color: #111827; margin-bottom: 40px; font-size: 2.5rem; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }
            .card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: transform 0.2s; display: flex; flex-direction: column; }
            .card:hover { transform: translateY(-5px); }
            .image-container { height: 300px; overflow: hidden; background-color: #e5e7eb; display: flex; align-items: center; justify-content: center;}
            .image-container img { width: 100%; height: 100%; object-fit: cover; }
            .no-image { color: #6b7280; font-size: 0.9rem; }
            .content { padding: 15px; display: flex; flex-direction: column; flex-grow: 1; }
            .brand { font-size: 0.75rem; text-transform: uppercase; color: #6366f1; font-weight: bold; letter-spacing: 0.05em; margin-bottom: 5px; }
            .title { font-size: 1rem; color: #1f2937; font-weight: 600; margin: 0 0 10px 0; }
            .price { font-size: 1.25rem; color: #111827; font-weight: bold; margin-top: auto; }
            .btn { display: block; background-color: #111827; color: white; text-align: center; padding: 10px; border-radius: 6px; text-decoration: none; margin-top: 15px; font-weight: 500; }
            .btn:hover { background-color: #374151; }
        </style>
    </head>
    <body>
        <h1>🎯 Radar Novedades</h1>
        <div class="grid">
    """

    # 3. Inyectamos la ropa en el HTML
    for prod in productos:
        nombre, url, precio, imagen, marca = prod
        
        # Formateamos el precio y la imagen
        precio_texto = f"{precio:.2f} €" if precio > 0 else "Consultar en web"
        imagen_html = f'<img src="{imagen}" alt="{nombre}">' if imagen else '<span class="no-image">📸 Sin imagen previa</span>'
        
        # Limpiamos el ID de la marca (ej: eme_studios_01 -> Eme Studios)
        marca_limpia = marca.split('_')[0].replace('-', ' ').title()

        html_content += f"""
            <div class="card">
                <div class="image-container">
                    {imagen_html}
                </div>
                <div class="content">
                    <span class="brand">{marca_limpia}</span>
                    <h2 class="title">{nombre}</h2>
                    <span class="price">{precio_texto}</span>
                    <a href="{url}" target="_blank" class="btn">Ver en Tienda</a>
                </div>
            </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """

    # Guardamos el archivo y lo abrimos automáticamente
    ruta_archivo = os.path.abspath('reporte_diario.html')
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ ¡Reporte generado con éxito! Abriendo en el navegador...")
    webbrowser.open('file://' + ruta_archivo)

if __name__ == "__main__":
    crear_reporte_html()