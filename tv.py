#!/usr/bin/env python3
# generador_m3u8.py

import threading
from playwright.sync_api import sync_playwright

CANALES = [
    "https://www.cablevisionhd.com/telefe-en-vivo.html",
    "https://www.cablevisionhd.com/el-trece-en-vivo.html",
    "https://www.cablevisionhd.com/las-estrellas-en-vivo.html",
    "https://www.cablevisionhd.com/space-en-vivo.html",
    "https://www.cablevisionhd.com/star-channel-en-vivo.html",
    "https://www.cablevisionhd.com/tnt-series-en-vivo.html",
    "https://www.cablevisionhd.com/tnt-en-vivo.html",
    "https://www.cablevisionhd.com/universal-channel-en-vivo.html",
    "https://www.cablevisionhd.com/cinemax-en-vivo.html",
    "https://www.cablevisionhd.com/syfy-en-vivo.html",
    "https://www.cablevisionhd.com/fx-en-vivo.html",
    "https://www.cablevisionhd.com/warner-bros-tv-en-vivo.html",
    "https://www.cablevisionhd.com/cinecanal-en-vivo.html",
    "https://www.cablevisionhd.com/amc-en-vivo.html",
    "https://www.cablevisionhd.com/studio-universal-en-vivo.html",
    "https://www.cablevisionhd.com/canal-sony-en-vivo.html",
    "https://www.cablevisionhd.com/discovery-channel-en-vivo.html",
    "https://www.cablevisionhd.com/history-en-vivo.html",
    "https://www.cablevisionhd.com/nat-geo-en-vivo.html",
    "https://www.cablevisionhd.com/espn-premium-en-vivo.html",
    "https://www.cablevisionhd.com/espn-en-vivo.html",
    "https://www.cablevisionhd.com/espn-2-en-vivo.html",
    "https://www.cablevisionhd.com/espn-3-en-vivo.html",
    "https://www.cablevisionhd.com/espn-4-en-vivo.html",
    "https://www.cablevisionhd.com/espn-5-en-vivo.html",
    "https://www.cxtvenvivo.com/tv-en-vivo/hits-mexicanos",
    "https://www.cxtvenvivo.com/tv-en-vivo/retro-plus-tv",
    "https://www.cxtvenvivo.com/tv-en-vivo/thats-80s",
    "https://www.cxtvenvivo.com/tv-en-vivo/thats-70s",
    "https://www.cxtvenvivo.com/tv-en-vivo/music-top",
]

SALIDA = "skd.m3u"

TIMEOUT_V1 = 5000   # ms — vuelta rápida
TIMEOUT_V2 = 12000  # ms — vuelta lenta

def nombre_desde_url(url):
    slug = url.split("/")[-1]
    slug = slug.replace("-en-vivo.html", "").replace("-en-vivo.php", "")
    slug = slug.replace(".html", "").replace(".php", "")
    return slug.replace("-", " ").title()

def capturar_m3u8(browser, url, espera_ms):
    encontradas = []
    encontrado = threading.Event()

    def on_request(request):
        if ".m3u8" in request.url and request.url not in encontradas:
            encontradas.append(request.url)
            encontrado.set()

    def on_response(response):
        if ".m3u8" in response.url and response.url not in encontradas:
            encontradas.append(response.url)
            encontrado.set()

    page = browser.new_page()
    page.on("request", on_request)
    page.on("response", on_response)

    # intento 1: URL original
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
    except:
        pass
    encontrado.wait(timeout=espera_ms / 1000)

    # intento 2: si falló y era .html probar .php con tiempo propio
    if not encontradas and url.endswith(".html"):
        encontrado.clear()
        url_php = url.replace(".html", ".php")
        print("php...", end=" ", flush=True)
        try:
            page.goto(url_php, wait_until="domcontentloaded", timeout=15000)
        except:
            pass
        encontrado.wait(timeout=espera_ms / 1000)

    page.close()
    return encontradas[0] if encontradas else None

def procesar_vuelta(browser, lista_urls, espera_ms, numero):
    print(f"\n═══ Vuelta {numero} — máx {espera_ms//1000}s por extensión ({len(lista_urls)} canales) ═══\n")
    obtenidos = {}
    fallidos = []

    for url in lista_urls:
        nombre = nombre_desde_url(url)
        print(f"  [*] {nombre}...", end=" ", flush=True)
        m3u8 = capturar_m3u8(browser, url, espera_ms)
        if m3u8:
            print("✓")
            obtenidos[url] = (nombre, m3u8)
        else:
            print("✗")
            fallidos.append(url)

    return obtenidos, fallidos

def main():
    resultados = {}
    aun_fallaron = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Vuelta 1 — rápida
        obtenidos, fallidos = procesar_vuelta(browser, CANALES, TIMEOUT_V1, 1)
        resultados.update(obtenidos)

        # Vuelta 2 — solo los que fallaron, más tiempo
        if fallidos:
            obtenidos, aun_fallaron_urls = procesar_vuelta(browser, fallidos, TIMEOUT_V2, 2)
            resultados.update(obtenidos)
            aun_fallaron = [nombre_desde_url(u) for u in aun_fallaron_urls]

        browser.close()

    # Generar .m3u respetando el orden original
    lineas = ["#EXTM3U"]
    ok = 0

    for url in CANALES:
        if url in resultados:
            nombre, m3u8 = resultados[url]
            lineas.append(f"#EXTINF:-1,{nombre}")
            lineas.append(m3u8)
            ok += 1

    with open(SALIDA, "w") as f:
        f.write("\n".join(lineas) + "\n")

    print(f"\n[✓] {ok}/{len(CANALES)} canales → {SALIDA}")
    if aun_fallaron:
        print(f"[!] Sin stream: {', '.join(aun_fallaron)}")

if __name__ == "__main__":
    main()
