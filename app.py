import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO

st.set_page_config(page_title="Validador SIAT Pro", layout="wide", page_icon="🇧🇴")

# Estilo profesional para la oficina
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-color: #2c3e50; color: #2c3e50; }
    .stButton>button:hover { background-color: #2c3e50; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🇧🇴 Sistema de Registro de Compras SIAT")
st.write("Automatiza tu contabilidad: Carga el CSV mensual y busca facturas con el QR.")

# 1. Persistencia de datos en la sesión
if 'base_siat' not in st.session_state:
    st.session_state.base_siat = None
if 'registros_seleccionados' not in st.session_state:
    st.session_state.registros_seleccionados = []

# --- Barra Lateral para Carga de Datos ---
with st.sidebar:
    st.header("⚙️ Configuración")
    archivo_csv = st.file_uploader("Sube el archivo 'ComprasParaConfirmar.csv'", type=['csv'])
    
    if archivo_csv:
        try:
            # Leemos con la configuración exacta para archivos del SIAT Bolivia
            df_temp = pd.read_csv(archivo_csv, sep=',', encoding='latin1', on_bad_lines='skip')
            # Limpiamos espacios en los nombres de las columnas
            df_temp.columns = [c.strip() for c in df_temp.columns]
            st.session_state.base_siat = df_temp
            st.success(f"Base de datos cargada: {len(df_temp)} registros.")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

# --- Panel Principal de Búsqueda ---
if st.session_state.base_siat is not None:
    st.info("💡 Paso: Escanea el QR para buscar la factura en tu base de datos.")
    
    url_input = st.text_input("Enlace del QR (Pega aquí):", placeholder="https://siat.impuestos.gob.bo/...")
    
    if st.button("🔍 Buscar y Registrar en Reporte"):
        if url_input:
            try:
                # Extraemos el CUF del link
                p = parse_qs(urlparse(url_input).query)
                cuf_link = p.get('cuf', [''])[0].strip()
                
                if cuf_link:
                    # Buscamos en la columna 'CODIGO DE AUTORIZACION'
                    base = st.session_state.base_siat
                    resultado = base[base['CODIGO DE AUTORIZACION'] == cuf_link]
                    
                    if not resultado.empty:
                        # Extraemos los datos que realmente te sirven para tu reporte
                        factura = resultado.iloc[0]
                        datos_limpios = {
                            "Fecha": factura['FECHA DE FACTURA/DUI/DIM'],
                            "Razón Social": factura['RAZON SOCIAL PROVEEDOR'],
                            "NIT Proveedor": factura['NIT PROVEEDOR'],
                            "Nro Factura": factura['NUMERO FACTURA'],
                            "Monto Total (Bs)": factura['IMPORTE TOTAL COMPRA'],
                            "CUF": cuf_link[:15] + "..." # Acortado para vista
                        }
                        st.session_state.registros_seleccionados.append(datos_limpios)
                        st.success(f"✅ Encontrada: {datos_limpios['Razón Social']} por {datos_limpios['Monto Total (Bs)']} Bs.")
                    else:
                        st.error("❌ No se encontró la factura. Revisa si pertenece al mes del archivo subido.")
                else:
                    st.warning("El link pegado no parece tener un CUF válido.")
            except Exception as e:
                st.error(f"Error procesando el link: {e}")
else:
    st.warning("⚠️ Primero debes subir el archivo 'ComprasParaConfirmar.csv' en el panel izquierdo.")

# --- Tabla de Resultados y Descarga ---
if st.session_state.registros_seleccionados:
    st.divider()
    st.subheader("📋 Tu Reporte de Facturas Seleccionadas")
    df_final = pd.DataFrame(st.session_state.registros_seleccionados)
    st.dataframe(df_final, use_container_width=True)
    
    # Preparar Excel para descargar
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Facturas_Registradas')
    
    st.download_button(
        label="📥 Descargar Excel para Contabilidad",
        data=output.getvalue(),
        file_name="Reporte_Facturas_SIAT_Limpio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("🗑️ Borrar lista y empezar de nuevo"):
        st.session_state.registros_seleccionados = []
        st.rerun()
