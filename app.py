import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import os

# Configuración de página
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- CSS MEJORADO (CONTRASTE Y DISEÑO) ---
st.markdown("""
    <style>
    .stApp { background-color: #fdf5e6; }
    [data-testid="stSidebar"] { background-color: #741b28 !important; }
    
    /* HACK DE VISIBILIDAD PARA EL SIDEBAR */
    [data-testid="stSidebar"] div, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p {
        color: white !important;
        font-weight: 500;
    }
    
    /* Estilo para los botones de eliminar individual */
    .stButton > button { border-radius: 5px; }
    .btn-delete > div > button {
        background-color: #ff4b4b !important;
        color: white !important;
        border: none !important;
    }

    /* Botón principal Univalle */
    .btn-proceso > div > button {
        background-color: #741b28 !important;
        color: #fdf5e6 !important;
        border: 2px solid #b8860b !important;
        height: 3.5em !important;
        width: 100% !important;
        font-size: 1.1em !important;
    }
    
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    .stDataFrame { border: 2px solid #741b28; border-radius: 10px; background-color: white; }
    
    /* Estilo para los links en espera */
    .link-box {
        background-color: #fff;
        padding: 10px;
        border-left: 5px solid #b8860b;
        margin-bottom: 5px;
        font-family: monospace;
    }
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
        st.session_state.links_en_espera = []
        st.session_state.registros_finales = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("UNIVERSIDAD DEL VALLE S.A.")
st.subheader("Control de Facturación Electrónica")
st.divider()

if st.session_state.base_siat is not None:
    # Área de escaneo con captura de evento
    st.markdown("### 📥 Escaneo de Facturas")
    
    # Usamos un formulario pequeño para que el 'Enter' del scanner siempre funcione
    with st.form("scanner_form", clear_on_submit=True):
        nuevo_link = st.text_input("Haz clic aquí y escanea la factura:")
        submit = st.form_submit_button("Añadir a la lista")
        
        if submit and nuevo_link:
            if nuevo_link not in st.session_state.links_en_espera:
                st.session_state.links_en_espera.append(nuevo_link)
            st.rerun()

    # Mostrar lista de links para revisión
    if st.session_state.links_en_espera:
        st.markdown(f"#### 📋 Facturas en espera ({len(st.session_state.links_en_espera)}):")
        
        for i, link in enumerate(st.session_state.links_en_espera):
            col_l, col_b = st.columns([8, 2])
            col_l.markdown(f"<div class='link-box'>{link[:80]}...</div>", unsafe_allow_html=True)
            
            # Botón de eliminar con estilo rojo
            if col_b.button(f"Borrar 🗑️", key=f"del_{i}"):
                st.session_state.links_en_espera.pop(i)
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Botón de procesar lote
        if st.button("🚀 PROCESAR LISTA Y BUSCAR DATOS", type="primary"):
            base = st.session_state.base_siat
            exitos = 0
            for l_espera in st.session_state.links_en_espera:
                try:
                    params = parse_qs(urlparse(l_espera).query)
                    cuf = params.get('cuf', [''])[0].strip()
                    match = base[base['CODIGO DE AUTORIZACION'] == cuf]
                    
                    if not match.empty:
                        item = match.iloc[0]
                        if not any(d['CUF_FULL'] == cuf for d in st.session_state.registros_finales):
                            st.session_state.registros_finales.append({
                                "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                                "Razón Social": item['RAZON SOCIAL PROVEEDOR'],
                                "NIT": item['NIT PROVEEDOR'],
                                "Nro Factura": item['NUMERO FACTURA'],
                                "Monto (Bs)": item['IMPORTE TOTAL COMPRA'],
                                "CUF_FULL": cuf
                            })
                            exitos += 1
                except:
                    continue
            
            st.session_state.links_en_espera = [] 
            st.success(f"Se procesaron {exitos} facturas con éxito.")
            st.rerun()
else:
    st.warning("👈 Por favor, carga el archivo CSV en la barra lateral para comenzar.")

# --- REPORTE FINAL ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📊 Reporte Consolidado UNIVALLE")
    df_res = pd.DataFrame(st.session_state.registros_finales)
    # Tabla limpia para visualización
    vista = df_res.copy()
    vista['CUF'] = vista['CUF_FULL'].str[:15] + "..."
    st.dataframe(vista.drop(columns=['CUF_FULL']), use_container_width=True)
    
    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as w:
        df_res.drop(columns=['CUF_FULL']).to_excel(w, index=False)
    
    st.download_button("📥 DESCARGAR EXCEL", buff.getvalue(), "Reporte_Contable_Univalle.xlsx")

st.markdown("<br><p style='text-align: center; color: #741b28; font-weight: bold;'>UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
