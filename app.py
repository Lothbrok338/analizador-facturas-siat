import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Facturación SIAT Bolivia", page_icon="📄")

st.title("📄 Extractor de Facturas SIAT")
st.markdown("Pega el link del QR para registrar la factura sin taipear.")

# Inicializar la lista de facturas en la sesión
if 'lista_facturas' not in st.session_state:
    st.session_state.lista_facturas = []

url_input = st.text_input("Enlace de la factura (URL del QR):")

if st.button("Procesar Factura"):
    if url_input:
        try:
            # Extraer parámetros directamente de la URL para mayor velocidad
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(url_input)
            params = parse_qs(parsed_url.query)
            
            nueva_factura = {
                "NIT Emisor": params.get('nit', [''])[0],
                "CUF": params.get('cuf', [''])[0],
                "Número Factura": params.get('numero', [''])[0],
                "URL": url_input
            }
            
            st.session_state.lista_facturas.append(nueva_factura)
            st.success(f"Factura {nueva_factura['Número Factura']} añadida!")
        except Exception as e:
            st.error("Error al leer el enlace. Asegúrate de que sea un link válido del SIAT.")

# Mostrar tabla y opción de descarga
if st.session_state.lista_facturas:
    df = pd.DataFrame(st.session_state.lista_facturas)
    st.subheader("Facturas Registradas")
    st.dataframe(df)
    
    # Convertir a Excel
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Facturas')
    
    st.download_button(
        label="📥 Descargar Excel para Contabilidad",
        data=output.getvalue(),
        file_name="reporte_facturas_siat.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if st.button("Limpiar lista"):
    st.session_state.lista_facturas = []
    st.rerun()
