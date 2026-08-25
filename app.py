import streamlit as st
import pandas as pd
import numpy as np

# Configuración de página
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
        df = pd.read_excel(uploaded_file, sheet_name='BD_Puerto')
        
        # Formatear fechas
        df['Fecha_Descarga_DT'] = pd.to_datetime(df['Fecha descarga'])
        df['Fecha_Str'] = df['Fecha_Descarga_DT'].dt.strftime('%d/%m/%Y')
        fechas_disponibles = df['Fecha_Str'].unique()
        
        # 2. Selector de fecha
        fecha_sel = st.selectbox("📅 Selecciona la fecha de operación:", fechas_disponibles)
        
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
            
            efectividad_descarga = (descargados / confirmados * 100) if confirmados > 0 else 100.0
            
            # --- CÁLCULO DE TIEMPOS MÍNIMOS Y MÁXIMOS ---
            df_f['DT_Arribo_Real'] = pd.to_datetime(df_f['Fecha Hora Llegada Real'])
            df_f['DT_Postura'] = pd.to_datetime(df_f['Postura bodega'])
            df_f['DT_Termino'] = pd.to_datetime(df_f['Término descarga'])
            df_f['DT_Retorno_Real'] = pd.to_datetime(df_f['Fecha Hora Retorno Real'])
            
            def calc_min_diff(end, start):
                if pd.isna(end) or pd.isna(start):
                    return np.nan
                diff = (end - start).total_seconds() / 60.0
                if diff < 0:
                    diff += 1440.0
                return diff

            df_f['Min_Postura'] = df_f.apply(lambda r: calc_min_diff(r['DT_Postura'], r['DT_Arribo_Real']), axis=1)
            df_f['Min_Salida'] = df_f.apply(lambda r: calc_min_diff(r['DT_Retorno_Real'], r['DT_Termino']), axis=1)
            
            # Mínimo y Máximo de Postura
            df_postura_val = df_f.dropna(subset=['Min_Postura'])
            if not df_postura_val.empty:
                idx_min_pos = df_postura_val['Min_Postura'].idxmin()
                idx_max_pos = df_postura_val['Min_Postura'].idxmax()
                
                postura_min_txt = f"{df_postura_val.loc[idx_min_pos, 'Min_Postura']:.0f} min (Tren {df_postura_val.loc[idx_min_pos, 'Tren planificado']} - {df_postura_val.loc[idx_min_pos, 'Puerto']})"
                postura_max_txt = f"{df_postura_val.loc[idx_max_pos, 'Min_Postura']:.0f} min (Tren {df_postura_val.loc[idx_max_pos, 'Tren planificado']} - {df_postura_val.loc[idx_max_pos, 'Puerto']})"
            else:
                postura_min_txt, postura_max_txt = "N/I", "N/I"
                
            # Mínimo y Máximo de Salida (filtrando descalces atípicos > 12 hrs)
            df_salida_val = df_f.dropna(subset=['Min_Salida'])
            df_salida_val = df_salida_val[df_salida_val['Min_Salida'] < 720]
            
            if not df_salida_val.empty:
                idx_min_sal = df_salida_val['Min_Salida'].idxmin()
                idx_max_sal = df_salida_val['Min_Salida'].idxmax()
                
                salida_min_txt = f"{df_salida_val.loc[idx_min_sal, 'Min_Salida']/60:.1f} hrs (Tren {df_salida_val.loc[idx_min_sal, 'Tren planificado']} - {df_salida_val.loc[idx_min_sal, 'Puerto']})"
                salida_max_txt = f"{df_salida_val.loc[idx_max_sal, 'Min_Salida']/60:.1f} hrs (Tren {df_salida_val.loc[idx_max_sal, 'Tren planificado']} - {df_salida_val.loc[idx_max_sal, 'Puerto']})"
            else:
                salida_min_txt, salida_max_txt = "N/I", "N/I"

            # --- ARMAR TEXTO PARA WHATSAPP ---
            reporte = f"*REPORTE DE OPERACIONES PUERTOS BIOBIO*\n"
            reporte += f"*Fecha:* {fecha_sel}\n\n"
            
            reporte += f"📊 *CONSOLIDADO GENERAL*\n"
            reporte += f"• *Total trenes operados:* {total_trenes} trenes\n"
            reporte += f"• *Cumplimiento llegada:* {pct_llegada:.1f}% ({llegada_si} de {total_trenes} en itinerario)\n"
            reporte += f"• *Cumplimiento salida:* {pct_salida:.1f}% ({salida_si} de {total_trenes} en itinerario)\n"
            reporte += f"• *Efectividad de descarga:* {efectividad_descarga:.1f}% ({descargados} descargados / {confirmados} confirmados)\n"
            reporte += f"• *Carros confirmados vs. Retorno:* {confirmados} confirmados / {retornados} retornados (Diferencia: {diferencia:+d} vacíos)\n\n"
            
            reporte += f"⏱️ *INDICADORES DE TIEMPO OPERATIVO*\n"
            reporte += f"• *Tiempo mínimo de postura:* {postura_min_txt}\n"
            reporte += f"• *Tiempo máximo de postura:* {postura_max_txt}\n"
            reporte += f"• *Tiempo mínimo de salida:* {salida_min_txt}\n"
            reporte += f"• *Tiempo máximo de salida:* {salida_max_txt}\n\n"
            
            # --- CONSOLIDADO POR CLIENTE ---
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
            
            st.success("✅ ¡Reporte generado con éxito!")
            st.text_area("📋 Copia y pega este reporte en WhatsApp:", reporte, height=450)
            
    except Exception as e:
        st.error(f"Error procesando la estructura del archivo: {e}")
