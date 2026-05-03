# 🤖 Bot de Finanzas Personales con IA (PocketFlow + DeepSeek)

Un bot inteligente y multimodal para Telegram que te ayuda a llevar un control de tus finanzas personales de manera sencilla y conversacional. Registra gastos e ingresos, consulta resúmenes, define presupuestos y recibe alertas.

Ahora con **Visión Computacional**: ¡Simplemente envía una foto de tu ticket y el bot hará el resto!

## ✨ Características Principales

*   ✅ **Registro de Transacciones:** Añade gastos e ingresos al instante.
*   📸 **Escaneo de Recibos (NUEVO):** Envía una foto de una factura, ticket o cuenta. La IA "leerá" la imagen, extraerá los ítems, el total y clasificará el gasto automáticamente.
*   📄 **Exportar a PDF (NUEVO):** Descarga un reporte financiero en PDF con resumen y breakdown por categoría.
*   🗣️ **Soporte Multimodal:** Envía mensajes de **texto** o **notas de voz** para registrar tus transacciones.
*   🧠 **Inteligencia Contextual:** Utiliza **DeepSeek (API compatible OpenAI)** para entender lenguaje natural, jerga local, fechas relativas ("ayer", "el mes pasado") y analizar imágenes.
*   📊 **Resúmenes Financieros:** Pide reportes por períodos flexibles ("hoy", "últimos 15 días") y recibe análisis mensuales automáticos con insights sobre tus hábitos.
*   🎯 **Gestión de Presupuestos:** Define límites mensuales por categoría y recibe **alertas proactivas** si estás por excederte.
*   🔍 **Consultas Detalladas:** Pregunta por gastos específicos ("¿cuánto gasté en Uber este mes?").
*   ☁️ **Google Sheets:** Todo se guarda en tu hoja de cálculo personal, manteniendo tus datos seguros y accesibles.
*   🛠️ **Arquitectura Agéntica:** Construido sobre **PocketFlow**, con una separación clara entre lógica de flujo, nodos de ejecución y prompts de IA.

## ⚙️ ¿Cómo Funciona? (Arquitectura)

El proyecto utiliza el framework **PocketFlow**, organizando la lógica en **Nodos** independientes.

1.  **Recepción:** `GetMessageNode` detecta si el mensaje es Texto, Audio, Foto o un Botón.
2.  **Procesamiento de Entrada:**
    *   🎤 **Audio:** `TranscribeAudioNode` convierte voz a texto.
    *   📸 **Foto:** `AnalyzeReceiptNode` usa visión computacional para extraer datos del ticket.
    *   💬 **Texto:** Pasa directamente al detector de intención.
3.  **Cerebro (Router):** `DetectIntentNode` decide qué quiere hacer el usuario (registrar, consultar, editar, etc.) y deriva al nodo correspondiente.
4.  **Ejecución:** Los nodos específicos interactúan con Google Sheets o generan respuestas.
5.  **Prompts Desacoplados:** Toda la "personalidad" e instrucciones para la IA viven en `utils/prompts.py`, facilitando la iteración sin tocar el código.

### Diagrama del Flujo

```mermaid
flowchart TD
    subgraph "Entrada del Usuario"
        A[Mensaje Nuevo] --> B(GetMessageNode);
    end

    B --> C{¿Tipo de Mensaje?};
    C -- Texto/Botón --> E[DetectIntentNode];
    C -- Audio --> D[TranscribeAudioNode];
    C -- Foto --> Z[AnalyzeReceiptNode];
    
    D --> E;

    subgraph "Ramas de Acción"
        E -- REGISTRAR_GASTO --> F[ParseExpenseListNode];
        E -- REGISTRAR_INGRESO --> G[ParseIncomeNode];
        E -- CONSULTAR_GASTOS --> H[FetchSheetDataNode];
        E -- DEFINIR_PRESUPUESTO --> I[ParseBudgetNode];
        E -- CONSULTAR_PRESUPUESTO --> J[QueryBudgetNode];
        E -- AGREGAR_CATEGORIA --> Q[AddCategoryNode];
        E -- CONSULTAR_POR_CATEGORIA --> R[QueryExpensesByCategoryNode];
        E -- EDITAR/ELIMINAR --> U[Edit/Delete Nodes];
        E -- AYUDA/OTRO --> T[Help/Fallback Nodes];
    end

    subgraph "Procesamiento y Salida"
        Z --> K[ProcessTransactionBatchNode];
        F --> K;
        G --> K;
        K -- Alerta Presupuesto --> L[Notificación];
        H --> M[FormatSummaryNode] --> N[SendSummaryNode];
        I --> O[SetBudgetNode];
    end
```

## 📖 Guía de Uso y Ejemplos

#### 1. Escaneo de Recibos (📸 Nuevo)
Simplemente toma una foto a tu ticket de compra y envíala al chat. No hace falta escribir nada.

| Acción | Resultado |
| :--- | :--- |
| *[Envías una foto de un ticket de supermercado]* | `Gasto Registrado ✅`<br>`📅 Fecha: 2024-01-15`<br>`💰 Monto: 15450.00 PESOS`<br>`🏷️ Categoría: Alimentos`<br>`📝 Descripción: Compra Supermercado` |

#### 2. Registrar Gastos (Texto o Voz)
Puedes registrar múltiples gastos en una sola frase. Además, puedes especificar fechas relativas como "ayer", "anteayer" o "el lunes".

| Comando | Respuesta |
| :--- | :--- |
| `Gaste 5000 en un cafe y 12000 en nafta` | `Gasto Registrado ✅ (Salidas)`<br>`Gasto Registrado ✅ (Auto)` |
| `ayer gaste 1000 en nafta` | `Gasto Registrado ✅`<br>`📅 Fecha: 2024-01-14`<br>`💰 Monto: 1000 PESOS`<br>`🏷️ Categoría: Auto` |
| `anteayer cargue nafta por 15000` | `Gasto Registrado ✅`<br>`📅 Fecha: 2024-01-13`<br>`💰 Monto: 15000 PESOS`<br>`🏷️ Categoría: Auto` |
| 🎙️ *"Cargué 20 mil de sube"* | `Gasto Registrado ✅`<br>`📅 Fecha: 2024-01-15`<br>`💰 Monto: 20000.0 PESOS`<br>`🏷️ Categoría: Transporte` |

#### 3. Consultas y Resúmenes

| Comando | Respuesta |
| :--- | :--- |
| `resumen de la semana pasada` | `📊 Resumen de Finanzas...`<br>`💸 Ingresos: $150,000`<br>`💰 Gastos: $45,000` |
| `cuanto gasté en alimentos este mes?` | `🔎 Gastos en Alimentos (ene 2024):`<br>`📅 Fecha: 2024-01-15 - $5,000`<br>`📅 Fecha: 2024-01-20 - $3,000`<br>`💰 Total: $8,000` |
| `enviame el reporte mensual` | `📊 Tu reporte mensual está listo!` *(adjunto PDF)* |

#### 4. Presupuestos y Alertas

| Comando | Respuesta |
| :--- | :--- |
| `fijar presupuesto de 100000 para salidas` | `✅ Presupuesto actualizado para Salidas.` |
| `como voy con salidas?` | `📊 Estado: 85% consumido. Te quedan $15,000.` |

*El bot te avisará automáticamente si un gasto hace que superes el 85% o el 100% de tu presupuesto.*

#### 5. Gestión y Edición

| Comando | Respuesta |
| :--- | :--- |
| `agrega la categoria Gimnasio` | `✅ Categoría 'Gimnasio' agregada.` |
| `el ultimo gasto no era 5000, eran 4500` | `✏️ Gasto actualizado con éxito.` |
| `borra el ultimo gasto` | `🗑️ Gasto eliminado.` |

## 🚀 Instalación y Configuración

### Prerrequisitos
*   Python 3.10 o superior.
*   Cuenta de Telegram y Token de Bot (@BotFather).
*   API Key de DeepSeek.
*   Cuenta de Google Cloud (para Google Sheets API).
*   **ffmpeg** instalado (obligatorio para procesar audios de voz):
    *   **macOS:** `brew install ffmpeg`
    *   **Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg`
    *   **Windows:** `choco install ffmpeg` (usando Chocolatey)

### Pasos

1.  **Clonar y Entorno Virtual:**
    ```bash
    git clone https://github.com/tu-usuario/tu-repo.git
    cd tu-repo
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

2.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Variables de Entorno (.env):**
    Crea un archivo `.env` en la raíz. El bot puede leer las credenciales de Google desde un archivo o directamente desde una variable de entorno:
    ```env
    TELEGRAM_TOKEN="TU_TOKEN"
    DEEPSEEK_API_KEY="TU_API_KEY"
    GOOGLE_SHEET_ID="ID_DE_TU_SHEET"
    # Opcional: Contenido completo del service_account.json como string
    GCP_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}' 
    ADMIN_CHAT_ID="TU_ID_DE_TELEGRAM"
    ```

4.  **Google Sheets:**
    *   Si no usas `GCP_SERVICE_ACCOUNT_JSON`, coloca tu `service_account.json` en la raíz del proyecto.
    *   Comparte tu hoja con el email del service account.
    *   Asegúrate de tener las hojas: `Gastos`, `Presupuestos`, `Categorias`.

5.  **Ejecutar:**
    ```bash
    python main.py
    ```

## 🐳 Docker (Opcional)

Si prefieres usar Docker, ya incluimos una configuración lista para usar:

1. **Construir la imagen:**
   ```bash
   docker build -t flux-cost-bot .
   ```
2. **Correr el contenedor:**
   ```bash
   docker run -d --name flux-bot --env-file .env flux-cost-bot
   ```

## 📂 Estructura del Proyecto

```
.
├── main.py                 # Entry point. Configura el Scheduler y el bucle principal.
├── flow.py                 # Definición del grafo de nodos (PocketFlow).
├── nodes.py                # Lógica de ejecución de cada nodo.
├── requirements.txt        # Dependencias (incluye Pillow, pocketflow, etc).
├── .env                    # Secretos.
├── service_account.json    # Credenciales Google (opcional si usas env var).
├── Dockerfile              # Configuración para Docker.
├── fly.toml                # Configuración para despliegue en Fly.io.
├── tests/                  # Tests unitarios
│   ├── conftest.py         # Fixtures para tests
│   ├── test_date_parsing_standalone.py
│   ├── test_helpers.py
│   └── test_nodes.py
├── .agent/                 # Skills de AI Agents
│   └── skills/
└── utils/
    ├── __init__.py
    ├── call_llm.py         # Interacción con DeepSeek (API OpenAI) con rate limiter, speech recognition y visión via base64.
    ├── prompts.py          # 🧠 Todos los prompts del sistema centralizados.
    ├── gsheets_api.py      # Lectura/Escritura en Sheets.
    ├── telegram_api.py     # Polling y envío de mensajes/fotos.
    └── logger_config.py    # Configuración de logs.
```

## ☁️ Despliegue (Fly.io)

1.  Instala `flyctl` e inicia sesión.
2.  Genera la app: `fly launch` (no despliegues aún).
3.  Configura los secretos en la nube:
    ```bash
    fly secrets set TELEGRAM_TOKEN="..." DEEPSEEK_API_KEY="..." GOOGLE_SHEET_ID="..."
    # Para el JSON de google, simplemente pega el contenido del archivo:
    fly secrets set GCP_SERVICE_ACCOUNT_JSON='{...}'
    ```
4.  Despliega: `fly deploy`.

## 🧪 Testing

El proyecto incluye tests para validar la funcionalidad del parsing de fechas, funciones helper y evitar regresiones.

```bash
# Activa el entorno virtual
source venv/bin/activate

# Corre los tests de forma standalone (más rápido)
python tests/test_date_parsing_standalone.py
python tests/test_helpers.py

# O corre todos los tests con pytest
python -m pytest tests/ -v
```

### Tests disponibles

El proyecto cuenta con **173 tests** cubriendo las funcionalidades principales:

- `test_date_parsing_standalone.py` - Tests para parsing de fechas relativas (hoy, ayer, anteayer, días de la semana)
- `test_date_parsing.py` - Tests para normalize_category y más funciones de parsing
- `test_helpers.py` - Tests para funciones helper como `calculate_monthly_spend` (11 tests)
- `test_detect_intent.py` - Tests para DetectIntentNode (15 intents diferentes)
- `test_nodes.py` - Tests para ParseExpenseListNode y otros nodos
- `test_parse_income.py` - Tests para ParseIncomeNode (5 tests)
- `test_parse_budget.py` - Tests para ParseBudgetNode (4 tests)
- `test_process_batch.py` - Tests para ProcessTransactionBatchNode (6 tests)
- `test_query_budget.py` - Tests para QueryBudgetNode (5 tests)
- `test_set_budget.py` - Tests para SetBudgetNode (4 tests)
- `test_add_category.py` - Tests para AddCategoryNode (4 tests)
- `test_call_llm.py` - Tests para el cliente DeepSeek/OpenAI con rate limiter, speech recognition y visión via base64
- `test_format_summary.py` - Tests para FormatSummaryNode (6 tests)
- `test_query_by_category.py` - Tests para QueryExpensesByCategoryNode (5 tests)
- `test_delete_last.py` - Tests para DeleteLastExpenseNode (4 tests)
- `test_edit_last.py` - Tests para EditLastExpenseNode (5 tests)
- `test_data_extraction.py` - Tests para DataExtractionNode y MonthlyAnalysisNode
- `test_analyze_receipt.py` - Tests para AnalyzeReceiptNode
- `test_integration.py` - Tests de integración entre nodos
- `test_export_report.py` - Tests para ExportReportNode (6 tests)
- `test_scheduler.py` - Tests para el scheduler automático (8 tests)

---

**Disclaimer:** Este es un proyecto personal de código abierto. Úsalo bajo tu propia responsabilidad. ¡Cuida tus finanzas! 💸