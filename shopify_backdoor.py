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
    logging.info(f"Desplegando Francotirador API en: {url}")
    
    productos_extraidos = []
    urls_vistas = set() # Para evitar duplicados
    
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
                
                # 1. Extraemos el precio (suele estar dentro de las 'variants')
                variantes = p.get('variants', [])
                precio = variantes[0].get('price', 0.0) if variantes else 0.0
                
                # 2. Extraemos la URL de la imagen principal
                imagenes = p.get('images', [])
                imagen_url = imagenes[0].get('src', '') if imagenes else ''
                
                # Empaquetamos todo en un diccionario
                productos_extraidos.append({
                    "name": titulo,
                    "url": link,
                    "price": float(precio) if precio else 0.0,
                    "image_url": imagen_url
                })
                
            logging.info(f"¡Extracción rica en datos! {len(productos_extraidos)} productos con precio y foto.")
        else:
            logging.error(f"La API está cerrada. Código: {response.status_code}")
            
    except Exception as e:
        logging.error(f"Fallo de conexión en la API: {e}")
        
    return productos_extraidos