## ---------------------------------

# TurbyCargado -  App en streamlit para calcular el tiempo que tarda en cargar mi auto eléctrico
## Script de utilidades

## Por: Ruben Durango
## Version: 1.0.0
## Fecha: 2024-08-13

## ---------------------------------


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
    # Despejar el tiempo en minutos usando la fórmula de la regresión lineal
    tiempo_minutos = (carga_final - carga_inicial) / pendiente
    return tiempo_minutos