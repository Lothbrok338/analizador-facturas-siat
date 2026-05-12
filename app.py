import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import os
import re

# Configuración de página
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- CSS DEFINITIVO: ESTÉTICA UNIVALLE ---
st.markdown("""
    <style>
    /* Fondo General */
    .stApp { background-color: #fdf5e6; }
    
    /* Barra Lateral */
    [data-testid="stSidebar"] { background-color: #741b28 !important; }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Botones Principales */
    .stButton > button { 
        border-radius: 8px; 
        font-weight: bold; 
        transition: 0.3s;
    }
    .stButton > button[kind="primary"] {
        background-color: #741b28 !important;
        color: #fdf5e6 !important;
        border: 2px solid #b8860b !important;
        height: 3.5em;
    }
    .stButton > button:hover {
        border-color: #fdf5e6 !important;
        transform: scale(1.02);
    }

    /* Botones de Eliminar (Pequeños) */
    .btn-del > div > button {
        background-color: #741b28 !important;
        color: white !important;
        border: 1px solid #b8860b !important;
        font-size: 0.8rem !important;
    }

    /* Títulos */
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    
    /* Alertas Personalizadas */
    .stAlert {
        background-color: white !important;
        border: 1px solid #b8860b !important;
        color: #741b28 !important;
    }

    /* Inputs y TextAreas */
    textarea, input {
        border: 1px solid #741b28 !important;
    }

    /* Contenedor de Factura */
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
    st.markdown("### ⚙️ CONFIGURACIÓN")
    archivo_csv = st.file_uploader("Subir ComprasParaConfirmar.csv", type=['csv'])
    
    if archivo_csv:
        try:
            df_siat = pd.read_csv(archivo_csv, sep=',', encoding='latin1', on_bad_lines='skip')
            df_siat.columns = [c.strip() for c in df_siat.columns]
            st.session_state.base_siat = df_siat
            st.success("✅ Base cargada correctamente")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()
    if st.button("🗑️ Resetear Aplicación", use_container_width=True):
        st.session_state.registros_finales = []
        st.rerun()

# --- CABECERA ---
st.title("UNIVERSIDAD DEL VALLE S.A.")
st.subheader("Sistema Contable - Validación de Facturas")
st.divider()

if st.session_state.base_siat is not None:
    # ENTRADA MASIVA
    st.markdown("### 📥 Carga Masiva")
    urls_raw = st.text_area("Escanea aquí tus códigos QR (procesamiento automático de links pegados):", height=150)
    
    if st.button("🚀 PROCESAR Y VALIDAR LOTE", type="primary", use_container_width=True):
        # El Regex quirúrgico para separar por 'http'
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
            st.success(f"Se añadieron {agregados} facturas nuevas al reporte.")
        else:
            st.warning("No se encontraron facturas nuevas en este lote.")

# --- REPORTE CONSOLIDADO ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📊 Reporte Consolidado UNIVALLE")
    
    # Lista de facturas con botón de eliminar estilizado
    for i, reg in enumerate(st.session_state.registros_finales):
        col_data, col_del = st.columns([9, 1])
        with col_data:
            st.markdown(f"""
            <div class='factura-card'>
                <strong>{reg['Razón Social']}</strong> | 
                <small>Factura: {reg['Nro Factura']} | Monto: {reg['Monto (Bs)']} Bs. | Fecha: {reg['Fecha']}</small>
            </div>
            """, unsafe_allow_html=True)
        with col_del:
            st.write("") # Alineación manual
            if st.button("Eliminar", key=f"del_{i}", help="Quitar de la lista"):
                st.session_state.registros_finales.pop(i)
                st.rerun()

    # Tabla Final y Descarga
    st.markdown("---")
    df_res = pd.DataFrame(st.session_state.registros_finales).drop(columns=['CUF_FULL'])
    st.dataframe(df_res, use_container_width=True)
    
    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as w:
        df_res.to_excel(w, index=False)
    
    st.download_button(
        label="📥 DESCARGAR REPORTE FINAL EXCEL",
        data=buff.getvalue(),
        file_name="Reporte_Contable_Univalle.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
else:
    if st.session_state.base_siat is None:
        st.info("💡 Por favor, carga el archivo de compras del SIAT en el panel de la izquierda.")

st.markdown("<br><p style='text-align: center; color: #741b28; opacity: 0.7;'>UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
