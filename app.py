import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO

# Configuración de página con identidad institucional
st.set_page_config(
    page_title="Sistema Contable | UNIVALLE",
    page_icon="🎓",
    layout="wide"
)

# --- PERSONALIZACIÓN VISUAL (COLORES UNIVALLE) ---
# Guinda: #741b28 | Crema: #fdf5e6 | Oro: #b8860b
st.markdown("""
    <style>
    .stApp {
        background-color: #fdf5e6;
    }
    [data-testid="stSidebar"] {
        background-color: #741b28;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3.5em;
        background-color: #741b28;
        color: #fdf5e6;
        font-weight: bold;
        border: 2px solid #b8860b;
    }
    .stButton>button:hover {
        background-color: #b8860b;
        color: white;
        border: 2px solid #741b28;
    }
    h1, h2, h3 {
        color: #741b28;
        font-family: 'Times New Roman', serif;
    }
    .stDataFrame {
        border: 2px solid #741b28;
        border-radius: 10px;
        background-color: white;
    }
    div.stTextInput > div > div > input {
        background-color: white;
    }
    div.stTextArea > div > div > textarea {
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    # He puesto una URL genérica de Univalle, pero Streamlit usará el icono local si prefieres
    st.image("https://www.univalle.edu/wp-content/uploads/2022/10/logo-univalle-horizontal.png", width=150)
with col_titulo:
    st.title("UNIVERSIDAD DEL VALLE S.A.")
    st.subheader("Departamento de Contabilidad - Validador de Facturas")

st.divider()

# --- LÓGICA DE SESIÓN ---
if 'base_siat' not in st.session_state:
    st.session_state.base_siat = None
if 'registros_finales' not in st.session_state:
    st.session_state.registros_finales = []

# --- SIDEBAR (CONFIGURACIÓN) ---
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    archivo_csv = st.file_uploader("Cargar Base Mensual (CSV)", type=['csv'])
    
    if archivo_csv:
        try:
            df_siat = pd.read_csv(archivo_csv, sep=',', encoding='latin1', on_bad_lines='skip')
            df_siat.columns = [c.strip() for c in df_siat.columns]
            st.session_state.base_siat = df_siat
            st.success(f"Base cargada: {len(df_siat)} filas.")
        except Exception as e:
            st.error(f"Error al leer CSV: {e}")
    
    st.divider()
    if st.button("🗑️ Limpiar Todo"):
        st.session_state.registros_finales = []
        st.rerun()

# --- PANEL DE PROCESAMIENTO ---
if st.session_state.base_siat is not None:
    st.markdown("### 📦 Procesamiento por Lote")
    urls_raw = st.text_area("Escanea las facturas aquí (una debajo de otra):", height=200, placeholder="Pega los links aquí...")
    
    if st.button("PROCESAR LOTE DE FACTURAS"):
        links = [l.strip() for l in urls_raw.split('\n') if l.strip()]
        
        if links:
            base = st.session_state.base_siat
            nuevos = 0
            
            for link in links:
                try:
                    params = parse_qs(urlparse(link).query)
                    cuf = params.get('cuf', [''])[0].strip()
                    
                    # Búsqueda en el archivo CSV (CODIGO DE AUTORIZACION es el CUF)
                    match = base[base['CODIGO DE AUTORIZACION'] == cuf]
                    
                    if not match.empty:
                        item = match.iloc[0]
                        st.session_state.registros_finales.append({
                            "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                            "Razón Social": item['RAZON SOCIAL PROVEEDOR'],
                            "NIT": item['NIT PROVEEDOR'],
                            "Nro Factura": item['NUMERO FACTURA'],
                            "Monto (Bs)": item['IMPORTE TOTAL COMPRA'],
                            "CUF": cuf[:15] + "..."
                        })
                        nuevos += 1
                except:
                    continue
            
            if nuevos > 0:
                st.balloons()
                st.success(f"Se añadieron {nuevos} facturas al reporte.")
            else:
                st.error("No se encontraron coincidencias para los links ingresados.")
else:
    st.warning("👈 Por favor, carga el archivo de Impuestos en la barra lateral.")

# --- TABLA Y EXPORTACIÓN ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📝 Reporte Contable Generado")
    resumen = pd.DataFrame(st.session_state.registros_finales)
    st.dataframe(resumen, use_container_width=True)
    
    # Exportar Excel
    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as w:
        resumen.to_excel(w, index=False)
    
    st.download_button(
        label="📥 DESCARGAR REPORTE EN EXCEL",
        data=buff.getvalue(),
        file_name="Reporte_Univalle_SIAT.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("<br><br><p style='text-align: center; color: #741b28;'>Sistema de Apoyo Contable Interno - UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
