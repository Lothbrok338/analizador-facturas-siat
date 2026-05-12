import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO

# Configuración de página con estilo profesional
st.set_page_config(
    page_title="Gestión de Facturación | UNIVALLE S.A.",
    page_icon="🎓",
    layout="wide"
)

# Estilo CSS para personalización institucional (Colores Azul/Blanco/Rojo típicos de Univalle)
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #003366; /* Azul Institucional */
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #cc0000; /* Rojo de acento */
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #003366;
    }
    h1 { color: #003366; font-family: 'Arial Black', sans-serif; }
    h3 { color: #555; }
    .stDataFrame { border: 1px solid #003366; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Título e Identidad Institucional
st.title("🎓 UNIVALLE S.A. - Gestión Contable")
st.subheader("Sistema de Validación Masiva de Facturas SIAT")
st.divider()

# Inicialización de estados de sesión
if 'base_datos' not in st.session_state:
    st.session_state.base_datos = None
if 'reporte_final' not in st.session_state:
    st.session_state.reporte_final = []

# --- BARRA LATERAL (CONFIGURACIÓN) ---
with st.sidebar:
    st.image("https://www.univalle.edu/wp-content/uploads/2022/10/logo-univalle-horizontal.png", width=200) # Logo genérico referencial
    st.header("⚙️ Configuración")
    archivo_siat = st.file_uploader("1. Cargar Base Mensual (CSV)", type=['csv'])
    
    if archivo_siat:
        try:
            # Lectura optimizada para el formato SIAT Bolivia
            df = pd.read_csv(archivo_siat, sep=',', encoding='latin1', on_bad_lines='skip')
            df.columns = [c.strip() for c in df.columns] # Limpiar nombres de columnas
            st.session_state.base_datos = df
            st.success(f"✅ Base de Datos Cargada: {len(df)} registros.")
        except Exception as e:
            st.error(f"Error al leer archivo: {e}")
    
    st.divider()
    if st.button("🗑️ Limpiar Todo"):
        st.session_state.reporte_final = []
        st.rerun()

# --- ÁREA PRINCIPAL (OPERATIVA) ---
if st.session_state.base_datos is not None:
    col_input, col_info = st.columns([2, 1])
    
    with col_info:
        st.info("""
        **Modo Masivo:**
        - Haz clic en el recuadro de la izquierda.
        - Escanea todas las facturas seguidas.
        - El sistema separará los links automáticamente.
        """)

    with col_input:
        # Área de texto para múltiples links
        urls_raw = st.text_area("📦 Escanea aquí tus facturas (una por línea):", height=200, placeholder="Pega o escanea los links aquí...")
        
        if st.button("🚀 PROCESAR LOTE DE FACTURAS"):
            links = [l.strip() for l in urls_raw.split('\n') if l.strip()]
            
            if not links:
                st.warning("No hay links para procesar.")
            else:
                base = st.session_state.base_datos
                encontradas = 0
                errores = 0
                
                for link in links:
                    try:
                        # Extraer CUF de la URL
                        query = parse_qs(urlparse(link).query)
                        cuf = query.get('cuf', [''])[0].strip()
                        
                        # Buscar en CODIGO DE AUTORIZACION (Basado en tu CSV)
                        resultado = base[base['CODIGO DE AUTORIZACION'] == cuf]
                        
                        if not resultado.empty:
                            row = resultado.iloc[0]
                            st.session_state.reporte_final.append({
                                "Fecha": row['FECHA DE FACTURA/DUI/DIM'],
                                "Proveedor": row['RAZON SOCIAL PROVEEDOR'],
                                "NIT": row['NIT PROVEEDOR'],
                                "Nro Factura": row['NUMERO FACTURA'],
                                "Monto (Bs)": row['IMPORTE TOTAL COMPRA'],
                                "Estado": "Validado en SIAT"
                            })
                            encontradas += 1
                        else:
                            errores += 1
                    except:
                        errores += 1
                
                st.balloons()
                st.success(f"Proceso Terminado: {encontradas} facturas añadidas. ({errores} no encontradas o errores).")

# --- REPORTE Y DESCARGA ---
if st.session_state.reporte_final:
    st.divider()
    st.write("### 📊 Vista Previa del Reporte para UNIVALLE S.A.")
    df_resumen = pd.DataFrame(st.session_state.reporte_final)
    
    # Mostrar tabla estilizada
    st.dataframe(df_resumen.style.set_properties(**{'background-color': 'white', 'color': 'black', 'border-color': '#003366'}), use_container_width=True)
    
    # Botón de descarga
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_resumen.to_excel(writer, index=False, sheet_name='Facturas_Univalle')
    
    st.download_button(
        label="📥 DESCARGAR REPORTE EN EXCEL",
        data=output.getvalue(),
        file_name="Reporte_Contable_Univalle.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    if st.session_state.base_datos is None:
        st.warning("👈 Por favor, carga el archivo 'ComprasParaConfirmar.csv' en la barra lateral para comenzar.")

st.markdown("---")
st.caption("Sistema de Apoyo Contable Interno - UNIVALLE S.A. © 2026")
