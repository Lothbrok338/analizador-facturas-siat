# --- REPORTE ---
if st.session_state.registros_finales:
    st.divider()
    st.write("### 📊 Reporte Generado")

    for i, reg in enumerate(st.session_state.registros_finales):
        col_data, col_del = st.columns([9, 1])

        with col_data:
            st.markdown(f"""
<div class='factura-card'>
<strong>{reg['Razón Social']}</strong> | 
<small>Factura: {reg['Nro Factura']} | Monto: {reg['Monto (Bs)']} Bs.</small>
</div>
            """, unsafe_allow_html=True)

        with col_del:
            st.write("")
            if st.button("X", key=f"del_{i}"):
                st.session_state.registros_finales.pop(i)
                st.rerun()

    st.markdown("---")

    # Crear DataFrame limpio
    df_res = pd.DataFrame(st.session_state.registros_finales).drop(columns=['CUF_FULL'])

    # Reiniciar índices para evitar desplazamientos extraños
    df_res = df_res.reset_index(drop=True)

    # Mostrar tabla en Streamlit
    st.dataframe(df_res, use_container_width=True)

    # Crear Excel
    buff = BytesIO()

    with pd.ExcelWriter(buff, engine='openpyxl') as w:
        df_res.to_excel(w, sheet_name='Reporte', index=False)

        # Obtener hoja
        ws = w.sheets['Reporte']

        # Ajustar ancho automático de columnas
        for column_cells in ws.columns:
            max_length = 0

            for cell in column_cells:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass

            adjusted_width = max_length + 5
            ws.column_dimensions[column_cells[0].column_letter].width = adjusted_width

    # Botón descarga
    st.download_button(
        label="📥 DESCARGAR EXCEL",
        data=buff.getvalue(),
        file_name="Reporte_Univalle.xlsx",
        use_container_width=True
    )

else:
    if st.session_state.base_siat is None:
        st.info("💡 Por favor, carga la base de datos en el panel lateral para comenzar.")
