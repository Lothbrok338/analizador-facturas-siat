import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from io import BytesIO

st.set_page_config(page_title="SIAT Bolivia Extractor", page_icon="🇧🇴")

st.title("🇧🇴 Extractor de Facturas Electrónicas")
st.markdown("Carga los datos del SIAT directamente a tu Excel sin errores manuales.")

if 'lista_facturas' not in st.session_state:
    st.session_state.lista_facturas = []

url_input = st.text_input("Pega el link del QR aquí:", placeholder="https://siat.impuestos.gob.bo/...")

if st.button("🚀 Extraer y Registrar"):
    if url_input:
        with st.spinner('Leyendo datos de Impuestos Nacionales...'):
            try:
                # 1. Extraer básicos de la URL (NIT, CUF, Número)
                parsed_url = urlparse(url_input)
                params = parse_qs(parsed_url.query)
                
                # 2. Web Scraping para datos internos
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                response = requests.get(url_input, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Buscamos por el texto de las etiquetas que vemos en la image_9b1d62.png
                def buscar_dato(etiqueta):
                    elemento = soup.find(text=lambda t: etiqueta in t)
                    if elemento:
                        # Buscamos el siguiente elemento de texto o el contenedor que tenga el valor
                        return elemento.find_next().text.strip()
                    return "No encontrado"

                razon_social = buscar_dato("Razón Social:")
                monto_raw = buscar_dato("Monto Total:")
                fecha = buscar_dato("Fecha Emisión:")
                
                # Limpiar el monto para que sea un número (quitar " Bs.")
                monto_limpio = monto_raw.replace(' Bs.', '').replace(',', '').strip()

                nueva_factura = {
                    "Fecha": fecha,
                    "Emisor": razon_social,
                    "NIT Emisor": params.get('nit', [''])[0],
                    "Nro Factura": params.get('numero', [''])[0],
                    "Monto Total (Bs)": monto_limpio,
                    "CUF": params.get('cuf', [''])[0]
                }
                
                st.session_state.lista_facturas.append(nueva_factura)
                st.success(f"Registrada: {razon_social} por {monto_raw}")
                
            except Exception as e:
                st.error("Hubo un problema al conectar con el SIAT. Verifica el link.")

# --- Tabla y Descarga ---
if st.session_state.lista_facturas:
    df = pd.DataFrame(st.session_state.lista_facturas)
    st.write("### Planilla Consolidada")
    st.dataframe(df)
    
    # Exportar a Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Facturas_Bolivia')
    
    st.download_button(
        label="📥 Descargar Reporte para Contabilidad",
        data=output.getvalue(),
        file_name="registro_siat_automatizado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if st.button("🗑️ Borrar lista actual"):
    st.session_state.lista_facturas = []
    st.rerun()
