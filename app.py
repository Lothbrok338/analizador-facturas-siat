import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO, StringIO
import os
import re
import json
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe, get_as_dataframe

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    creds_dict = json.loads(st.secrets["google_credentials_json"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_url(st.secrets["spreadsheet_url"])

# --- FUNCIONES DE BASE DE DATOS EN LA NUBE (CON CACHÉ) ---
@st.cache_data(ttl=600)
def cargar_historico():
    try:
        sheet = init_connection()
        ws = sheet.worksheet("HISTORICO_FACTURAS")
        df = get_as_dataframe(ws).dropna(how='all').dropna(axis=1, how='all')
        if df.empty or 'CUF / Autorización' not in df.columns:
            return pd.DataFrame(columns=["Fecha", "Razón Social", "NIT", "Nro Factura", "Monto (Bs)", "CUF / Autorización"])
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Fecha", "Razón Social", "NIT", "Nro Factura", "Monto (Bs)", "CUF / Autorización"])

def guardar_historico(df_nuevo):
    sheet = init_connection()
    ws = sheet.worksheet("HISTORICO_FACTURAS")
    df_actual = cargar_historico()
    df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
    ws.clear()
    set_with_dataframe(ws, df_final)
    cargar_historico.clear()

@st.cache_data(ttl=600)
def cargar_siat_maestro():
    try:
        sheet = init_connection()
        ws = sheet.worksheet("SIAT_MAESTRO")
        df = get_as_dataframe(ws).dropna(how='all').dropna(axis=1, how='all')
        if df.empty:
            return None
        return df
    except:
        return None

def guardar_siat_maestro(df_nuevo):
    sheet = init_connection()
    ws = sheet.worksheet("SIAT_MAESTRO")
    df_actual = cargar_siat_maestro()
    
    if df_actual is not None and not df_actual.empty:
        df_combinado = pd.concat([df_actual, df_nuevo], ignore_index=True)
        df_combinado = df_combinado.drop_duplicates(subset=['CODIGO DE AUTORIZACION'], keep='last')
    else:
        df_combinado = df_nuevo
        
    ws.clear()
    set_with_dataframe(ws, df_combinado)
    cargar_siat_maestro.clear()

# --- ESTILOS CSS PROFESIONALES ---
st.markdown("""
<style>
    .stApp { background-color: #fdf5e6; }
    [data-testid="stSidebar"] { background-color: #741b28 !important; border-right: 2px solid #b8860b; }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #ffffff !important; font-weight: 500 !important; }
    [data-testid="stFileUploader"] section { background-color: #1a1a1a !important; border: 1px dashed #b8860b !important; border-radius: 8px !important; }
    [data-testid="stFileUploaderFileName"], [data-testid="stFileUploaderFileData"], 
    [data-testid="stFileUploader"] small { color: #b8860b !important; opacity: 1 !important; }
    [data-testid="stFileUploader"] button { background-color: #741b28 !important; color: white !important; border: 1px solid #b8860b !important; }
    .stButton > button { border-radius: 4px; font-weight: 600; text-transform: uppercase; transition: all 0.3s ease; }
    div.stButton > button:first-child:not([kind="primary"]) { background-color: #741b28 !important; color: #ffffff !important; border: 1px solid #b8860b !important; }
    .stButton > button[kind="primary"] { background-color: #741b28 !important; color: #ffffff !important; border: 1px solid #b8860b !important; height: 3em; }
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    .factura-card { background-color: #ffffff; padding: 15px; border-left: 5px solid #741b28; border-radius: 4px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .cuf-text { color: #b8860b; font-family: monospace; font-weight: bold; }
    .alerta-duplicado { color: #d32f2f; font-weight: bold; background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #d32f2f;}
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE SESIÓN ---
if 'registros_sesion' not in st.session_state:
    st.session_state.registros_sesion = []

# --- PANEL LATERAL ---
with st.sidebar:
    logo_path = "UNIVALLE LOGO.webp"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("<h2 style='color:white; text-align:center;'>UNIVALLE</h2>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center;'>INSTRUMENTO DE CONTROL CONTABLE</h4>", unsafe_allow_html=True)
    st.divider()
    
    archivo_csv = st.file_uploader("Vincular Base SIAT Diaria (.csv)", type=['csv'])
    
    if archivo_csv:
        try:
            content = archivo_csv.read()
            try:
                decoded_content = content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_content = content.decode('latin1')
            
            df_diario = pd.read_csv(StringIO(decoded_content), sep=',', on_bad_lines='skip')
            df_diario.columns = [c.strip() for c in df_diario.columns]
            df_diario = df_diario.map(lambda x: x.strip() if isinstance(x, str) else x)
            
            with st.spinner("Guardando base en Google Sheets..."):
                guardar_siat_maestro(df_diario)
            st.success("Base diaria respaldada con éxito")
        except Exception as e:
            st.error(f"Error en la lectura: {e}")
    
    st.divider()
    
    df_historico_actual = cargar_historico()
    df_siat_actual = cargar_siat_maestro()
    
    st.write("☁️ **Estadísticas en la Nube:**")
    st.write(f"- Base Maestra: {len(df_siat_actual) if df_siat_actual is not None else 0} registros")
    st.write(f"- Facturas Procesadas: {len(df_historico_actual)}")
    
    st.divider()
    if st.button("🔄 Limpiar Pantalla", use_container_width=True):
        st.session_state.registros_sesion = []
        st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.title("UNIVERSIDAD DEL VALLE S.A.")
st.subheader("Módulo Centralizado de Procesamiento de Datos Fiscales")
st.divider()

base_siat = cargar_siat_maestro()

if base_siat is not None:
    # --- IMPLEMENTACIÓN DE PESTAÑAS MÓDULO MANUAL / QR ---
    tab1, tab2 = st.tabs(["📥 Consolidación por Enlaces (QR)", "🔍 Búsqueda y Registro Manual"])
    
    # PESTAÑA 1: PROCESAMIENTO POR QR / URL
    with tab1:
        urls_raw = st.text_area("Depósito de URLs para procesamiento masivo:", height=150, placeholder="Pega los enlaces aquí...", key="txt_urls")
        
        if st.button("🚀 EJECUTAR PROCESAMIENTO DE DATOS", type="primary", use_container_width=True, key="btn_qr"):
            links = re.findall(r'https?://[^\s]+?(?=https?://|$)', urls_raw)
            historico_db = cargar_historico()
            cufs_historicos = historico_db['CUF / Autorización'].tolist() if not historico_db.empty else []
            
            agregados = 0
            duplicados = 0
            nuevos_registros_df = []
            
            with st.spinner("Procesando enlaces..."):
                for link in links:
                    try:
                        link_clean = link.strip().rstrip(',').rstrip(';')
                        params = parse_qs(urlparse(link_clean).query)
                        cuf_extraido = params.get('cuf', [''])[0].strip()
                        
                        if not cuf_extraido:
                            continue

                        if cuf_extraido in cufs_historicos or any(d['CUF / Autorización'] == cuf_extraido for d in st.session_state.registros_sesion):
                            duplicados += 1
                            continue

                        match = base_siat[base_siat['CODIGO DE AUTORIZACION'] == cuf_extraido]
                        
                        if not match.empty:
                            item = match.iloc[0]
                            rs_raw = str(item['RAZON SOCIAL PROVEEDOR'])
                            try:
                                razon_social = rs_raw.encode('latin1').decode('utf-8') if "Ã" in rs_raw else rs_raw
                            except:
                                razon_social = rs_raw
                            
                            nuevo_registro = {
                                "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                                "Razón Social": razon_social,
                                "NIT": item['NIT PROVEEDOR'],
                                "Nro Factura": item['NUMERO FACTURA'],
                                "Monto (Bs)": item['IMPORTE TOTAL COMPRA'],
                                "CUF / Autorización": cuf_extraido
                            }
                            st.session_state.registros_sesion.append(nuevo_registro)
                            nuevos_registros_df.append(nuevo_registro)
                            agregados += 1
                    except:
                        continue
                
                if nuevos_registros_df:
                    guardar_historico(pd.DataFrame(nuevos_registros_df))
                    st.success(f"Operación exitosa: {agregados} registros validados y subidos a la nube.")
                
                if duplicados > 0:
                    st.markdown(f"<div class='alerta-duplicado'>⚠️ SE INHIBIERON {duplicados} FACTURAS REPETIDAS (Ya se encuentran registradas en la nube).</div>", unsafe_allow_html=True)

    # PESTAÑA 2: MOTOR DE BÚSQUEDA MANUAL DIRECTO
    with tab2:
        st.markdown("### Búsqueda de Comprobante en Base Maestra")
        col_f, col_n = st.columns(2)
        with col_f:
            nro_factura_in = st.text_input("Número de Factura:", placeholder="Ej. 4032", key="input_nro_fac")
        with col_n:
            nit_in = st.text_input("NIT del Proveedor (Opcional para precisar):", placeholder="Ej. 1020304029", key="input_nit")
            
        if st.button("🔍 LOCALIZAR Y CONSOLIDAR REGISTRO", type="primary", use_container_width=True, key="btn_manual"):
            if not nro_factura_in.strip():
                st.warning("Por favor, introduzca un número de factura válido.")
            else:
                # Normalización técnica de tipos para evitar fallos de flotantes en Pandas
                base_siat['NUMERO FACTURA_STR'] = base_siat['NUMERO FACTURA'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                match_manual = base_siat[base_siat['NUMERO FACTURA_STR'] == nro_factura_in.strip()]
                
                if nit_in.strip() != "" and not match_manual.empty:
                    base_siat['NIT_STR'] = base_siat['NIT PROVEEDOR'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    match_manual = match_manual[match_manual['NIT_STR'] == nit_in.strip()]
                
                if match_manual.empty:
                    st.error("No se localizó ningún registro coincidente en la Base Maestra SIAT con los datos proveídos.")
                else:
                    historico_db = cargar_historico()
                    cufs_historicos = historico_db['CUF / Autorización'].tolist() if not historico_db.empty else []
                    
                    agregados_m = 0
                    duplicados_m = 0
                    nuevos_m_df = []
                    
                    for idx, item in match_manual.iterrows():
                        cuf_extraido = str(item['CODIGO DE AUTORIZACION']).strip()
                        
                        if cuf_extraido in cufs_historicos or any(d['CUF / Autorización'] == cuf_extraido for d in st.session_state.registros_sesion):
                            duplicados_m += 1
                            continue
                            
                        rs_raw = str(item['RAZON SOCIAL PROVEEDOR'])
                        try:
                            razon_social = rs_raw.encode('latin1').decode('utf-8') if "Ã" in rs_raw else rs_raw
                        except:
                            razon_social = rs_raw
                            
                        nuevo_registro = {
                            "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                            "Razón Social": razon_social,
                            "NIT": item['NIT PROVEEDOR'],
                            "Nro Factura": item['NUMERO FACTURA'],
                            "Monto (Bs)": item['IMPORTE TOTAL COMPRA'],
                            "CUF / Autorización": cuf_extraido
                        }
                        st.session_state.registros_sesion.append(nuevo_registro)
                        nuevos_m_df.append(nuevo_registro)
                        agregados_m += 1
                    
                    if nuevos_m_df:
                        guardar_historico(pd.DataFrame(nuevos_m_df))
                        st.success(f"✅ Factura Nro {nro_factura_in} localizada y agregada de forma exitosa al archivo central de la nube.")
                    
                    if duplicados_m > 0 and agregados_m == 0:
                        st.markdown(f"<div class='alerta-duplicado'>⚠️ CONTROL DE CONTROL: El documento fiscal consultado ya fue procesado con anterioridad y reside en el histórico.</div>", unsafe_allow_html=True)

# --- REPORTE INTEGRADO ---
if st.session_state.registros_sesion:
    st.divider()
    st.write("### 📊 Historial de Datos Procesados en la Sesión Actual")
    
    for i, reg in enumerate(st.session_state.registros_sesion):
        st.markdown(f"""
        <div class='factura-card'>
            <span style='color: #741b28; font-weight: bold; font-size: 1.1em;'>{reg['Razón Social']}</span><br>
            <small>Factura: {reg['Nro Factura']} | Monto: {reg['Monto (Bs)']} Bs. | NIT: {reg['NIT']}</small><br>
            <span class='cuf-text'>CUF: {reg['CUF / Autorización']}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 📥 Descargar Historial Completo Compilado de la Nube")
    df_historico_completo = cargar_historico()
    st.dataframe(df_historico_completo, use_container_width=True)
    
    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as w:
        df_historico_completo.to_excel(w, index=False)
    
    st.download_button(
        label="DESCARGAR INFORME TÉCNICO COMPLETO (EXCEL)",
        data=buff.getvalue(),
        file_name="Reporte_Nube_UNIVALLE.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
else:
    if base_siat is None:
        st.info("📌 Sistema en espera. Por favor, vincule la base de datos diaria para iniciar el procesamiento.")
    else:
        st.info("📌 Base operativa en la nube. Seleccione un método arriba (Enlaces o Búsqueda Manual) para validar registros.")

st.markdown("<br><p style='text-align: center; color: #741b28; opacity: 0.6;'>DEPARTAMENTO DE CONTABILIDAD | UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
