import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import re

st.set_page_config(page_title="SIAT Extractor Pro", page_icon="🇧🇴")

st.title("🇧🇴 Extractor de Facturas SIAT")
st.markdown("Si sale 'No encontrado', intenta procesar el link de nuevo.")

if 'lista_facturas' not in st.session_state:
    st.session_state.lista_facturas = []

url_input = st.text_input("Pega el link del QR aquí:")

if st.button("🚀 Extraer Datos"):
    if url_input:
        with st.spinner('Accediendo al portal de Impuestos...'):
            try:
                # 1. Datos básicos de la URL
                parsed_url = urlparse(url_input)
                params = parse_qs(parsed_url.query)
                
                # 2. Configuración de conexión (Simulando un navegador real)
                session = requests.Session()
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                }
                
                response = session.get(url_input, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Función mejorada para buscar por el texto de la etiqueta
                def obtener_valor(texto_etiqueta):
                    # Buscamos el elemento que contiene el texto (ej. "Monto Total:")
                    tag = soup.find(text=re.compile(texto_etiqueta, re.IGNORECASE))
                    if tag:
                        # Buscamos el siguiente div o span que contenga el valor real
                        contenedor = tag.find_parent().find_next_sibling()
                        if contenedor:
                            return contenedor.get_text(strip=True)
                    return "No encontrado"

                # Extraer según lo visto en image_9b1d62.png
                razon_social = obtener_valor("Razón Social")
                monto_raw = obtener_valor("Monto Total")
                fecha = obtener_valor("Fecha Emisión")

                nueva_factura = {
                    "Fecha": fecha,
                    "Razón Social": razon_social,
                    "NIT Emisor": params.get('nit', [''])[0],
                    "Nro Factura": params.get('numero', [''])[0],
                    "Monto (Bs)": monto_raw.replace(' Bs.', '').replace(',', ''),
                    "CUF": params.get('cuf', [''])[0]
                }
                
                st.session_state.lista_facturas.append(nueva_factura)
                st.success(f"Registrado: {razon_social}")
                
            except Exception as e:
                st.error("Error de conexión. Inténtalo una vez más.")

# --- Tabla y Descarga ---
if st.session_state.lista_facturas:
    df = pd.DataFrame(st.session_state.lista_facturas)
    st.dataframe(df)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Facturas')
    
    st.download_button(label="📥 Descargar Excel", data=output.getvalue(), 
                       file_name="facturas_siat.xlsx", 
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
