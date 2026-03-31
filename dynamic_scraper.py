from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def scrape_storefront(url):
    logging.info(f"Cambiando estrategia. Entrando por la puerta principal: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        productos_extraidos = []
        urls_vistas = set()
        
        try:
            response = page.goto(url, wait_until="domcontentloaded")
            
            if response and response.status in [403, 503]:
                page.wait_for_timeout(5000)
            else:
                page.wait_for_timeout(2000)
                
            elementos_producto = page.query_selector_all("a[href*='/products/']")
            
            for el in elementos_producto:
                link = el.get_attribute("href")
                if link:
                    dominio = url.split("/collections")[0] 
                    if link.startswith("/"):
                        link = dominio + link
                        
                    if link not in urls_vistas:
                        urls_vistas.add(link)
                        # Creamos el nombre a partir de la URL
                        temp_name = link.split('/')[-1].replace('-', ' ').title()
                        
                        # Empaquetamos en diccionario (precios e imágenes en blanco por ahora en el visual)
                        productos_extraidos.append({
                            "name": temp_name,
                            "url": link,
                            "price": 0.0,
                            "image_url": ""
                        })
            
            if productos_extraidos:
                logging.info(f"¡Éxito! Hemos encontrado {len(productos_extraidos)} productos únicos.")
                
        except Exception as e:
            logging.error(f"Fallo en la misión: {e}")
            
        finally:
            browser.close()
            
        return productos_extraidos