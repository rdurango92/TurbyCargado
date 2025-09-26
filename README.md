# 🔋 TurbyCargado

**Calculadora Personal de Tiempo de Carga para Vehículos Eléctricos**

TurbyCargado es una aplicación web desarrollada en Streamlit que permite calcular con precisión el tiempo de carga del vehículo eléctrico Changan Lumin (cariñosamente llamado "Turby"). La aplicación utiliza análisis de regresión basado en datos históricos reales de carga para proporcionar estimaciones personalizadas y precisas.

![TurbyCargado Banner](src/images/turby_.png)

## ✨ Características Principales

- 📊 **Cálculo Preciso**: Utiliza regresión lineal basada en datos históricos reales
- 🎯 **Personalización**: Ajustes específicos para el comportamiento de carga de Turby
- 📱 **Interfaz Intuitiva**: Aplicación web fácil de usar construida con Streamlit
- 📈 **Visualización**: Gráficos interactivos con Plotly para mostrar el progreso de carga
- ⏰ **Planificación**: Calcula tanto el tiempo de carga como la hora estimada de finalización
- 🔐 **Seguimiento**: Sistema de notificaciones protegido por contraseña
- 📊 **Análisis de Datos**: Notebook Jupyter incluido con análisis completo

## 🚗 ¿Qué es Turby?

Turby es un **Changan Lumin**, un vehículo eléctrico compacto y eficiente. Esta aplicación está específicamente calibrada para las características de carga de este modelo, utilizando datos reales recopilados durante múltiples ciclos de carga.

## 🛠️ Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/rdurango92/TurbyCargado.git
   cd TurbyCargado
   ```

2. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura los secretos** (opcional para seguimiento):
   - Crea un archivo `.streamlit/secrets.toml`
   - Añade tu contraseña para el sistema de seguimiento:
     ```toml
     [general]
     password = "tu_contraseña_aquí"
     ```

4. **Ejecuta la aplicación**:
   ```bash
   streamlit run src/app.py
   ```

5. **Abre tu navegador** y ve a `http://localhost:8501`

## 🎯 Cómo Usar

### Calculadora de Carga

1. **Configura los parámetros**:
   - **Carga Inicial**: Porcentaje actual de batería (0-100%)
   - **Carga Final**: Porcentaje deseado de batería (0-100%)
   - **Hora de Inicio**: Momento en que comenzará la carga

2. **Haz clic en "Calcular"** para obtener:
   - Tiempo estimado de carga en minutos
   - Hora estimada de finalización
   - Visualización del progreso

3. **Interpretación de Resultados**:
   - Los cálculos se basan en una pendiente de regresión de ~0.0024 carga/minuto
   - Los resultados son específicos para las condiciones de Turby

### Sistema de Seguimiento (Opcional)

- Utiliza la contraseña configurada para acceder al seguimiento de carga
- Recibe notificaciones sobre el progreso de la carga

## 📁 Estructura del Proyecto

```
TurbyCargado/
├── src/
│   ├── app.py              # Aplicación principal de Streamlit
│   ├── utilidades.py       # Funciones auxiliares
│   └── images/
│       └── turby_.png      # Imagen de Turby
├── data/
│   └── cargas.csv          # Datos históricos de carga
├── notebooks/
│   └── analisis_ciclos_de_carga.ipynb  # Análisis de datos
├── requirements.txt        # Dependencias del proyecto
├── LICENSE                # Licencia MIT
└── README.md              # Este archivo
```

## 📊 Análisis de Datos

El proyecto incluye un completo análisis de los ciclos de carga en el notebook `notebooks/analisis_ciclos_de_carga.ipynb` que incluye:

- **Análisis Exploratorio**: Visualización de patrones de carga
- **Regresión Lineal**: Modelado del comportamiento de carga
- **Validación del Modelo**: Métricas de precisión (R² > 0.99)
- **Visualizaciones**: Gráficos detallados de los ciclos de carga

## 🔬 Metodología Técnica

### Modelo de Regresión

La aplicación utiliza un modelo de regresión lineal simple:

```
Carga(t) = Pendiente × Tiempo + Intercepto
```

- **Pendiente**: ~0.0024 (carga por minuto)
- **R²**: >0.99 (excelente ajuste)
- **Datos**: Basado en múltiples ciclos de carga reales

### Tecnologías Utilizadas

- **Streamlit**: Framework de aplicaciones web
- **Pandas**: Manipulación y análisis de datos
- **NumPy**: Computación numérica
- **Plotly**: Visualizaciones interactivas
- **Matplotlib/Seaborn**: Gráficos estáticos
- **scikit-learn**: Modelado de machine learning

## ⚠️ Importante: Limitaciones y Disclaimer

**TurbyCargado** está diseñado específicamente para el vehículo Changan Lumin del autor. Los resultados **NO SE GARANTIZA** que sean aplicables a otros vehículos, ya que dependen de múltiples factores:

- 🔌 La potencia del cargador utilizado
- 🚗 El tipo y modelo específico del vehículo
- 🌡️ Condiciones ambientales (temperatura)
- 🔋 Estado y antigüedad de la batería
- ⚡ Tipo de carga (AC/DC, lenta/rápida)

**Recomendación**: Utilizar esta herramienta solo para **fines personales** y como **referencia general**, no como base para decisiones críticas de tiempo.

## 👨‍💻 Autor

**Ruben Durango**
- 🌐 [Portafolio Personal](https://rubendurango.com/)
- 💼 [LinkedIn](https://www.linkedin.com/in/rdurango92/)
- 🐱 [GitHub](https://github.com/rdurango92)

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si tienes ideas para mejorar la aplicación o encontraste un bug:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 🎯 Roadmap Futuro

- [ ] Soporte para múltiples modelos de vehículos
- [ ] Integración con APIs de clima para ajustes por temperatura
- [ ] Notificaciones push móviles
- [ ] Histórico de cargas y estadísticas
- [ ] Modo oscuro para la interfaz
- [ ] API REST para integraciones externas

## 📝 Changelog

### v1.0.0 (2024-08-13)
- ✨ Lanzamiento inicial de TurbyCargado
- 📊 Calculadora de tiempo de carga
- 📈 Visualizaciones con Plotly
- 🔐 Sistema de seguimiento protegido
- 📓 Notebook de análisis incluido

---

<div align="center">
  <p><strong>¡Hecho con ❤️ para la comunidad de vehículos eléctricos!</strong></p>
  <p><em>TurbyCargado - Porque cada minuto cuenta cuando se trata de movilidad sostenible 🌱</em></p>
</div>
