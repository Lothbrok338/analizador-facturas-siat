import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import os
import re

# Configuración de página
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- CSS DEFINITIVO (EL QUE YA TE GUSTABA) ---
st.markdown("""
    <style>
    .stApp { background-color: #fdf5e6; }
    [data-testid="stSidebar"] { background-color: #741b28 !important; }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Panel de Carga Negro Permanente */
    [data-testid="stFileUploader"] section {
        background-color: #000000 !important;
        border: 2px solid #b8860b !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploaderDropzone"] { background-color: #000000 !important; }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] small, 
    [data-testid="stFileUploader"] div, [data-testid="stFileUploader"] svg {
        color: #ffffff !important; fill: #ffffff !important;
    }
    [data-testid="stFileUploaderFileName"] { color: #b8860b !important; }

    /* Botones y Títulos */
    .stButton > button { border-radius: 8px; font-weight: bold; }
    .stButton > button[kind="primary"] {
        background-color: #741b28 !important;
        color: #fdf5e6 !important;
        border: 2px solid #b8860b !important;
        height: 3.5em;
    }
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    
    .factura-card {
        background-color: white;
        padding: 12px;
        border-left: 6px solid #741b28;
        border-radius: 4px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
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
    
    st.markdown("---")
    st.write("### PANEL DE CONTROL")
    archivo_csv = st.file_uploader("Cargar base de datos (.csv)", type=['csv'])
    
    if archivo_csv:
        try:
            df_siat = pd.read_csv(archivo_csv, sep=',', encoding='latin1', on_bad_lines='skip')
            df_siat.columns = [c.strip() for c in df_siat.columns]
            st.session_state.base_siat = df_siat
            st.success("✅ Base vinculada")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()
    if st.button("🗑️ Limpiar sesión", use_container_width=True):
        st.session_state.registros_finales = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("UNIVERSIDAD DEL VALLE S.A.")
st.subheader("Validación y Consolidación de Facturas")
st.divider()

if st.session_state.base_siat is not None:
    st.markdown("### 📥 Escaneo Masivo")
    urls_raw = st.text_area("Escanea o pega los links aquí:", height=150)
    
    if st.button("🚀 VALIDAR LOTE", type="primary", use_container_width=True):
        links = re.findall(r'https?://[^\s]+?(?=https?://|$)', urls_raw)
        base = st.session_state.base_siat
        agregados = 0
        
        for link in links:
            try:
                link_clean = link.strip().rstrip(',').rstrip(';')
                params = parse_qs(urlparse(link_clean).query)
                cuf = params.get('cuf', [''])[0].strip()
                
                match = base[base['CODIGO DE AUTORIZACION'] == cuf]
                if not match.empty:
                    item = match.iloc[0]
                    if not any(d['CUF'] == cuf for d in st.session_state.registros_finales):
                        st.session_state.registros_finales.append({
                            "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                            "NIT": item['NIT PROVEEDOR'],
                            "Razon Social": item['RAZON SOCIAL PROVEEDOR'],
                            "Nro Factura": item['NUMERO FACTURA'],
                            "Monto": item['IMPORTE TOTAL COMPRA'],
                            "CUF": cuf
                        })
                        agregados += 1
            except:
                continue
        
        if agregados > 0:
            st.success(f"Se añadieron {agregados} registros.")

# --- REPORTE ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📊 Reporte Generado")
    
    for i, reg in enumerate(st.session_state.registros_finales):
        col_data, col_del = st.columns([9, 1])
        with col_data:
            st.markdown(f"""
            <div class='factura-card'>
                <strong>{reg['Razon Social']}</strong> | 
                <small>Factura: {reg['Nro Factura']} | Monto: {reg['Monto']} Bs.</small>
            </div>
            """, unsafe_allow_html=True)
        with col_del:
            st.write("") 
            if st.button("X", key=f"del_{i}"):
                st.session_state.registros_finales.pop(i)
                st.rerun()

    st.markdown("---")
    
    # --- GENERACIÓN DE EXCEL ESTRUCTURADO (D, F, L, M, AB, AC) ---
    columnas_letras = [chr(i) for i in range(ord('A'), ord('Z') + 1)] + ['AA', 'AB', 'AC']
    df_final = pd.DataFrame(index=range(len(st.session_state.registros_finales)), columns=columnas_letras)

    for i, r in enumerate(st.session_state.registros_finales):
        df_final.iloc[i, 3] = r['Fecha']         # D
        df_final.iloc[i, 5] = r['Nro Factura']   # F
        df_final.iloc[i, 11] = r['Razon Social'] # L
        df_final.iloc[i, 12] = r['NIT']          # M
        df_final.iloc[i, 27] = r['CUF']          # AB
        df_final.iloc[i, 28] = r['Monto']        # AC

    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Reporte')
        worksheet = writer.sheets['Reporte']
        columnas_activas = {'D', 'F', 'L', 'M', 'AB', 'AC'}
        
        for col_name in columnas_letras:
            if col_name in columnas_activas:
                worksheet.column_dimensions[col_name].width = 22
            else:
                worksheet.column_dimensions[col_name].width = 1 # Columnas vacías mínimas

    st.download_button(
        label="📥 DESCARGAR EXCEL",
        data=buff.getvalue(),
        file_name="Reporte_Univalle.xlsx",
        use_container_width=True
    )
else:
    if st.session_state.base_siat is None:
        st.info("💡 Por favor, carga la base de datos en el panel lateral para comenzar.")

st.markdown("<br><p style='text-align: center; color: #741b28; opacity: 0.7;'>UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
