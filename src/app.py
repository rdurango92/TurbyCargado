## ---------------------------------

# TurbyCargado -  App en streamlit para calcular el tiempo que tarda en cargar mi auto eléctrico

## Por: Ruben Durango
## Version: 1.0.0
## Fecha: 2024-08-13

## ---------------------------------

# Importar librerías
import streamlit as st
from datetime import datetime, timedelta

from utilidades import calcular_tiempo_carga

## ---------------------------------

# Layout de la pagina
st.set_page_config(page_title="TurbyCargado", page_icon="🔋", layout="wide", initial_sidebar_state="expanded")

# Titulos
st.title("🔋 TurbyCargado")
st.subheader("Calcula el tiempo que tarda en cargar tu auto eléctrico")
#st.write("Ingresa los siguientes datos:")

# Layout de la app ---------------------------------

## Dos columnas principales
col1, col2 = st.columns(2)

# Columna 1 ----------------------------------------

with col1:
    with st.container(border=True):
        carga_inicial = st.slider("🪫 Carga inicial", 0, 100, 40)  # De 0 a 100% con valor inicial de 40%
        carga_final = st.slider("🔋 Carga deseada", 0, 100, 80)  # De 0 a 100% con valor inicial de 80%
        hora_inicial = st.time_input("⌚ Hora inicial", value=datetime.now().time())

        # Variable para almacenar si se ha pulsado el botón
        boton_pulsado = st.button("Calcular", type="primary", use_container_width=True)
    
    # Crear el container para las tarjetas
    with st.container():
        col_a, col_b = st.columns(2)

        if boton_pulsado:
            # Si se ha pulsado el botón, calculamos y mostramos los resultados

            # Calcular el tiempo de carga
            tiempo_minutos = calcular_tiempo_carga(carga_inicial / 100, carga_final / 100, 0.0023662327596904323)
            
            # Calcular la hora final
            hora_final = (datetime.combine(datetime.today(), hora_inicial) + timedelta(minutes=tiempo_minutos)).time()

            # Primera tarjeta (Tiempo de carga)
            with col_a:
                st.markdown("""
                <div style="background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #00CED1;">
                    <h6 style="text-align: center;">🔋 Tiempo de carga</h6>
                    <p style="text-align: center; font-size: 28px; color: #00CED1;"><b>{}</b> minutos</p>
                </div>
                """.format(int(tiempo_minutos)), unsafe_allow_html=True)

            # Segunda tarjeta (Hora final)
            with col_b:
                st.markdown("""
                <div style="background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #00CED1;">
                    <h6 style="text-align: center;">✅ Hora final</h6>
                    <p style="text-align: center; font-size: 28px; color: #00CED1;"><b>{}</b></p>
                </div>
                """.format(hora_final.strftime("%I:%M %p")), unsafe_allow_html=True)
        else:
            # Si no se ha pulsado el botón, mostramos un mensaje para que el usuario calcule primero
            with col_a:
                st.markdown("""
                <div style="background-color: #FFFFFF; padding: 16px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #FF6B6B;">
                    <h6 style="text-align: center;">🪫 Tiempo de carga</h6>
                    <p style="text-align: center; font-size: 20px; color: #FF6B6B;">Haz clic en Calcular</p>
                </div>
                """, unsafe_allow_html=True)

            with col_b:
                st.markdown("""
                <div style="background-color: #FFFFFF; padding: 16px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #FF6B6B;">
                    <h6 style="text-align: center;">⛔ Hora final</h6>
                    <p style="text-align: center; font-size: 20px; color: #FF6B6B;">Haz clic en Calcular</p>
                </div>
                """, unsafe_allow_html=True)

# Columna 2 ----------------------------------------

# Barra lateral ------------------------------------

st.sidebar.markdown("Bievenido a TurbyCargado 🚗🔋")
    

