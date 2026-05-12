import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse, parse_qs
from io import BytesIO

st.set_page_config(page_title="SIAT Central | Automatización", layout="wide", page_icon="📈")

# Estilo "Clean" para la oficina
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2c3e50; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("💼 Gestión de Facturas Electrónicas - SIAT")
st.info("Solo pega el enlace del QR. El sistema extraerá los montos y nombres automáticamente.")

if 'df_final' not in st.session_state:
    st.session_state.df_final = pd.DataFrame(columns=["Fecha", "Razón Social", "NIT Emisor", "Nro Factura", "Monto (Bs)", "CUF"])

# Interfaz simplificada
col1, col2 = st.columns([3, 1])
with col1:
    url_input = st.text_input("Enlace de Factura:", placeholder="Pega el link aquí...")
with col2:
    procesar = st.button("Registrar Factura")

if procesar and url_input:
    with st.spinner('Sincronizando con SIAT...'):
        try:
            # 1. Extraer llaves del link
            p = parse_qs(urlparse(url_input).query)
            nit, cuf, numero = p.get('nit', [''])[0], p.get('cuf', [''])[0], p.get('numero', [''])[0]

            # 2. Petición directa al motor de búsqueda del SIAT
            # Intentamos obtener el JSON de datos que el SIAT usa para llenar la image_9b1d62.png
            headers = {'User-Agent': 'Mozilla/5.0'}
            api_url = f"https://siat.impuestos.gob.bo/consulta/QR?nit={nit}&cuf={cuf}&numero={numero}"
            res = requests.get(api_url, headers=headers, timeout=10)
            
            # 3. Lógica de extracción quirúrgica
            # Aquí usamos selectores CSS para ir directo al grano
            from bs4 import BeautifulSoup
            s = BeautifulSoup(res.text, 'html.parser')
            
            # Buscamos los valores basados en la estructura de la image_9b1d62.png
            def get_val(label):
                tag = s.find(text=lambda t: label in t)
                return tag.find_parent().find_next_sibling().text.strip() if tag else "N/A"

            # Creamos la fila
            nueva_fila = {
                "Fecha": get_val("Fecha Emisión"),
                "Razón Social": get_val("Razón Social"),
                "NIT Emisor": nit,
                "Nro Factura": numero,
                "Monto (Bs)": get_val("Monto Total").replace(' Bs.', '').replace(',', ''),
                "CUF": cuf[:15] + "..." # Acortado para estética
            }

            # Añadir al DataFrame global
            st.session_state.df_final = pd.concat([st.session_state.df_final, pd.DataFrame([nueva_fila])], ignore_index=True)
            st.success(f"Factura de {nueva_fila['Razón Social']} añadida.")
        except:
            st.error("Error de conexión. Verifica que el link sea válido.")

# Mostrar tabla elegante
if not st.session_state.df_final.empty:
    st.divider()
    st.dataframe(st.session_state.df_final, use_container_width=True)
    
    # Exportación limpia
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        st.session_state.df_final.to_excel(w, index=False)
    
    st.download_button("📥 Descargar Reporte Consolidado (Excel)", out.getvalue(), "facturas_siat.xlsx")

if st.button("Limpiar Sesión"):
    st.session_state.df_final = pd.DataFrame(columns=["Fecha", "Razón Social", "NIT Emisor", "Nro Factura", "Monto (Bs)", "CUF"])
    st.rerun()
