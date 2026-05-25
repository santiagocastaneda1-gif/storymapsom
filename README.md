# 🗺️ StoryMap SOM
## Explorador Visual de Textos mediante Self-Organizing Maps

**Proyecto Final — Computación Blanda**
**Autores:** Santiago Castañeda · Santiago Florez
**Python:** 3.11.9 | **Framework:** Kivy 2.3.0

---

## 📁 Estructura del proyecto

```
storymapsom/
├── main.py                  ← Punto de entrada + UI completa (Kivy)
├── core/
│   ├── __init__.py
│   └── som_engine.py        ← Núcleo IA: SOM + TF-IDF + KMeans
├── buildozer.spec           ← Configuración para compilar en Android
├── requirements.txt         ← Dependencias Python
└── README.md
```

---

## 🧠 Técnica de IA implementada

### Self-Organizing Map (SOM) de Kohonen

El SOM aprende una **proyección topológica 2D** de vectores TF-IDF de alta dimensión, preservando relaciones de similitud semántica entre textos.

**Ecuaciones clave:**

```
Actualización de pesos:
  Δw(t) = η(t) · h(i,t) · (x − w)

Decaimiento de tasa de aprendizaje:
  η(t) = η₀ · exp(−t/λ)

Decaimiento del radio de vecindad:
  σ(t) = σ₀ · exp(−t/λ_σ)

Función de vecindad gaussiana:
  h(i,t) = exp(−d²(bmu,i) / 2σ(t)²)
```

**Pipeline completo:**
1. Tokenización + eliminación de stopwords (ES/EN)
2. Construcción de vocabulario con frecuencia mínima
3. Vectores **TF-IDF** normalizados (L2)
4. Entrenamiento SOM con decaimiento exponencial
5. Asignación de documentos a BMU (Best Matching Unit)
6. Clustering **K-Means** sobre posiciones del mapa
7. U-Matrix para visualizar fronteras de clusters

---

## 📱 Funcionalidades de la app

| Pantalla | Función |
|---|---|
| 🌟 Bienvenida | Presentación animada con partículas |
| 📄 Documentos | Agregar texto manual, cargar .txt, cargar demo |
| 🧠 Entrenar | Configurar grilla, iteraciones, clusters y entrenar |
| 🗺️ Mapa SOM | Visualización 2D del mapa con U-Matrix y leyenda |
| 📊 Análisis | Métricas, curva de convergencia, palabras clave |
| ⚙️ Config | Info teórica, guardar sesión, reiniciar |

---

## 🚀 Ejecución local (PC / prueba)

### 1. Instalar dependencias

```bash
# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Instalar
pip install kivy numpy scikit-learn nltk minisom
```

### 2. Ejecutar

```bash
cd storymapsom/
python main.py
```

---

## 🤖 Compilar para Android con Buildozer

### Requisitos del sistema (Linux recomendado)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk \
    build-essential libssl-dev libffi-dev \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

# Instalar Buildozer
pip install --upgrade buildozer cython==0.29.36
```

### Pasos de compilación

```bash
# 1. Entrar a la carpeta del proyecto
cd storymapsom/

# 2. Inicializar (primera vez)
buildozer init         # Ya está incluido buildozer.spec

# 3. Compilar APK en modo debug
buildozer android debug

# 4. O compilar y desplegar directo al dispositivo (con USB + ADB)
buildozer android debug deploy run

# El APK queda en:
# .buildozer/android/platform/build-armeabi-v7a/dists/storymapsom/bin/
```

### Con Docker (alternativa más sencilla)

```bash
docker run --volume "$(pwd)":/home/user/hostcwd \
  kivy/buildozer android debug
```

---

## 📋 Notas importantes para el entorno

- **Python:** El proyecto fue desarrollado y probado con Python **3.11.9**
- **Kivy:** versión 2.3.0 (compatible con Buildozer Android API 33)
- **minisom:** La app trae su **propia implementación SOM** en `core/som_engine.py` para mayor control y compatibilidad con Buildozer (minisom listado como respaldo)
- **Permisos Android:** `READ_EXTERNAL_STORAGE`, `WRITE_EXTERNAL_STORAGE`

---

## 📄 Demo incluido

La app incluye **12 cuentos clásicos** preintegrados:
Caperucita, Los Tres Cerditos, Blancanieves, Cenicienta, Jack y las Habichuelas, La Sirenita, El Patito Feo, El Gato con Botas, La Bella y la Bestia, Rapunzel, El Flautista de Hamelin, El Principito.

---

## 📊 Rúbrica del proyecto

| Criterio | Implementado |
|---|---|
| Funcionamiento app (25%) | ✅ App funcional completa |
| Uso correcto IA (25%) | ✅ SOM Kohonen + TF-IDF + KMeans |
| Creatividad (15%) | ✅ Visualización U-Matrix + convergencia |
| Interfaz gráfica (10%) | ✅ UI dark theme, partículas, tabs |
| Experimentación (15%) | ✅ Parámetros ajustables, métricas |
| Presentación final (10%) | Pendiente |

---

## 📚 Referencias

- Kohonen, T. (1982). Self-organized formation of topologically correct feature maps. *Biological Cybernetics*, 43, 59–69.
- Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. *Information Processing & Management*, 24(5), 513–523.
