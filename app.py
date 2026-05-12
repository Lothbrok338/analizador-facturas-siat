import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import os

# Configuración de página
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- CSS PROFESIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #fdf5e6; }
    [data-testid="stSidebar"] { background-color: #741b28 !important; }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: white !important;
    }
    .stButton > button { border-radius: 5px; font-weight: bold; }
    .btn-proceso > div > button {
        background-color: #741b28 !important;
        color: #fdf5e6 !important;
        border: 2px solid #b8860b !important;
        height: 3.5em !important;
    }
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE SESIÓN ---
if 'base_siat' not in st.session_state:
    st.session_state.base_siat = None
if 'registros_finales' not in st.session_state:
    st.session_state.registros_finales = []

# --- SIDEBAR ---
with st.sidebar:
    nombre_logo = "UNIVALLE LOGO.webp"
    if os.path.exists(nombre_logo):
        st.image(nombre_logo, use_container_width=True)
    
    st.markdown("### ⚙️ CONFIGURACIÓN")
    archivo_csv = st.file_uploader("Cargar ComprasParaConfirmar.csv", type=['csv'])
    
    if archivo_csv:
        try:
            df_siat = pd.read_csv(archivo_csv, sep=',', encoding='latin1', on_bad_lines='skip')
            df_siat.columns = [c.strip() for c in df_siat.columns]
            st.session_state.base_siat = df_siat
            st.success(f"Base cargada: {len(df_siat)} filas.")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()
    if st.button("🗑️ Resetear Todo"):
        st.session_state.registros_finales = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("UNIVERSIDAD DEL VALLE S.A.")
st.subheader("Control de Facturación Electrónica")
st.divider()

if st.session_state.base_siat is not None:
    st.markdown("### 📥 Carga Masiva de Facturas")
    urls_raw = st.text_area("Escanea o pega todos los links aquí (uno por línea):", height=200, placeholder="Link 1...\nLink 2...")
    
    if st.button("🚀 PROCESAR Y AÑADIR AL REPORTE", type="primary", use_container_width=True):
        links = [l.strip() for l in urls_raw.split('\n') if l.strip()]
        base = st.session_state.base_siat
        agregados = 0
        
        for link in links:
            try:
                params = parse_qs(urlparse(link).query)
                cuf = params.get('cuf', [''])[0].strip()
                match = base[base['CODIGO DE AUTORIZACION'] == cuf]
                
                if not match.empty:
                    item = match.iloc[0]
                    # Evitar duplicados exactos en el reporte
                    if not any(d['CUF_FULL'] == cuf for d in st.session_state.registros_finales):
                        st.session_state.registros_finales.append({
                            "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                            "Razón Social": item['RAZON SOCIAL PROVEEDOR'],
                            "NIT": item['NIT PROVEEDOR'],
                            "Nro Factura": item['NUMERO FACTURA'],
                            "Monto (Bs)": item['IMPORTE TOTAL COMPRA'],
                            "CUF_FULL": cuf
                        })
                        agregados += 1
            except:
                continue
        if agregados > 0:
            st.success(f"✅ Se añadieron {agregados} facturas nuevas.")
        else:
            st.warning("⚠️ No se encontraron facturas nuevas en el lote.")

# --- REPORTE CONSOLIDADO CON OPCIÓN DE ELIMINAR ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📊 Reporte Consolidado UNIVALLE")
    st.info("Si hay una factura incorrecta, presiona el botón 'Eliminar' de esa fila.")

    # Crear una lista para controlar qué eliminar
    for i, reg in enumerate(st.session_state.registros_finales):
        with st.expander(f"📄 {reg['Razón Social']} - {reg['Monto (Bs)']} Bs.", expanded=False):
            col_info, col_del = st.columns([8, 2])
            with col_info:
                st.write(f"**Fecha:** {reg['Fecha']} | **Factura:** {reg['Nro Factura']} | **NIT:** {reg['NIT']}")
                st.caption(f"CUF: {reg['CUF_FULL']}")
            with col_del:
                if st.button("Eliminar de la lista 🗑️", key=f"del_final_{i}"):
                    st.session_state.registros_finales.pop(i)
                    st.rerun()

    # Botones de exportación
    if st.session_state.registros_finales:
        df_res = pd.DataFrame(st.session_state.registros_finales).drop(columns=['CUF_FULL'])
        st.dataframe(df_res, use_container_width=True)
        
        buff = BytesIO()
        with pd.ExcelWriter(buff, engine='openpyxl') as w:
            df_res.to_excel(w, index=False)
        
        st.download_button("📥 DESCARGAR REPORTE FINAL EXCEL", buff.getvalue(), "Reporte_Contable_Univalle.xlsx", use_container_width=True)

else:
    if st.session_state.base_siat is None:
        st.warning("👈 Por favor, carga el archivo CSV en la barra lateral para comenzar.")

st.markdown("<br><p style='text-align: center; color: #741b28; font-weight: bold;'>UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
