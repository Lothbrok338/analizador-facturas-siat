import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import os

# Configuración de página
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- PERSONALIZACIÓN VISUAL (COLORES UNIVALLE) ---
st.markdown("""
    <style>
    .stApp { background-color: #fdf5e6; }
    [data-testid="stSidebar"] { background-color: #741b28; }
    
    /* Forzar texto blanco en Sidebar para visibilidad */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: white !important;
    }
    
    /* Estilo para los botones de eliminar */
    .stButton>button {
        border-radius: 5px;
        font-weight: bold;
    }
    .btn-del>button {
        background-color: #ff4b4b !important;
        color: white !important;
        height: 2em !important;
        padding: 0px !important;
    }
    
    .stButton>button[kind="primary"] {
        background-color: #741b28;
        color: #fdf5e6;
        border: 2px solid #b8860b;
        height: 3.5em;
        width: 100%;
    }
    
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    .stDataFrame { border: 2px solid #741b28; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE SESIÓN ---
if 'base_siat' not in st.session_state:
    st.session_state.base_siat = None
if 'links_en_espera' not in st.session_state:
    st.session_state.links_en_espera = []
if 'registros_finales' not in st.session_state:
    st.session_state.registros_finales = []

# --- SIDEBAR ---
with st.sidebar:
    nombre_logo = "UNIVALLE LOGO.webp"
    if os.path.exists(nombre_logo):
        st.image(nombre_logo, use_container_width=True)
    
    st.markdown("### ⚙️ CONFIGURACIÓN")
    archivo_csv = st.file_uploader("Cargar Base Mensual (CSV)", type=['csv'])
    
    if archivo_csv:
        try:
            df_siat = pd.read_csv(archivo_csv, sep=',', encoding='latin1', on_bad_lines='skip')
            df_siat.columns = [c.strip() for c in df_siat.columns]
            st.session_state.base_siat = df_siat
            st.success(f"Base cargada: {len(df_siat)} filas.")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()
    if st.button("🗑️ Resetear Aplicación"):
        st.session_state.links_en_espera = []
        st.session_state.registros_finales = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("UNIVERSIDAD DEL VALLE S.A.")
st.subheader("Control Contable de Facturación Electrónica")
st.divider()

if st.session_state.base_siat is not None:
    # Área de escaneo
    st.markdown("### 📥 Escaneo de Facturas")
    nuevo_link = st.text_input("Escanear factura (el link se añadirá a la lista automáticamente):", key="scanner")
    
    # Si detecta un link, lo añade a la lista de espera y limpia el input
    if nuevo_link:
        if nuevo_link not in st.session_state.links_en_espera:
            st.session_state.links_en_espera.append(nuevo_link)
        st.rerun()

    # Mostrar lista de links para revisión
    if st.session_state.links_en_espera:
        st.markdown("#### 📋 Links listos para procesar:")
        for i, link in enumerate(st.session_state.links_en_espera):
            col_l, col_b = st.columns([9, 1])
            col_l.code(link) # Se muestra como código (no editable)
            if col_b.button("🗑️", key=f"del_{i}"):
                st.session_state.links_en_espera.pop(i)
                st.rerun()
        
        if st.button("🚀 PROCESAR LISTA ACTUAL", kind="primary"):
            base = st.session_state.base_siat
            for l_espera in st.session_state.links_en_espera:
                try:
                    params = parse_qs(urlparse(l_espera).query)
                    cuf = params.get('cuf', [''])[0].strip()
                    match = base[base['CODIGO DE AUTORIZACION'] == cuf]
                    
                    if not match.empty:
                        item = match.iloc[0]
                        # Evitar duplicados en el reporte final
                        if not any(d['CUF_FULL'] == cuf for d in st.session_state.registros_finales):
                            st.session_state.registros_finales.append({
                                "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                                "Razón Social": item['RAZON SOCIAL PROVEEDOR'],
                                "NIT": item['NIT PROVEEDOR'],
                                "Nro Factura": item['NUMERO FACTURA'],
                                "Monto (Bs)": item['IMPORTE TOTAL COMPRA'],
                                "CUF_FULL": cuf
                            })
                except:
                    continue
            st.session_state.links_en_espera = [] # Limpiar lista de espera tras procesar
            st.success("Proceso completado.")
            st.rerun()
else:
    st.warning("👈 Por favor, carga el archivo CSV en la barra lateral para comenzar.")

# --- REPORTE FINAL ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📊 Reporte Consolidado UNIVALLE")
    resumen = pd.DataFrame(st.session_state.registros_finales)
    # Mostramos una versión limpia (sin el CUF largo que ensucia la tabla)
    vista_tabla = resumen.copy()
    vista_tabla['CUF'] = vista_tabla['CUF_FULL'].str[:15] + "..."
    st.dataframe(vista_tabla.drop(columns=['CUF_FULL']), use_container_width=True)
    
    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as w:
        resumen.drop(columns=['CUF_FULL']).to_excel(w, index=False)
    
    st.download_button("📥 DESCARGAR EXCEL", buff.getvalue(), "Reporte_Univalle.xlsx")

st.markdown("<br><p style='text-align: center; color: #741b28;'>UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
