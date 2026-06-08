# 🤖 Agente de Ofertas Inteligente (AgenteOfertas)

Este proyecto es un **Agente de Inteligencia Artificial** personal escrito en Python que se encarga de monitorear y comparar los precios de tus productos favoritos en múltiples tiendas en línea (incluyendo **Amazon.com**, **eBay**, **AliExpress** y soporte para **MercadoLibre**).

El agente se ejecuta de manera automatizada a través de **GitHub Actions** (o localmente), consolida los precios en una base de datos histórica (`history.json`), envía alertas instantáneas a tu celular mediante **Telegram** cuando detecta un precio mínimo, y genera un **Dashboard interactivo en HTML** alojado de forma gratuita en **GitHub Pages**.

---

## ✨ Características

*   **Conversión de Moneda en Tiempo Real:** Convierte precios de USD y EUR a Pesos Colombianos (COP) usando el tipo de cambio oficial actualizado en cada ejecución.
*   **Filtros Inteligentes (Anti-Ruido):** Evita falsos positivos filtrando automáticamente accesorios (fundas, cables, etc.) usando reglas de exclusión semántica y umbrales de precio mínimos.
*   **Monitoreo Histórico:** Registra el historial de precios de cada producto para identificar si la oferta actual representa un verdadero bajo histórico.
*   **Alertas Instantáneas por Telegram:** Recibe notificaciones con el precio, la comparativa frente a otras tiendas, imágenes y el enlace directo de compra.
*   **Dashboard Moderno con Gráficas:** Un reporte visual con efectos de glassmorphic que incluye gráficos interactivos de líneas de tiempo de precios alimentados por **Chart.js**.

---

## 📁 Estructura del Repositorio

*   `agent/`: Código fuente del agente.
    *   `scrapers/`: Módulos de extracción de datos para Amazon, eBay, AliExpress y MercadoLibre.
    *   `currency.py`: Conversor de divisas.
    *   `analyzer.py`: Filtro inteligente de palabras excluyentes y rango de precios.
    *   `notifier.py`: Formateo y envío de alertas a Telegram.
    *   `report.py`: Generador del dashboard.
    *   `main.py`: Punto de entrada del script.
*   `templates/`: Plantilla HTML del reporte visual.
*   `docs/`: Contiene el dashboard compilado (`index.html`) listo para ser servido por GitHub Pages.
*   `config.json`: Archivo de configuración principal donde defines los productos a monitorear.
*   `history.json`: Base de datos local de historial de precios (auto-actualizada).
*   `.github/workflows/run_agent.yml`: Workflow para ejecutar el agente automáticamente en la nube de GitHub.

---

## 🚀 Configuración y Uso Local

### 1. Requisitos Previos
Tener instalado **Python 3.8+**.

### 2. Instalación
Crea un entorno virtual e instala las dependencias necesarias:

```bash
# Crear entorno virtual
python -m venv venv

# Activar el entorno virtual
# En Windows (PowerShell):
.\venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Ejecución del Agente
Para correr el agente de forma manual por primera vez:

```bash
python -m agent.main
```

Esto generará el historial inicial en `history.json` y compilará el reporte HTML en `docs/index.html`.

---

## ⚙️ Automatización con GitHub Actions y GitHub Pages

Para que el agente trabaje para ti las 24 horas del día de manera gratuita, configúralo en tu repositorio de GitHub:

### Paso 1: Configurar los Secretos en GitHub (Secrets)
Ve a tu repositorio en GitHub y dirígete a: **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**. Añade los siguientes secretos:

1.  **`TELEGRAM_BOT_TOKEN`**: El token de tu Bot de Telegram.
    *   *¿Cómo obtenerlo?* Habla con [@BotFather](https://t.me/BotFather) en Telegram, crea un bot usando `/newbot` y copia el token proporcionado.
2.  **`TELEGRAM_CHAT_ID`**: Tu ID de chat de Telegram para saber a dónde enviar el mensaje.
    *   *¿Cómo obtenerlo?* Inicia una conversación con tu bot recién creado (presiona `/start`). Luego, habla con [@userinfobot](https://t.me/userinfobot) y copia el "ID" que te muestre.
3.  **`MERCADOLIBRE_ACCESS_TOKEN`** (Opcional): Si deseas usar la API de MercadoLibre, genera un Access Token personal desde tu panel de desarrollador en [Mercado Libre Developers](https://developers.mercadolibre.com/).
4.  **`GEMINI_API_KEY`** (Opcional): Si deseas habilitar filtros adicionales basados en IA semántica de Google Gemini para afinar la coincidencia de productos.

### Paso 2: Activar GitHub Pages para el Dashboard
1.  Ve a **Settings** -> **Pages** en tu repositorio de GitHub.
2.  En **Build and deployment** -> **Source**, selecciona **Deploy from a branch**.
3.  En **Branch**, selecciona tu rama principal (ej. `master` o `main`) y la carpeta `/docs`.
4.  Presiona **Save**.
5.  ¡Listo! En unos minutos, podrás acceder a tu dashboard de ofertas en: `https://<tu-usuario>.github.io/<tu-repositorio>/`.

### Paso 3: Push a tu Repositorio
Asegúrate de agregar la dirección remota de tu repositorio de GitHub y subir los cambios:

```bash
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

A partir de este momento, GitHub Actions ejecutará tu agente cada 12 horas de forma automática, actualizará tu Dashboard en GitHub Pages y te enviará un mensaje de Telegram si encuentra una oferta imperdible.

---

## 🎯 ¿Cómo personalizar mis productos?

Abre el archivo `config.json` y edita o agrega objetos en la lista `"products"`. 

```json
{
  "name": "Nombre de Producto Visual",
  "search_queries": ["búsqueda exacta 1", "búsqueda exacta 2"],
  "max_price_cop": 1500000, // Precio máximo que estás dispuesto a pagar en COP
  "min_price_cop": 400000,  // Filtra ofertas sospechosamente baratas (accesorios)
  "exclude_words": ["funda", "estuche", "vidrio", "protector"] // Evita falsos positivos
}
```
