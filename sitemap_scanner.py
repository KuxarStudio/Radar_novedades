import requests
from lxml import etree
import logging

# Configuración de mensajes de consola
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# REGLA DE ORO DEL SCRAPING: Nunca ir con las manos vacías. 
# Simulamos ser un navegador Chrome real desde un ordenador Windows.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

def check_sitemap(sitemap_url):
    """
    Descarga y lee un archivo sitemap.xml para extraer todas las URLs que contiene.
    """
    logging.info(f"Escaneando sitemap: {sitemap_url}")
    try:
        # Hacemos la petición a la web de forma sigilosa
        response = requests.get(sitemap_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            # Si nos dejan pasar, parseamos el archivo XML
            root = etree.fromstring(response.content)
            
            # Los sitemaps usan algo llamado 'namespaces', lo definimos para buscar las etiquetas <loc> (locations)
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = root.xpath('//ns:loc/text()', namespaces=namespaces)
            
            logging.info(f"¡Éxito! Encontradas {len(urls)} URLs en el sitemap.")
            
            # Imprimimos solo las primeras 5 para no saturar la terminal
            print("\n--- Muestra de los primeros 5 productos ---")
            for url in urls[:5]:
                print(f" -> {url}")
            print("-------------------------------------------\n")
            
            return urls
        else:
            logging.error(f"Error {response.status_code} al acceder al sitemap. Posible bloqueo o URL incorrecta.")
            return []
            
    except Exception as e:
        logging.error(f"Fallo de conexión: {e}")
        return []

if __name__ == "__main__":
    # Probamos con un sitemap público masivo para validar el motor lógico
    # sin que nos bloqueen los escudos anti-resellers.
    test_url = "https://www.apple.com/sitemap.xml"
    check_sitemap(test_url)