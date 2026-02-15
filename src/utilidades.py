## ---------------------------------

# TurbyCargado -  App en streamlit para calcular el tiempo que tarda en cargar mi auto eléctrico
## Script de utilidades

## Por: Ruben Durango
## Version: 1.0.0
## Fecha: 2024-08-13

## ---------------------------------

import streamlit as st

@st.cache_data
def calcular_tiempo_carga(carga_inicial, carga_final, pendiente):
    """
    Calcula el tiempo en minutos necesario para cargar la batería desde una carga inicial hasta una carga final.

    Parámetros:
    carga_inicial (float): La carga inicial de la batería (entre 0 y 1).
    carga_final (float): La carga deseada de la batería (entre 0 y 1).
    pendiente (float): La pendiente de la regresión lineal.

    Retorna:
    float: El tiempo en minutos necesario para alcanzar la carga final desde la carga inicial.
    """
    if not (0 <= carga_inicial <= 1):
        raise ValueError("La carga inicial debe estar entre 0 y 1.")
    if not (0 <= carga_final <= 1):
        raise ValueError("La carga final debe estar entre 0 y 1.")
    if carga_final <= carga_inicial:
        raise ValueError("La carga final debe ser mayor que la carga inicial.")
    if pendiente <= 0:
        raise ValueError("La pendiente debe ser mayor que 0.")

    # Despejar el tiempo en minutos usando la fórmula de la regresión lineal
    tiempo_minutos = (carga_final - carga_inicial) / pendiente
    return int(round(tiempo_minutos))
