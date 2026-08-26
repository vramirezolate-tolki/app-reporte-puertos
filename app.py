import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io

# Configuración de página
st.set_page_config(
    page_title="Reporte Operacional Puertos Biobío",
    page_icon="🚢",
    layout="centered"
)

st.title("🚢 Generador de Reporte e Infografía")
st.subheader("Operaciones Puertos Biobío")

# 1. Cargar archivo Excel
uploaded_file = st.file_uploader("Sube el archivo Excel (Resumen descargas)", type=["xlsx"])

def generar_imagen_infografia(df_f, fecha_sel, postura_min_txt, postura_max_txt, salida_min_txt, salida_max_txt):
    """Genera una tarjeta gráfica tipo infografía idéntica a la de la muestra."""
    fig, ax = plt.subplots(figsize=(10, 13), dpi=200)
    fig.patch.set_facecolor('#f4f6f9')
    ax.set_facecolor('#f4f6f9')
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 130)

    # Título General
    ax.text(5, 124, f"REPORTE OPERACIONAL - {fecha_sel}", fontsize=16, fontweight='bold', color='#1a365d')

    # --- TARJETA 1: RENDIMIENTO POR PUERTO ---
    rect1 = patches.FancyBboxPatch((5, 82), 43, 38, boxstyle="round,pad=1", ec="#cbd5e1", fc="white", lw=1)
    ax.add_patch(rect1)
    ax.text(8, 116, "⚓ RENDIMIENTO POR PUERTO", fontsize=11, fontweight='bold', color='#1e3a8a')

    # Encabezados de tabla
    ax.text(8, 109, "PUERTO", fontsize=8, fontweight='bold', color='#64748b')
    ax.text(21, 109, "TRENE", fontsize=8, fontweight='bold', color='#64748b')
    ax.text(28, 109, "CUMP. LLEG", fontsize=8, fontweight='bold', color='#64748b')
    ax.text(39, 109, "CUMP. SAL", fontsize=8, fontweight='bold', color='#64748b')

    y_p = 102
    for puerto in df_f['Puerto'].unique():
        sub = df_f[df_f['Puerto'] == puerto]
        c = len(sub)
        ll_p = (sub['Cumple Llegada'] == 'SI').sum() / c * 100
        sl_p = (sub['Cumple Salida Retorno'] == 'SI').sum() / c * 100
        
        ax.text(8, y_p, puerto, fontsize=9, fontweight='bold', color='#1e293b')
        ax.text(23, y_p, str(c), fontsize=9, color='#1e293b')
        
        col_ll = '#16a34a' if ll_p >= 80 else '#d97706' if ll_p >= 50 else '#dc2626'
        col_sl = '#16a34a' if sl_p >= 80 else '#d97706' if sl_p >= 50 else '#dc2626'
        
        ax.text(29, y_p, f"{ll_p:.0f}%", fontsize=9, fontweight='bold', color=col_ll)
        ax.text(40, y_p, f"{sl_p:.0f}%", fontsize=9, fontweight='bold', color=col_sl)
        y_p -= 7.5

    # --- TARJETA 2: CONSOLIDADO POR CLIENTE ---
    rect2 = patches.FancyBboxPatch((5, 38), 43, 38, boxstyle="round,pad=1", ec="#cbd5e1", fc="white", lw=1)
    ax.add_patch(rect2)
    ax.text(8, 72, "🏢 CONSOLIDADO POR CLIENTE", fontsize=11, fontweight='bold', color='#1e3a8a')
    
    y_c = 65
    df_cliente = df_f.groupby('Cliente').agg({'Carros confirmados': 'sum', 'Carros retornos': 'sum'}).reset_index()
    for _, r_c in df_cliente.iterrows():
        cl_name = str(r_c['Cliente'])[:18]
        ax.text(8, y_c, cl_name, fontsize=8, fontweight='bold', color='#334155')
        ax.text(28, y_c, f"{int(r_c['Carros confirmados'])} conf", fontsize=8, color='#64748b')
        ax.text(38, y_c, f"{int(r_c['Carros retornos'])} ret", fontsize=8, fontweight='bold', color='#1e293b')
        y_c -= 5.5

    # --- TARJETA 3: TIEMPOS OPERATIVOS ---
    rect3 = patches.FancyBboxPatch((5, 5), 43, 28, boxstyle="round,pad=1", ec="#cbd5e1", fc="white", lw=1)
    ax.add_patch(rect3)
    ax.text(8, 29, "⏱️ TIEMPOS OPERATIVOS DESTACADOS", fontsize=10, fontweight='bold', color='#1e3a8a')

    # Cajas internas de tiempos
    ax.text(8, 22, "MÍNIMO POSTURA", fontsize=7, fontweight='bold', color='#15803d')
    ax.text(8, 17, posture_min_clean(postura_min_txt), fontsize=10, fontweight='bold', color='#16a34a')
    
    ax.text(28, 22, "MÁXIMO POSTURA", fontsize=7, fontweight='bold', color='#b91c1c')
    ax.text(28, 17, posture_max_clean(postura_max_txt), fontsize=10, fontweight='bold', color='#dc2626')

    ax.text(8, 11, "MÍNIMO SALIDA", fontsize=7, fontweight='bold', color='#15803d')
    ax.text(8, 6, salida_min_clean(salida_min_txt), fontsize=10, fontweight='bold', color='#16a34a')
    
    ax.text(28, 11, "MÁXIMO SALIDA", fontsize=7, fontweight='bold', color='#b91c1c')
    ax.text(28, 6, salida_max_clean(salida_max_txt), fontsize=10, fontweight='bold', color='#dc2626')

    # --- TARJETA 4: NOVEDADES Y DESTACADOS (PANEL DERECHO) ---
    rect4 = patches.FancyBboxPatch((52, 5), 43, 115, boxstyle="round,pad=1", ec="#cbd5e1", fc="white", lw=1)
    ax.add_patch(rect4)
    ax.text(55, 116, "⚠️ NOVEDADES Y DESTACADOS", fontsize=11, fontweight='bold', color='#1e3a8a')

    y_obs = 108
    obs_list = df_f[df_f['Observaciones'].notna()]
    if not obs_list.empty:
        for _, r_o in obs_list.iterrows():
            ax.text(55, y_obs, f"• Tren {r_o['Tren planificado']} ({r_o['Puerto']})", fontsize=8.5, fontweight='bold', color='#0f172a')
            obs_raw = str(r_o['Observaciones']).replace('\n', ' ')
            obs_txt = obs_raw[:110] + "..." if len(obs_raw) > 110 else obs_raw
            ax.text(55, y_obs - 4, obs_txt, fontsize=7.5, color='#475569', wrap=True)
            y_obs -= 16
    else:
        ax.text(55, y_obs, "Sin novedades críticas registradas.", fontsize=8.5, color='#64748b')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

# Helpers de formato de texto
def posture_min_clean(txt): return txt.split('(')[0].strip() if '(' in txt else txt
def posture_max_clean(txt): return txt.split('(')[0].strip() if '(' in txt else txt
def salida_min_clean(txt): return txt.split('(')[0].strip() if '(' in txt else txt
def salida_max_clean(txt): return txt.split('(')[0].strip() if '(' in txt else txt

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='BD_Puerto')
        df['Fecha_Descarga_DT'] = pd.to_datetime(df['Fecha descarga'])
        df['Fecha_Str'] = df['Fecha_Descarga_DT'].dt.strftime('%d/%m/%Y')
        fechas_disponibles = df['Fecha_Str'].unique()
        
        fecha_sel = st.selectbox("📅 Selecciona la fecha de operación:", fechas_disponibles)
        df_f = df[df['Fecha_Str'] == fecha_sel].copy()
        
        if not df_f.empty:
            total_trenes = len(df_f)
            llegada_si = (df_f['Cumple Llegada'] == 'SI').sum()
            salida_si = (df_f['Cumple Salida Retorno'] == 'SI').sum()
            pct_llegada = (llegada_si / total_trenes) * 100
            pct_salida = (salida_si / total_trenes) * 100
            
            confirmados = int(df_f['Carros confirmados'].sum())
            descargados = int(df_f['Carros descargados'].sum())
            retornados = int(df_f['Carros retornos'].sum())
            diferencia = int(df_f['Diferencia Carros Retorno'].sum())
            
            efectividad_descarga = (descargados / confirmados * 100) if confirmados > 0 else 100.0
            
            # Tiempos
            df_f['DT_Arribo_Real'] = pd.to_datetime(df_f['Fecha Hora Llegada Real'])
            df_f['DT_Postura'] = pd.to_datetime(df_f['Postura bodega'])
            df_f['DT_Termino'] = pd.to_datetime(df_f['Término descarga'])
            df_f['DT_Retorno_Real'] = pd.to_datetime(df_f['Fecha Hora Retorno Real'])
            
            def calc_min_diff(end, start):
                if pd.isna(end) or pd.isna(start): return np.nan
                diff = (end - start).total_seconds() / 60.0
                return diff + 1440.0 if diff < 0 else diff

            df_f['Min_Postura'] = df_f.apply(lambda r: calc_min_diff(r['DT_Postura'], r['DT_Arribo_Real']), axis=1)
            df_f['Min_Salida'] = df_f.apply(lambda r: calc_min_diff(r['DT_Retorno_Real'], r['DT_Termino']), axis=1)
            
            df_postura_val = df_f.dropna(subset=['Min_Postura'])
            if not df_postura_val.empty:
                idx_min_pos = df_postura_val['Min_Postura'].idxmin()
                idx_max_pos = df_postura_val['Min_Postura'].idxmax()
                postura_min_txt = f"{df_postura_val.loc[idx_min_pos, 'Min_Postura']:.0f} min (Tren {df_postura_val.loc[idx_min_pos, 'Tren planificado']} - {df_postura_val.loc[idx_min_pos, 'Puerto']})"
                postura_max_txt = f"{df_postura_val.loc[idx_max_pos, 'Min_Postura']:.0f} min (Tren {df_postura_val.loc[idx_max_pos, 'Tren planificado']} - {df_postura_val.loc[idx_max_pos, 'Puerto']})"
            else:
                postura_min_txt, postura_max_txt = "N/I", "N/I"
                
            df_salida_val = df_f.dropna(subset=['Min_Salida'])
            df_salida_val = df_salida_val[df_salida_val['Min_Salida'] < 720]
            if not df_salida_val.empty:
                idx_min_sal = df_salida_val['Min_Salida'].idxmin()
                idx_max_sal = df_salida_val['Min_Salida'].idxmax()
                salida_min_txt = f"{df_salida_val.loc[idx_min_sal, 'Min_Salida']/60:.1f} hrs (Tren {df_salida_val.loc[idx_min_sal, 'Tren planificado']} - {df_salida_val.loc[idx_min_sal, 'Puerto']})"
                salida_max_txt = f"{df_salida_val.loc[idx_max_sal, 'Min_Salida']/60:.1f} hrs (Tren {df_salida_val.loc[idx_max_sal, 'Tren planificado']} - {df_salida_val.loc[idx_max_sal, 'Puerto']})"
            else:
                salida_min_txt, salida_max_txt = "N/I", "N/I"

            # --- TEXTO DE WHATSAPP ---
            reporte = f"*REPORTE EJECUTIVO DE OPERACIONES*\n*Fecha:* {fecha_sel}\n\n"
            reporte += f"📊 *CONSOLIDADO GENERAL*\n• *Total trenes operados:* {total_trenes} trenes\n• *Cumplimiento llegada:* {pct_llegada:.1f}%\n• *Cumplimiento salida (+0):* {pct_salida:.1f}%\n• *Efectividad de descarga:* {efectividad_descarga:.1f}%\n• *Carros confirmados vs. Retorno:* {confirmados} / {retornados} (Dif: {diferencia:+d})\n\n"
            reporte += f"⏱️ *INDICADORES DE TIEMPO OPERATIVO*\n• *Mínimo postura:* {postura_min_txt}\n• *Máximo postura:* {postura_max_txt}\n• *Mínimo salida:* {salida_min_txt}\n• *Máximo salida:* {salida_max_txt}\n\n"
            
            reporte += f"🏭 *CONSOLIDADO POR CLIENTE*\n"
            df_cliente = df_f.groupby('Cliente').agg({'Carros confirmados': 'sum', 'Carros retornos': 'sum'}).reset_index()
            for _, r_c in df_cliente.iterrows():
                reporte += f"• *{r_c['Cliente']}:* {int(r_c['Carros confirmados'])} conf / {int(r_c['Carros retornos'])} ret\n"
            
            reporte += f"\n---\n\n🚢 *DESGLOSE POR PUERTO*\n\n"
            for puerto in df_f['Puerto'].unique():
                sub = df_f[df_f['Puerto'] == puerto]
                c = len(sub)
                lleg_p = (sub['Cumple Llegada'] == 'SI').sum()
                sal_p = (sub['Cumple Salida Retorno'] == 'SI').sum()
                c_conf = int(sub['Carros confirmados'].sum())
                c_ret = int(sub['Carros retornos'].sum())
                c_dif = int(sub['Diferencia Carros Retorno'].sum())
                reporte += f"*{puerto} ({c} trenes)*\n• *Cumplimiento llegada:* {(lleg_p/c)*100:.1f}%\n• *Cumplimiento salida:* {(sal_p/c)*100:.1f}%\n• *Carros:* {c_conf} conf / {c_ret} ret (Dif: {c_dif:+d})\n\n"
            
            obs_list = df_f[df_f['Observaciones'].notna()]
            if not obs_list.empty:
                reporte += f"---\n\n⚠️ *NOVEDADES Y DESTACADOS OPERACIONALES*\n\n"
                for _, r_obs in obs_list.iterrows():
                    obs_clean = str(r_obs['Observaciones']).replace('\n', ' ')
                    reporte += f"• *Tren {r_obs['Tren planificado']} ({r_obs['Puerto']}):* {obs_clean}\n"
            
            # --- INTERFAZ STREAMLIT ---
            tab1, tab2 = st.tabs(["📋 Reporte Texto (WhatsApp)", "🖼️ Infografía Visual (Imagen)"])
            
            with tab1:
                st.text_area("Copia el texto para WhatsApp:", reporte, height=400)
                
            with tab2:
                st.write("### Infografía generada automáticamente:")
                img_buf = generar_imagen_infografia(df_f, fecha_sel, postura_min_txt, postura_max_txt, salida_min_txt, salida_max_txt)
                st.image(img_buf, caption=f"Infografía Operacional {fecha_sel}", use_column_width=True)
                
                # Botón de Descarga de Imagen
                st.download_button(
                    label="📥 Descargar Imagen PNG",
                    data=img_buf,
                    file_name=f"Reporte_Puertos_{fecha_sel.replace('/', '_')}.png",
                    mime="image/png"
                )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
            st.text_area("📋 Copia y pega este reporte en WhatsApp:", reporte, height=450)
            
    except Exception as e:
        st.error(f"Error procesando la estructura del archivo: {e}")
