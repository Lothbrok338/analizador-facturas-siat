import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import os
import re

# Configuración de página
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- CSS INSTITUCIONAL (CON CONTRASTE CORREGIDO) ---
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
            # Cargamos con encoding latin1 para evitar errores de tildes
            df_siat = pd.read_csv(archivo_csv, sep=',', encoding='latin1', on_bad_lines='skip')
            df_siat.columns = [c.strip() for c in df_siat.columns]
            st.session_state.base_siat = df_siat
            st.success("✅ Base vinculada")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
    
    st.divider()
    if st.button("🗑️ Limpiar sesión", use_container_width=True):
        st.session_state.registros_finales = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("UNIVERSIDAD DEL VALLE S.A.")
st.subheader("Consolidación y Estructuración de Facturas")
st.divider()

if st.session_state.base_siat is not None:
    st.markdown("### 📥 Escaneo Masivo")
    urls_raw = st.text_area("Pega los links de los QR aquí:", height=150)
    
    if st.button("🚀 PROCESAR Y ESTRUCTURAR", type="primary", use_container_width=True):
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
                    if not any(d['CUF_FULL'] == cuf for d in st.session_state.registros_finales):
                        st.session_state.registros_finales.append({
                            "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                            "NIT Proveedor": item['NIT PROVEEDOR'],
                            "Razón Social": item['RAZON SOCIAL PROVEEDOR'],
                            "Nro Factura": item['NUMERO FACTURA'],
                            "Importe Total (Bs)": item['IMPORTE TOTAL COMPRA'],
                            "Crédito Fiscal": item.get('CREDITO FISCAL', 0),
                            "CUF_FULL": cuf
                        })
                        agregados += 1
            except:
                continue
        
        if agregados > 0:
            st.success(f"Se estructuraron {agregados} facturas nuevas.")
        else:
            st.warning("No se encontraron facturas nuevas para procesar.")

# --- REPORTE Y EXPORTACIÓN ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📊 Vista Previa del Reporte")
    
    # 1. Definimos el orden personalizado de las columnas para el Excel
    orden_columnas = ["Fecha", "NIT Proveedor", "Razón Social", "Nro Factura", "Importe Total (Bs)", "Crédito Fiscal"]
    
    df_res = pd.DataFrame(st.session_state.registros_finales)
    
    # Reordenamos el DataFrame antes de mostrarlo y descargarlo
    df_res = df_res[orden_columnas]
    
    st.dataframe(df_res, use_container_width=True)
    
    # Generación del archivo Excel
    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as writer:
        df_res.to_excel(writer, index=False, sheet_name='Reporte_Facturas')
        
        # Ajuste automático de ancho de columnas (Opcional pero recomendado)
        worksheet = writer.sheets['Reporte_Facturas']
        for idx, col in enumerate(df_res.columns):
            max_len = max(df_res[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

    st.download_button(
        label="📥 DESCARGAR EXCEL ESTRUCTURADO",
        data=buff.getvalue(),
        file_name="Reporte_Facturas_Univalle.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    st.markdown("---")
    st.write("#### Editar registros actuales:")
    for i, reg in enumerate(st.session_state.registros_finales):
        col_txt, col_btn = st.columns([9, 1])
        col_txt.markdown(f"**{reg['Fecha']}** - {reg['Razón Social']} (Bs. {reg['Importe Total (Bs)']})")
        if col_btn.button("X", key=f"del_{i}"):
            st.session_state.registros_finales.pop(i)
            st.rerun()
else:
    if st.session_state.base_siat is None:
        st.info("💡 Por favor, carga la base de datos en el panel lateral para comenzar.")

st.markdown("<br><p style='text-align: center; color: #741b28; opacity: 0.7;'>UNIVALLE S.A. | Gestión de Compras © 2026</p>", unsafe_allow_html=True)
