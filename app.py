import streamlit as st
import pandas as pd

st.set_page_config(page_title="Reporte Puertos Biobío", page_icon="🚢", layout="centered")

st.title("🚢 Generador de Reporte Operacional")
st.subheader("Puertos Biobío")

# 1. Cargar archivo Excel
uploaded_file = st.file_uploader("Sube el archivo Excel (Resumen descargas)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Cargar hoja de base de datos
        df = pd.read_excel(uploaded_file, sheet_name='BD_Puerto')
        
        # Formatear la columna de fecha
        df['Fecha_Str'] = pd.to_datetime(df['Fecha descarga']).dt.strftime('%d/%m/%Y')
        fechas_disponibles = df['Fecha_Str'].unique()
        
        # 2. Selector de fecha
        fecha_sel = st.selectbox("📅 Selecciona la fecha de operación:", fechas_disponibles)
        
        # Filtrar datos por fecha seleccionada
        df_f = df[df['Fecha_Str'] == fecha_sel].copy()
        
        if not df_f.empty:
            total_trenes = len(df_f)
            llegada_si = (df_f['Cumple Llegada'] == 'SI').sum()
            salida_si = (df_f['Cumple Salida Retorno'] == 'SI').sum()
            pct_llegada = (llegada_si / total_trenes) * 100
            pct_salida = (salida_si / total_trenes) * 100
            
            conf = int(df_f['Carros confirmados'].sum())
            ret = int(df_f['Carros retornos'].sum())
            dif = int(df_f['Diferencia Carros Retorno'].sum())
            
            # Construir texto para WhatsApp
            reporte_wsp = f"*REPORTE EJECUTIVO DE OPERACIONES*\n"
            reporte_wsp += f"*Fecha:* {fecha_sel}\n\n"
            reporte_wsp += f"📊 *CONSOLIDADO GENERAL*\n"
            reporte_wsp += f"• *Total trenes operados:* {total_trenes} trenes\n"
            reporte_wsp += f"• *Cumplimiento llegada:* {pct_llegada:.1f}%\n"
            reporte_wsp += f"• *Cumplimiento salida (+0):* {pct_salida:.1f}%\n"
            reporte_wsp += f"• *Carros confirmados vs. Retorno:* {conf} confirmados / {ret} retornados (Diferencia: {dif:+d} vacíos)\n\n"
            reporte_wsp += f"---\n\n🚢 *DESGLOSE POR PUERTO*\n\n"
            
            for puerto in df_f['Puerto'].unique():
                sub = df_f[df_f['Puerto'] == puerto]
                c = len(sub)
                lleg_p = (sub['Cumple Llegada'] == 'SI').sum()
                sal_p = (sub['Cumple Salida Retorno'] == 'SI').sum()
                c_conf = int(sub['Carros confirmados'].sum())
                c_ret = int(sub['Carros retornos'].sum())
                c_dif = int(sub['Diferencia Carros Retorno'].sum())
                
                reporte_wsp += f"*{puerto} ({c} trenes)*\n"
                reporte_wsp += f"• *Cumplimiento llegada:* {(lleg_p/c)*100:.1f}%\n"
                reporte_wsp += f"• *Cumplimiento salida:* {(sal_p/c)*100:.1f}%\n"
                reporte_wsp += f"• *Carros:* {c_conf} confirmados / {c_ret} retornados (Diferencia: {c_dif:+d})\n\n"
            
            # Observaciones
            obs_list = df_f[df_f['Observaciones'].notna()]
            if not obs_list.empty:
                reporte_wsp += f"---\n\n⚠️ *NOVEDADES Y DESTACADOS OPERACIONALES*\n\n"
                for _, r in obs_list.iterrows():
                    obs_clean = str(r['Observaciones']).replace('\n', ' ')
                    reporte_wsp += f"• *Tren {r['Tren planificado']} ({r['Puerto']}):* {obs_clean}\n"
            
            # 3. Mapeo visual y cuadro de copia
            st.success("✅ ¡Reporte generado con éxito!")
            st.text_area("📋 Copia el siguiente texto directamente a WhatsApp:", reporte_wsp, height=400)
            
    except Exception as e:
        st.error(f"Error al procesar la estructura del archivo: {e}")