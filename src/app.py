## ---------------------------------

# TurbyCargado -  App en streamlit para calcular el tiempo que tarda en cargar mi auto eléctrico

## Por: Ruben Durango
## Version: 1.0.0
## Fecha: 2024-08-13

## ---------------------------------

# Importar librerías
import streamlit as st
from PIL import Image
from datetime import datetime, timedelta

from utilidades import calcular_tiempo_carga


## ---------------------------------

# Layout de la pagina
st.set_page_config(page_title="TurbyCargado", page_icon="🔋", layout="wide", initial_sidebar_state="expanded")

# Titulos
st.title("🔋 TurbyCargado")
st.subheader("Calcula el tiempo que tarda en cargar Turby")

# Cargando e inicializando variables  --------------

#Carga de secretos
password = st.secrets["general"]["password"]

if "carga_inicial" not in st.session_state:
    st.session_state.carga_inicial = 40
if "carga_final" not in st.session_state:
    st.session_state.carga_final = 80
if "hora_inicial" not in st.session_state:
    st.session_state.hora_inicial = datetime.now().time()
if "tiempo_minutos" not in st.session_state:
    st.session_state.tiempo_minutos = None
if "hora_final" not in st.session_state:
    st.session_state.hora_final = None
if "boton_pulsado" not in st.session_state:
    st.session_state.boton_pulsado = False

# Layout de la app ---------------------------------

## Dos columnas principales
col1, col2 = st.columns(2)

# Columna 1 ----------------------------------------

with col1:
    with st.container(border=True):
        st.session_state.carga_inicial = st.slider("🪫 Carga inicial", 0, 100, st.session_state.carga_inicial)  # De 0 a 100% con valor inicial desde session_state
        st.session_state.carga_final = st.slider("🔋 Carga deseada", 0, 100, st.session_state.carga_final)  # De 0 a 100% con valor inicial desde session_state
        st.session_state.hora_inicial = st.time_input("⌚ Hora inicial", value=st.session_state.hora_inicial)

        # Variable para almacenar si se ha pulsado el botón
        if st.button("Calcular", type="primary", use_container_width=True):
            st.session_state.boton_pulsado = True
            # Calcular el tiempo de carga
            st.session_state.tiempo_minutos = calcular_tiempo_carga(st.session_state.carga_inicial / 100, st.session_state.carga_final / 100, 0.0023662327596904323)
            
            # Calcular la hora final
            st.session_state.hora_final = (datetime.combine(datetime.today(), st.session_state.hora_inicial) + timedelta(minutes=st.session_state.tiempo_minutos)).time()

    # Crear el container para las tarjetas
    with st.container():
        col_a, col_b = st.columns(2)

        if st.session_state.boton_pulsado and st.session_state.tiempo_minutos is not None:
            # Si se ha pulsado el botón, mostramos los resultados

            # Primera tarjeta (Tiempo de carga)
            with col_a:
                st.markdown("""
                <div style="background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #00CED1;">
                    <h6 style="text-align: center;">🔋 Tiempo de carga</h6>
                    <p style="text-align: center; font-size: 28px; color: #00CED1;"><b>{}</b> minutos</p>
                </div>
                """.format(int(st.session_state.tiempo_minutos)), unsafe_allow_html=True)

            # Segunda tarjeta (Hora final)
            with col_b:
                st.markdown("""
                <div style="background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #00CED1;">
                    <h6 style="text-align: center;">✅ Hora final</h6>
                    <p style="text-align: center; font-size: 28px; color: #00CED1;"><b>{}</b></p>
                </div>
                """.format(st.session_state.hora_final.strftime("%I:%M %p")), unsafe_allow_html=True)
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

st.sidebar.image(Image.open("src/images/turby_.png"))
st.sidebar.header("Bievenido a TurbyCargado🔋")
st.sidebar.write("Puedes calcular el tiempo que tardara Turby en cargar. Una vez calcules el ciclo de carga puedes dar clic en inicio")

# Separador
st.sidebar.markdown("---")
 
with st.sidebar.container(border=True):
    with st.popover("✈️ Seguimiento de Carga",  
                    use_container_width=True):
        # Input para la contraseña
        contra = st.text_input("🔐 Introduce tu contraseña:", type="password")
        
        # Verificación de la contraseña
        if contra:
            if contra == password:
                st.success("🔓 Contraseña correcta")
                if st.button("✈️ Iniciar", use_container_width=True, type="primary"):
                    st.write("Notificaciones de carga iniciadas...")
            else:
                st.error("❌ Contraseña incorrecta")
                
with st.sidebar.expander("Importante ℹ️", expanded=False):
    st.markdown("""
    **TurbyCargado** es una herramienta diseñada específicamente para calcular el tiempo que mi auto tarda en cargar. 
    No se garantiza que los resultados sean aplicables a otros vehículos, ya que dependen de múltiples factores como:
    - La potencia del cargador.
    - El tipo de carga del auto.
    - El modelo de vehículo.
    - Entre otras muchas variables.

    Por lo tanto, se recomienda utilizar esta herramienta solo para fines personales 😅 y no como referencia general.
    """)

with st.sidebar.expander("Conéctate conmigo 🤗", expanded=False):
    st.markdown("[![Portafolio](https://img.shields.io/badge/Portafolio-FF5722?style=for-the-badge)](https://rubendurango.com/)")
    st.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/rdurango92/)")
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/rdurango92)")
    st.markdown("[![GitHub Project](https://img.shields.io/badge/Proyecto-GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/rdurango92/TurbyCargado)")