import requests
import logging
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_shopify_api(domain):
    url = f"{domain}/products.json?limit=250"
    logging.info(f"Desplegando Francotirador API Avanzado en: {url}")
    
    productos_extraidos = []
    urls_vistas = set()
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        
        if response.status_code == 200:
            productos = response.json().get('products', [])
            
            for p in productos:
                link = f"{domain}/products/{p['handle']}"
                
                if link in urls_vistas:
                    continue
                urls_vistas.add(link)
                
                titulo = p.get('title', 'Sin título')
                
                # --- NUEVA EXTRACCIÓN AVANZADA ---
                
                # 1. Categoría
                categoria = p.get('product_type', 'Uncategorized')
                if not categoria: 
                    categoria = 'Uncategorized'
                
                # 2. Etiquetas (Tags - Útiles para material, corte, color)
                etiquetas_raw = p.get('tags', [])
                etiquetas = ", ".join(etiquetas_raw) if isinstance(etiquetas_raw, list) else str(etiquetas_raw)
                
                # 3. Variantes (Para sacar Precio, Tallas y Stock)
                variantes = p.get('variants', [])
                precio = variantes[0].get('price', 0.0) if variantes else 0.0
                
                tallas_disponibles = []
                hay_stock_general = False
                
                for var in variantes:
                    # Si la variante tiene stock, guardamos su nombre (que suele ser la talla)
                    if var.get('available', False):
                        hay_stock_general = True
                        # 'title' en variantes suele ser "M", "L", "Black / XL", etc.
                        tallas_disponibles.append(var.get('title', ''))
                
                tallas_str = ", ".join(tallas_disponibles)
                
                # 4. Imagen
                imagenes = p.get('images', [])
                imagen_url = imagenes[0].get('src', '') if imagenes else ''
                
                # Empaquetamos todo
                productos_extraidos.append({
                    "name": titulo,
                    "url": link,
                    "price": float(precio) if precio else 0.0,
                    "image_url": imagen_url,
                    "category": categoria,
                    "sizes": tallas_str,
                    "tags": etiquetas,
                    "is_available": hay_stock_general
                })
                
            logging.info(f"¡Datos profundos extraídos! {len(productos_extraidos)} productos con Tallas y Categorías.")
        else:
            logging.error(f"La API está cerrada. Código: {response.status_code}")
            
    except Exception as e:
        logging.error(f"Fallo de conexión en la API: {e}")
        
    return productos_extraidos