import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import os
import re

# Configuración de página
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- CSS INSTITUCIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #fdf5e6; }
    [data-testid="stSidebar"] { background-color: #741b28 !important; }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #ffffff !important; font-weight: 600 !important; }

    /* Panel de Carga Negro */
    [data-testid="stFileUploader"] section { background-color: #000000 !important; border: 2px solid #b8860b !important; border-radius: 10px !important; }
    [data-testid="stFileUploaderDropzone"] { background-color: #000000 !important; }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] div, [data-testid="stFileUploader"] svg {
        color: #ffffff !important; fill: #ffffff !important;
    }
    [data-testid="stFileUploaderFileName"] { color: #b8860b !important; }

    /* Estilos de Botones */
    .stButton > button { border-radius: 8px; font-weight: bold; }
    .stButton > button[kind="primary"] {
        background-color: #741b28 !important;
        color: #fdf5e6 !important;
        border: 2px solid #b8860b !important;
        height: 3.5em;
    }
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    .factura-card {
        background-color: white; padding: 12px; border-left: 6px solid #741b28;
        border-radius: 4px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px;
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
st.subheader("Estructuración de Columnas Personalizada (D, F, L, M, AB, AC)")
st.divider()

if st.session_state.base_siat is not None:
    urls_raw = st.text_area("Escanea los links de los QR aquí:", height=150)
    
    if st.button("🚀 PROCESAR Y MAPEAR EXCEL", type="primary", use_container_width=True):
        links = re.findall(r'https?://[^\s]+?(?=https?://|$)', urls_raw)
        base = st.session_state.base_siat
        agregados = 0
        
        for link in links:
            try:
                link_clean = link.strip().split(' ')[0]
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
            st.success(f"Se añadieron {agregados} facturas al reporte.")

if st.session_state.registros_finales:
    st.write("### 📊 Vista Previa")
    temp_df = pd.DataFrame(st.session_state.registros_finales)
    st.dataframe(temp_df, use_container_width=True)

    # --- GENERACIÓN DE EXCEL CON COLUMNAS ESPECÍFICAS ---
    # Creamos un DataFrame con 29 columnas (A hasta AC)
    columnas_letras = [chr(i) for i in range(ord('A'), ord('Z') + 1)] + ['AA', 'AB', 'AC']
    df_excel = pd.DataFrame(columns=columnas_letras)

    # Mapeo según tu solicitud:
    # Fecha -> D (indice 3)
    # Nro Factura -> F (indice 5)
    # Razon Social -> L (indice 11)
    # NIT -> M (indice 12)
    # CUF -> AB (indice 27)
    # Monto -> AC (indice 28)

    registros = st.session_state.registros_finales
    df_final = pd.DataFrame(index=range(len(registros)), columns=columnas_letras)

    for i, r in enumerate(registros):
        df_final.iloc[i, 3] = r['Fecha']         # Columna D
        df_final.iloc[i, 5] = r['Nro Factura']   # Columna F
        df_final.iloc[i, 11] = r['Razon Social'] # Columna L
        df_final.iloc[i, 12] = r['NIT']          # Columna M
        df_final.iloc[i, 27] = r['CUF']          # Columna AB
        df_final.iloc[i, 28] = r['Monto']        # Columna AC

    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, header=True, sheet_name='Facturas')
        
        # Ajuste de tamaño de columnas
        worksheet = writer.sheets['Facturas']
        columnas_con_datos = {4, 6, 12, 13, 28, 29} # Letras en Excel son 1-indexed para openpyxl
        
        for i, col_name in enumerate(columnas_letras, 1):
            if i in columnas_con_datos:
                # Columnas con datos: Autoajustables
                worksheet.column_dimensions[col_name].width = 25
            else:
                # Columnas vacías: Tamaño mínimo
                worksheet.column_dimensions[col_name].width = 1

    st.download_button(
        label="📥 DESCARGAR EXCEL PARA UNIVALLE (D, F, L, M, AB, AC)",
        data=buff.getvalue(),
        file_name="Reporte_Contable_Estructurado.xlsx",
        use_container_width=True
    )

    if st.button("🗑️ Borrar lista"):
        st.session_state.registros_finales = []
        st.rerun()
