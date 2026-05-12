import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import os
import re

# Configuración de página
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- CSS RADICAL PARA VISIBILIDAD Y DISEÑO ---
st.markdown("""
    <style>
    .stApp { background-color: #fdf5e6; }
    [data-testid="stSidebar"] { background-color: #741b28 !important; }
    
    /* Forzar visibilidad total en el Sidebar */
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }

    .stButton > button { border-radius: 5px; font-weight: bold; }
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    
    /* Estilo para las filas del reporte editable */
    .factura-item {
        background-color: white;
        padding: 15px;
        border: 1px solid #741b28;
        border-radius: 8px;
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
            st.success(f"Base cargada con {len(df_siat)} registros.")
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
    st.caption("Escanea todas tus facturas aquí. El sistema las separará automáticamente aunque aparezcan pegadas.")
    urls_raw = st.text_area("Cuadro de escaneo:", height=150, placeholder="Escanea aquí...")
    
    if st.button("🚀 PROCESAR Y VALIDAR LOTE", type="primary", use_container_width=True):
        # LÓGICA QUIRÚRGICA: Busca cualquier texto que empiece con http y termine antes del siguiente http o espacio
        # Esto separa links pegados como: https://...https://...
        links = re.findall(r'https?://[^\s]+?(?=https?://|$)', urls_raw)
        
        base = st.session_state.base_siat
        agregados = 0
        
        for link in links:
            try:
                # Limpiamos el link de caracteres basura que puedan quedar al final
                link_clean = link.strip().rstrip(',').rstrip(';')
                params = parse_qs(urlparse(link_clean).query)
                cuf = params.get('cuf', [''])[0].strip()
                
                match = base[base['CODIGO DE AUTORIZACION'] == cuf]
                
                if not match.empty:
                    item = match.iloc[0]
                    # Evitar duplicados por CUF
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
            st.balloons()
            st.success(f"Se procesaron {len(links)} links. {agregados} facturas nuevas añadidas.")
        else:
            st.warning("No se encontraron facturas nuevas. Revisa que el archivo CSV corresponda a estos links.")

# --- REPORTE EDITABLE ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📊 Reporte Consolidado UNIVALLE")
    st.info("Revisa la lista. Puedes eliminar filas individuales antes de descargar el Excel.")
    
    # Creamos una copia para iterar y permitir borrado
    for i, reg in enumerate(st.session_state.registros_finales):
        col_data, col_action = st.columns([8, 1])
        with col_data:
            st.markdown(f"""
            <div class='factura-item'>
                <strong>{reg['Razón Social']}</strong><br>
                <small>Fecha: {reg['Fecha']} | Factura: {reg['Nro Factura']} | Monto: {reg['Monto (Bs)']} Bs.</small>
            </div>
            """, unsafe_allow_html=True)
        with col_action:
            st.write("") # Espaciado
            if st.button("🗑️", key=f"btn_del_{i}"):
                st.session_state.registros_finales.pop(i)
                st.rerun()

    # Botón de Descarga Final
    if st.session_state.registros_finales:
        df_res = pd.DataFrame(st.session_state.registros_finales).drop(columns=['CUF_FULL'])
        
        # Mostrar tabla final
        st.dataframe(df_res, use_container_width=True)
        
        buff = BytesIO()
        with pd.ExcelWriter(buff, engine='openpyxl') as w:
            df_res.to_excel(w, index=False)
        
        st.download_button(
            label="📥 DESCARGAR REPORTE EXCEL FINAL",
            data=buff.getvalue(),
            file_name="Reporte_Contable_Univalle.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    if st.session_state.base_siat is None:
        st.warning("👈 Por favor, carga el archivo CSV en la barra lateral para comenzar.")

st.markdown("<br><p style='text-align: center; color: #741b28; font-weight: bold;'>Sistema de Apoyo Contable Interno - UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
