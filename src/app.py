## ---------------------------------
# TurbyCargado - App en streamlit para calcular tiempo de carga
## ---------------------------------

import logging
from datetime import datetime, time, timedelta, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from services.notifications import (
    NotificationError,
    build_start_message,
    send_telegram_message,
)
from services.storage import (
    ChargeCycleCreate,
    NotificationJob,
    create_storage_from_turso,
)
from services.time_ui import (
    add_minutes_to_time,
    combine_today_with_time,
    did_cross_midnight,
    format_datetime_12h,
    format_time_12h,
    from_utc_iso_to_local,
    get_timezone,
    round_time_to_step,
)
from utilidades import calcular_tiempo_carga


SLOPE = 0.0023662327596904323
LOGGER = logging.getLogger("turbycargado")


def _get_secret(section: str, key: str, default: str | None = None) -> str | None:
    try:
        section_data = st.secrets.get(section, {})
    except Exception:
        section_data = {}

    if isinstance(section_data, dict):
        return section_data.get(key, default)

    try:
        return section_data[key]
    except Exception:
        return default


@st.cache_resource(show_spinner=False)
def _get_storage(url: str, auth_token: str):
    return create_storage_from_turso(url=url, auth_token=auth_token)


def _sync_time_state(timezone_name: str) -> None:
    start_local_dt = combine_today_with_time(st.session_state.hora_inicial, timezone_name)
    end_local_dt = start_local_dt + timedelta(minutes=int(st.session_state.tiempo_minutos))
    st.session_state.start_local_dt = start_local_dt
    st.session_state.end_local_dt = end_local_dt
    st.session_state.hora_final = end_local_dt.time()
    st.session_state.cross_midnight = did_cross_midnight(start_local_dt, end_local_dt)


def _init_session_state(timezone_name: str) -> None:
    now_local = datetime.now(get_timezone(timezone_name))
    default_start_time = round_time_to_step(now_local.time(), step_minutes=5)

    if "carga_inicial" not in st.session_state:
        st.session_state.carga_inicial = 40
    if "carga_final" not in st.session_state:
        st.session_state.carga_final = 80
    if "hora_inicial" not in st.session_state:
        st.session_state.hora_inicial = default_start_time
    if "tiempo_minutos" not in st.session_state:
        st.session_state.tiempo_minutos = 170
    if "boton_pulsado" not in st.session_state:
        st.session_state.boton_pulsado = False
    if "cross_midnight" not in st.session_state:
        st.session_state.cross_midnight = False
    if "last_cycle_id" not in st.session_state:
        st.session_state.last_cycle_id = None

    _sync_time_state(timezone_name=timezone_name)


def _apply_quick_time(minutes_offset: int, timezone_name: str) -> None:
    now_local = datetime.now(get_timezone(timezone_name))
    quick_time = add_minutes_to_time(now_local.time(), minutes_offset)
    st.session_state.hora_inicial = round_time_to_step(quick_time, step_minutes=5)
    _sync_time_state(timezone_name=timezone_name)


def _build_history_dataframe(cycles: list[dict], timezone_name: str) -> pd.DataFrame:
    rows = []
    for cycle in cycles:
        cycle_timezone = cycle.get("timezone") or timezone_name
        start_local = from_utc_iso_to_local(cycle["start_at_utc"], cycle_timezone)
        end_local = from_utc_iso_to_local(cycle["end_at_utc"], cycle_timezone)
        rows.append(
            {
                "Inicio": format_datetime_12h(start_local),
                "Fin estimado": format_datetime_12h(end_local),
                "SOC inicial (%)": int(cycle["start_soc"]),
                "SOC objetivo (%)": int(cycle["target_soc"]),
                "Minutos estimados": int(cycle["estimated_minutes"]),
                "Estado": cycle["status"],
            }
        )
    return pd.DataFrame(rows)


# Layout de la pagina
st.set_page_config(
    page_title="TurbyCargado",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔋 TurbyCargado")
st.subheader("Calcula el tiempo que tarda en cargar Turby")

# Secretos/configuracion
password = _get_secret("general", "password")
timezone_name = _get_secret("general", "timezone", "UTC") or "UTC"
turso_url = _get_secret("turso", "url")
turso_auth_token = _get_secret("turso", "auth_token")
telegram_bot_token = _get_secret("telegram", "bot_token")
telegram_chat_id = _get_secret("telegram", "chat_id")

_init_session_state(timezone_name=timezone_name)

storage = None
storage_error = None
if turso_url and turso_auth_token:
    try:
        storage = _get_storage(turso_url, turso_auth_token)
    except Exception as exc:
        storage_error = str(exc)
        LOGGER.exception("storage_init_failed")

# Layout principal
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.session_state.carga_inicial = st.slider(
            "🪫 Carga inicial",
            0,
            100,
            st.session_state.carga_inicial,
        )
        st.session_state.carga_final = st.slider(
            "🔋 Carga deseada",
            0,
            100,
            st.session_state.carga_final,
        )

        quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
        if quick_col1.button("Ahora", width="stretch"):
            _apply_quick_time(minutes_offset=0, timezone_name=timezone_name)
        if quick_col2.button("+15 min", width="stretch"):
            _apply_quick_time(minutes_offset=15, timezone_name=timezone_name)
        if quick_col3.button("+30 min", width="stretch"):
            _apply_quick_time(minutes_offset=30, timezone_name=timezone_name)
        if quick_col4.button("+60 min", width="stretch"):
            _apply_quick_time(minutes_offset=60, timezone_name=timezone_name)

        st.session_state.hora_inicial = st.slider(
            "⌚ Hora inicial",
            min_value=time(0, 0),
            max_value=time(23, 55),
            value=st.session_state.hora_inicial,
            step=timedelta(minutes=5),
        )
        st.caption(f"Hora seleccionada: {format_time_12h(st.session_state.hora_inicial)}")

        invalid_soc = st.session_state.carga_final <= st.session_state.carga_inicial
        if invalid_soc:
            st.warning("La carga deseada debe ser mayor que la carga inicial.")

        if st.button(
            "Calcular",
            type="primary",
            width="stretch",
            disabled=invalid_soc,
        ):
            try:
                st.session_state.tiempo_minutos = calcular_tiempo_carga(
                    st.session_state.carga_inicial / 100,
                    st.session_state.carga_final / 100,
                    SLOPE,
                )
                st.session_state.boton_pulsado = True
                _sync_time_state(timezone_name=timezone_name)
            except ValueError as exc:
                st.session_state.boton_pulsado = False
                st.error(str(exc))

    with st.container():
        col_a, col_b = st.columns(2)
        if st.session_state.boton_pulsado and st.session_state.tiempo_minutos is not None:
            cross_day_text = " (+1 dia)" if st.session_state.cross_midnight else ""
            with col_a:
                st.markdown(
                    """
                    <div style="background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #00CED1;">
                        <h6 style="text-align: center;">🔋 Tiempo de carga</h6>
                        <p style="text-align: center; font-size: 28px; color: #00CED1;"><b>{}</b> minutos</p>
                    </div>
                    """.format(int(st.session_state.tiempo_minutos)),
                    unsafe_allow_html=True,
                )
            with col_b:
                st.markdown(
                    """
                    <div style="background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #00CED1;">
                        <h6 style="text-align: center;">✅ Hora final</h6>
                        <p style="text-align: center; font-size: 28px; color: #00CED1;"><b>{}</b>{}</p>
                    </div>
                    """.format(format_time_12h(st.session_state.hora_final), cross_day_text),
                    unsafe_allow_html=True,
                )
        else:
            with col_a:
                st.markdown(
                    """
                    <div style="background-color: #FFFFFF; padding: 16px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #FF6B6B;">
                        <h6 style="text-align: center;">🪫 Tiempo de carga</h6>
                        <p style="text-align: center; font-size: 20px; color: #FF6B6B;">Haz clic en Calcular</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_b:
                st.markdown(
                    """
                    <div style="background-color: #FFFFFF; padding: 16px; border-radius: 10px; border: 1px solid #cccccc; border-left: 8px solid #FF6B6B;">
                        <h6 style="text-align: center;">⛔ Hora final</h6>
                        <p style="text-align: center; font-size: 20px; color: #FF6B6B;">Haz clic en Calcular</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

with col2:
    with st.container(border=True):
        tiempo_plot = max(int(st.session_state.tiempo_minutos), 1)
        tiempos = np.linspace(0, tiempo_plot, num=50)
        cargas = np.linspace(st.session_state.carga_inicial, st.session_state.carga_final, num=50)

        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(
                x=tiempos,
                y=cargas,
                fill="tozeroy",
                fillcolor="rgba(0, 206, 209, 0.3)",
                mode="lines",
                line={"color": "#00CED1"},
                name="Proceso de Carga",
                hovertemplate="<b>Tiempo:</b> %{x:.0f} minutos<br><b>Carga:</b> %{y:.0f}%<extra></extra>",
            )
        )
        fig1.update_layout(
            xaxis_title="Tiempo (minutos)",
            yaxis_title="Carga (%)",
            margin={"l": 20, "r": 20, "t": 30, "b": 20},
            height=320,
            hovermode="closest",
        )
        st.plotly_chart(fig1, width="stretch")

    with st.container(border=True):
        eventos = ["Inicio", "25%", "50%", "75%", "Fin"]
        inicio = st.session_state.start_local_dt
        tiempo_total = int(st.session_state.tiempo_minutos)
        tiempos_eventos_dt = [
            inicio,
            inicio + timedelta(minutes=tiempo_total * 0.25),
            inicio + timedelta(minutes=tiempo_total * 0.5),
            inicio + timedelta(minutes=tiempo_total * 0.75),
            st.session_state.end_local_dt,
        ]
        tiempos_eventos = [format_time_12h(dt.time()) for dt in tiempos_eventos_dt]

        fig2 = go.Figure()
        for evento, tiempo_txt, carga, minutos in zip(
            eventos,
            tiempos_eventos,
            [
                st.session_state.carga_inicial,
                int(st.session_state.carga_inicial + (st.session_state.carga_final - st.session_state.carga_inicial) * 0.25),
                int(st.session_state.carga_inicial + (st.session_state.carga_final - st.session_state.carga_inicial) * 0.5),
                int(st.session_state.carga_inicial + (st.session_state.carga_final - st.session_state.carga_inicial) * 0.75),
                st.session_state.carga_final,
            ],
            [0, tiempo_total * 0.25, tiempo_total * 0.5, tiempo_total * 0.75, tiempo_total],
        ):
            fig2.add_trace(
                go.Scatter(
                    x=[tiempo_txt],
                    y=[0],
                    mode="markers+text",
                    marker={"size": 12, "color": "#00CED1"},
                    text=[evento],
                    textposition="top center",
                    hovertemplate=f"<b>Hora:</b> {tiempo_txt}<br><b>Minutos:</b> {int(minutos)} min<br><b>Carga:</b> {int(carga)}%<extra></extra>",
                    name=evento,
                )
            )

        fig2.add_trace(
            go.Scatter(
                x=tiempos_eventos,
                y=[0, 0, 0, 0, 0],
                mode="lines",
                line={"color": "#00CED1", "width": 3},
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig2.update_layout(
            xaxis_title=None,
            yaxis={"showticklabels": False},
            margin={"l": 10, "r": 10, "t": 0, "b": 0},
            height=110,
            hovermode="closest",
            showlegend=False,
        )
        st.plotly_chart(fig2, width="stretch")

# Sidebar
st.sidebar.image(Image.open("src/images/turby_.png"))
st.sidebar.header("Bienvenido a TurbyCargado🔋")
st.sidebar.write(
    "Calcula el tiempo de carga y, si quieres, inicia un seguimiento con notificaciones."
)
st.sidebar.markdown("---")

with st.sidebar.container(border=True):
    with st.popover("✈️ Seguimiento de Carga", width="stretch"):
        access_granted = True
        if password:
            entered_password = st.text_input("🔐 Introduce tu contraseña:", type="password")
            if entered_password:
                if entered_password == password:
                    st.success("🔓 Contraseña correcta")
                else:
                    access_granted = False
                    st.error("❌ Contraseña incorrecta")
            else:
                access_granted = False
        else:
            st.caption("Sin contraseña configurada (general.password no definido).")

        tracking_ready = bool(storage) and bool(telegram_bot_token and telegram_chat_id)
        if storage_error:
            st.warning(f"Base de datos no disponible: {storage_error}")
        elif not storage:
            st.warning("Configura [turso] en secrets para guardar ciclos.")

        if not (telegram_bot_token and telegram_chat_id):
            st.warning("Configura [telegram] bot_token y chat_id para notificaciones.")

        start_tracking_disabled = not (
            st.session_state.boton_pulsado and access_granted and tracking_ready
        )

        if st.button(
            "✈️ Iniciar seguimiento",
            width="stretch",
            type="primary",
            disabled=start_tracking_disabled,
        ):
            try:
                cycle_payload = ChargeCycleCreate(
                    start_soc=int(st.session_state.carga_inicial),
                    target_soc=int(st.session_state.carga_final),
                    start_at_local=st.session_state.start_local_dt,
                    timezone=timezone_name,
                    estimated_minutes=int(st.session_state.tiempo_minutos),
                )
                saved_cycle = storage.insert_cycle(cycle=cycle_payload, slope=SLOPE)
                start_job_id = storage.insert_notification_job(
                    NotificationJob(
                        cycle_id=saved_cycle["id"],
                        event_type="start",
                        scheduled_at_utc=datetime.now(timezone.utc),
                    )
                )
                storage.insert_notification_job(
                    NotificationJob(
                        cycle_id=saved_cycle["id"],
                        event_type="end",
                        scheduled_at_utc=saved_cycle["end_at_utc"],
                    )
                )

                try:
                    message = build_start_message(
                        start_local=saved_cycle["start_at_local"],
                        end_local=saved_cycle["end_at_local"],
                        start_soc=saved_cycle["start_soc"],
                        target_soc=saved_cycle["target_soc"],
                    )
                    send_telegram_message(
                        bot_token=telegram_bot_token,
                        chat_id=telegram_chat_id,
                        text=message,
                    )
                    storage.mark_job_sent(job_id=start_job_id)
                    st.success("Seguimiento iniciado y notificacion de inicio enviada.")
                except NotificationError as exc:
                    LOGGER.error("telegram_start_failed error=%s", exc)
                    st.warning(
                        "El ciclo se guardo, pero no se envio el mensaje inmediato. "
                        "El worker programado reintentara."
                    )

                st.session_state.last_cycle_id = saved_cycle["id"]
            except Exception as exc:
                LOGGER.exception("start_tracking_failed")
                st.error(f"No se pudo iniciar seguimiento: {exc}")

with st.sidebar.expander("Importante ℹ️", expanded=False):
    st.markdown(
        """
    **TurbyCargado** esta calibrado para mi Changan Lumin.
    Los resultados pueden variar en otros autos por factores como potencia del cargador,
    tipo de bateria, temperatura y condiciones de carga.
    """
    )

with st.sidebar.expander("Conectate conmigo 🤗", expanded=False):
    st.markdown("[![Portafolio](https://img.shields.io/badge/Portafolio-FF5722?style=for-the-badge)](https://rubendurango.com/)")
    st.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/rdurango92/)")
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/rdurango92)")
    st.markdown("[![GitHub Project](https://img.shields.io/badge/Proyecto-GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/rdurango92/TurbyCargado)")

# Historial de ciclos
st.markdown("---")
st.subheader("Historial de ciclos")
if not storage:
    st.info("Configura Turso para habilitar persistencia e historial de ciclos.")
else:
    try:
        recent_cycles = storage.list_recent_cycles(limit=30)
    except Exception as exc:
        LOGGER.exception("history_query_failed")
        st.error(f"No se pudo leer el historial: {exc}")
        recent_cycles = []

    if recent_cycles:
        history_df = _build_history_dataframe(recent_cycles, timezone_name=timezone_name)
        st.dataframe(history_df, width="stretch", hide_index=True)
        st.download_button(
            "Descargar historial (CSV)",
            data=history_df.to_csv(index=False).encode("utf-8"),
            file_name="turby_historial_ciclos.csv",
            mime="text/csv",
            width="stretch",
        )
    else:
        st.info("Aun no hay ciclos guardados.")
