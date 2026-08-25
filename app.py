import streamlit as st
import pandas as pd
import numpy as np

# Configuración inicial de la página
st.set_page_config(
    page_title="Reporte Operacional Puertos Biobío",
    page_icon="🚢",
    layout="centered"
)

st.title("🚢 Generador de Reporte Ejecutivo")
st.subheader("Operaciones Puertos Biobío")

# 1. Cargar archivo Excel
uploaded_file = st.file_uploader("Sube el archivo Excel (Resumen descargas)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Cargar la pestaña base
        df = pd.read_excel(uploaded_file, sheet_name='BD_Puerto')
        
        # Convertir y dar formato a las fechas
        df['Fecha_Descarga_DT'] = pd.to_datetime(df['Fecha descarga'])
        df['Fecha_Str'] = df['Fecha_Descarga_DT'].dt.strftime('%d/%m/%Y')
        fechas_disponibles = df['Fecha_Str'].unique()
        
        # 2. Selector de fecha
        fecha_sel = st.selectbox("📅 Selecciona la fecha de operación:", fechas_disponibles)
        
        # Filtrar el dataframe
        df_f = df[df['Fecha_Str'] == fecha_sel].copy()
        
        if not df_f.empty:
            total_trenes = len(df_f)
            llegada_si = (df_f['Cumple Llegada'] == 'SI').sum()
            salida_si = (df_f['Cumple Salida Retorno'] == 'SI').sum()
            pct_llegada = (llegada_si / total_trenes) * 100
            pct_salida = (salida_si / total_trenes) * 100
            
            # Carros
            planificados = int(df_f['Carros planificados'].sum())
            confirmados = int(df_f['Carros confirmados'].sum())
            descargados = int(df_f['Carros descargados'].sum())
            retornados = int(df_f['Carros retornos'].sum())
            diferencia = int(df_f['Diferencia Carros Retorno'].sum())
            
            # Efectividad de descarga
            efectividad_descarga = (descargados / confirmados * 100) if confirmados > 0 else 100.0
            
            # --- CÁLCULO DE TIEMPOS (PUNTO 1) ---
            # Conversión de columnas a datetime para cálculo exacto
            df_f['DT_Arribo_Real'] = pd.to_datetime(df_f['Fecha Hora Llegada Real'])
            df_f['DT_Postura'] = pd.to_datetime(df_f['Postura bodega'])
            df_f['DT_Termino'] = pd.to_datetime(df_f['Término descarga'])
            df_f['DT_Retorno_Real'] = pd.to_datetime(df_f['Fecha Hora Retorno Real'])
            
            # Función para ajustar diferencia de minutos si cruza la medianoche
            def calc_min_diff(end, start):
                if pd.isna(end) or pd.isna(start):
                    return np.nan
                diff = (end - start).total_seconds() / 60.0
                if diff < 0:
                    diff += 1440.0 # +24 horas si pasa de medianoche
                return diff

            df_f['Min_Postura'] = df_f.apply(lambda r: calc_min_diff(r['DT_Postura'], r['DT_Arribo_Real']), axis=1)
            df_f['Min_Salida'] = df_f.apply(lambda r: calc_min_diff(r['DT_Retorno_Real'], r['DT_Termino']), axis=1)
            
            prom_postura_min = df_f['Min_Postura'].mean()
            prom_salida_hrs = (df_f['Min_Salida'].mean() / 60.0) if not df_f['Min_Salida'].isna().all() else 0.0
            
            # Formato condicional del promedio de postura
            txt_prom_postura = f"{prom_postura_min:.0f} min" if pd.notna(prom_postura_min) else "N/I"
            txt_prom_salida = f"{prom_salida_hrs:.1f} hrs" if pd.notna(prom_salida_hrs) else "N/I"

            # --- ARMAR TEXTO PARA WHATSAPP ---
            reporte = f"*REPORTE EJECUTIVO DE OPERACIONES*\n"
            reporte += f"*Fecha:* {fecha_sel}\n\n"
            
            reporte += f"📊 *CONSOLIDADO GENERAL*\n"
            reporte += f"• *Total trenes operados:* {total_trenes} trenes\n"
            reporte += f"• *Cumplimiento llegada:* {pct_llegada:.1f}% ({llegada_si} de {total_trenes} en itinerario)\n"
            reporte += f"• *Cumplimiento salida:* {pct_salida:.1f}% ({salida_si} de {total_trenes} en itinerario)\n"
            reporte += f"• *Efectividad de descarga:* {efectividad_descarga:.1f}% ({descargados} descargados / {confirmados} confirmados)\n"
            reporte += f"• *Carros confirmados vs. Retorno:* {confirmados} confirmados / {retornados} retornados (Diferencia: {diferencia:+d} vacíos)\n\n"
            
            reporte += f"⏱️ *INDICADORES DE TIEMPO OPERATIVO*\n"
            reporte += f"• *Tiempo promedio de postura:* {txt_prom_postura} (Arribo Real a Postura Bodega)\n"
            reporte += f"• *Tiempo promedio de salida:* {txt_prom_salida} (Término Descarga a Retorno Real)\n\n"
            
            # --- PUNTO 3: CONSOLIDADO POR CLIENTE ---
            reporte += f"🏭 *CONSOLIDADO POR CLIENTE*\n"
            df_cliente = df_f.groupby('Cliente').agg({
                'Carros confirmados': 'sum',
                'Carros retornos': 'sum'
            }).reset_index()
            
            for _, r_c in df_cliente.iterrows():
                reporte += f"• *{r_c['Cliente']}:* {int(r_c['Carros confirmados'])} confirmados / {int(r_c['Carros retornos'])} retornados\n"
            
            reporte += f"\n---\n\n🚢 *DESGLOSE POR PUERTO*\n\n"
            
            # --- DESGLOSE POR PUERTO ---
            for puerto in df_f['Puerto'].unique():
                sub = df_f[df_f['Puerto'] == puerto]
                c = len(sub)
                lleg_p = (sub['Cumple Llegada'] == 'SI').sum()
                sal_p = (sub['Cumple Salida Retorno'] == 'SI').sum()
                c_conf = int(sub['Carros confirmados'].sum())
                c_ret = int(sub['Carros retornos'].sum())
                c_dif = int(sub['Diferencia Carros Retorno'].sum())
                
                reporte += f"*{puerto} ({c} trenes)*\n"
                reporte += f"• *Cumplimiento llegada:* {(lleg_p/c)*100:.1f}%\n"
                reporte += f"• *Cumplimiento salida:* {(sal_p/c)*100:.1f}%\n"
                reporte += f"• *Carros:* {c_conf} confirmados / {c_ret} retornados (Diferencia: {c_dif:+d})\n\n"
            
            # --- NOVEDADES ---
            obs_list = df_f[df_f['Observaciones'].notna()]
            if not obs_list.empty:
                reporte += f"---\n\n⚠️ *NOVEDADES Y DESTACADOS OPERACIONALES*\n\n"
                for _, r_obs in obs_list.iterrows():
                    obs_clean = str(r_obs['Observaciones']).replace('\n', ' ')
                    reporte += f"• *Tren {r_obs['Tren planificado']} ({r_obs['Puerto']}):* {obs_clean}\n"
            
            # Visualización en pantalla
            st.success("✅ ¡Reporte ejecutivo generado con éxito!")
            st.text_area("📋 Copia y pega este reporte en WhatsApp:", reporte, height=450)
            
    except Exception as e:
        st.error(f"Error procesando la estructura del archivo: {e}")