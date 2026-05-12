import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="SIAT Extractor Inteligente", page_icon="🇧🇴")

st.title("🇧🇴 Extractor de Facturas SIAT")
st.markdown("""
### Instrucciones para evitar el 'No encontrado':
1. Abre el link del QR en tu navegador.
2. Selecciona **todo el texto** de la página (Ctrl + A) y cópialo (Ctrl + C).
3. Pégalo en el cuadro de abajo y dale a 'Procesar Texto'.
""")

if 'lista_facturas' not in st.session_state:
    st.session_state.lista_facturas = []

# Cuadro de texto grande para pegar el contenido
texto_pegado = st.text_area("Pega aquí todo el texto de la página de la factura:", height=200)

if st.button("🚀 Procesar Texto"):
    if texto_pegado:
        try:
            # Lógica de limpieza con Expresiones Regulares (Regex)
            def extraer(patron, texto):
                resultado = re.search(patron, texto)
                return resultado.group(1).strip() if resultado else "No encontrado"

            # Buscamos los patrones exactos que vimos en la image_9b1d62.png
            razon_social = extraer(r"Razón Social:\s*(.*)", texto_pegado)
            monto = extraer(r"Monto Total:\s*([\d\.,]+)", texto_pegado)
            fecha = extraer(r"Fecha Emisión:\s*([\d/ :]+)", texto_pegado)
            nit = extraer(r"NIT Emisor:\s*(\d+)", texto_pegado)
            nro_factura = extraer(r"Número de Factura:\s*(\d+)", texto_pegado)
            cuf = extraer(r"CUF:\s*([A-Z0-9]+)", texto_pegado)

            nueva_factura = {
                "Fecha": fecha,
                "Razón Social": razon_social,
                "NIT Emisor": nit,
                "Nro Factura": nro_factura,
                "Monto (Bs)": monto.replace(',', ''),
                "CUF": cuf
            }
            
            st.session_state.lista_facturas.append(nueva_factura)
            st.success(f"¡Factura de {razon_social} añadida!")
        except Exception as e:
            st.error("No se pudo procesar el texto. Asegúrate de copiar toda la página.")

# --- Tabla y Descarga ---
if st.session_state.lista_facturas:
    df = pd.DataFrame(st.session_state.lista_facturas)
    st.write("### Planilla Acumulada")
    st.dataframe(df)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Facturas')
    
    st.download_button(label="📥 Descargar Excel para Contabilidad", 
                       data=output.getvalue(), 
                       file_name="contabilidad_siat.xlsx", 
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if st.button("🗑️ Borrar Todo"):
    st.session_state.lista_facturas = []
    st.rerun()
