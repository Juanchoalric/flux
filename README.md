# Bot de Finanzas Personales para Telegram

Un bot inteligente y multimodal para Telegram que te ayuda a llevar un control de tus finanzas personales de manera sencilla y conversacional. Registra gastos e ingresos, consulta resúmenes, define presupuestos y recibe alertas, todo a través de mensajes de texto o voz.

## Características Principales

*   ✅ **Registro de Transacciones:** Añade gastos e ingresos al instante.
*   🗣️ **Soporte Multimodal:** Envía un mensaje de texto o un **mensaje de voz** para registrar tus transacciones.
*   ✨ **Categorías Personalizables:** Agrega una o varias categorías nuevas en un solo mensaje para adaptar el bot a tu estilo de vida.
*   📊 **Resúmenes Financieros:** Pide resúmenes generales por períodos de tiempo flexibles ("hoy", "mes pasado", "últimos 15 días").
*   🎯 **Gestión de Presupuestos:** Define y consulta presupuestos mensuales por categoría.
*   🔔 **Alertas Automáticas:** Recibe notificaciones proactivas si te acercas o superas tu presupuesto mensual en una categoría.
*   🔍 **Consultas Detalladas:** Pregunta por gastos específicos en una o varias categorías y para cualquier período de tiempo que se te ocurra.
*   ✍️ **Edición y Eliminación Rápida:** Corrige el monto, la categoría o la descripción de tu último gasto, o bórralo por completo con un simple comando.
*   ❓ **Sistema de Ayuda y Fallback:** Si el bot no entiende, te da ejemplos. Además, puedes pedirle ayuda en cualquier momento con botones interactivos.
*   🧠 **Procesamiento con IA:** Utiliza Google Gemini para entender el lenguaje natural, interpretar fechas y extraer datos complejos.
*   ☁️ **Integración con Google Sheets:** Todas tus transacciones y presupuestos se guardan de forma segura y accesible en tu propia hoja de cálculo.

## ¿Cómo Funciona? El Flujo del Bot

El proyecto está construido sobre el framework **PocketFlow**, que organiza la lógica en una serie de **Nodos** interconectados. Cada nodo tiene una tarea específica, lo que hace que el sistema sea modular y fácil de extender.

El flujo principal es el siguiente:

1.  **Recepción del Mensaje:** El `GetMessageNode` revisa constantemente si hay nuevos mensajes en Telegram, incluyendo clics en botones.
2.  **Análisis de Tipo:** Determina si el mensaje es de texto, de audio o un clic de botón.
    *   Si es **audio**, pasa al `TranscribeAudioNode`, que usa la IA para convertir la voz a texto.
    *   Si es **texto** o un **clic de botón**, pasa directamente al siguiente paso.
3.  **Detección de Intención:** El `DetectIntentNode` analiza el texto y lo clasifica en una de las acciones posibles (registrar gasto, consultar resumen, editar gasto, etc.).
4.  **Ramificación (Branching):** Según la intención detectada, el flujo se dirige a la rama correspondiente para ejecutar la acción solicitada.
5.  **Ejecución y Respuesta:** Los nodos de cada rama procesan la solicitud, interactúan con Google Sheets y envían una respuesta al usuario a través de Telegram.

### Diagrama del Flujo

```mermaid
flowchart TD
    subgraph "Inicio"
        A[Usuario envía mensaje] --> B(GetMessageNode);
    end

    B --> C{¿Texto, Audio o Botón?};
    C -- Texto/Botón --> E[DetectIntentNode];
    C -- Audio --> D[TranscribeAudioNode];
    D --> E;

    subgraph "Acciones del Bot"
        E -- REGISTRAR_GASTO --> F[ParseExpenseListNode];
        E -- REGISTRAR_INGRESO --> G[ParseIncomeNode];
        E -- CONSULTAR_GASTOS --> H[FetchSheetDataNode];
        E -- DEFINIR_PRESUPUESTO --> I[ParseBudgetNode];
        E -- CONSULTAR_PRESUPUESTO --> J[QueryBudgetNode];
        E -- AGREGAR_CATEGORIA --> Q[AddCategoryNode];
        E -- CONSULTAR_GASTOS_POR_CATEGORIA --> R[QueryExpensesByCategoryNode];
        E -- PEDIR_AYUDA --> S[HelpNode];
        E -- OTRO --> T[FallbackNode];
        E -- EDITAR_ULTIMO_GASTO --> U[EditLastExpenseNode];
        E -- ELIMINAR_ULTIMO_GASTO --> V[DeleteLastExpenseNode];
    end

    F --> K[ProcessTransactionBatchNode];
    G --> K;
    
    subgraph "Procesamiento y Salida"
        K -- Alerta (Opcional) --> L[Notificación de Alerta];
        H --> M[FormatSummaryNode] --> N[SendSummaryNode];
        I --> O[SetBudgetNode];
    end
    
    L --> P((Fin));
    N --> P;
    O --> P;
    J --> P;
    Q --> P;
    R --> P;
    S --> P;
    T --> P;
    U --> P;
    V --> P;
```

## Guía de Uso y Ejemplos

#### 1. Registrar un Gasto
Puedes registrar uno o varios gastos en un solo mensaje, ya sea por texto o por voz.

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `Gaste 5000 en un cafe y 12000 en el supermercado` | `Gasto Registrado ✅`<br>`Monto: 5000.0 PESOS`<br>`Categoría: salidas`<br><br>`Gasto Registrado ✅`<br>`Monto: 12000.0 PESOS`<br>`Categoría: alimentos` |
| 🎙️ *(Mensaje de voz)* "hice un gasto de 28000 en medicamentos" | `Gasto Registrado ✅`<br>`Monto: 28000.0 PESOS`<br>`Categoría: medicamentos` |

#### 2. Registrar un Ingreso

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `cobre 150000 de mi sueldo` | `Ingreso Registrado 💸`<br>`Monto: 150000.0 PESOS`<br>`Descripción: sueldo` |

#### 3. Pedir un Resumen Financiero

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `resumen de la semana pasada` | `📊 Resumen de Finanzas del 2025-10-25 al 2025-11-01`<br>`-----------------------------------`<br>`💸 Total Ingresado: 150,000.00 PESOS`<br>`💰 Total Gastado: 17,000.00 PESOS`<br>`⚖️ Balance Final: 133,000.00 PESOS`<br>... (etc.) |

#### 4. Definir un Presupuesto Mensual

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `fijar presupuesto de 80000 para alimentos` | `✅ Presupuesto actualizado!`<br>`Categoría: Alimentos`<br>`Monto Máximo: 80,000.00 PESOS` |

#### 5. Consultar un Presupuesto

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `cuanto me queda para alimentos?` | `📊 Estado de tu Presupuesto para 'Alimentos'`<br>`-----------------------------------`<br>` Límite Mensual: 80,000.00 PESOS`<br>` Total Gastado: 65,000.00 PESOS (81.3%)`<br>`-----------------------------------`<br>` **Te quedan: 15,000.00 PESOS**` |

#### 6. Gestionar Categorías
Personaliza el bot añadiendo tus propias categorías de gastos. Puedes agregar una o varias a la vez.

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `agrega la categoria Gimnasio` | `✅ Categorías agregadas: Gimnasio.` |
| `añade las categorias Inversiones y Regalos` | `✅ Categorías agregadas: Inversiones, Regalos.` |

#### 7. Consultar Gastos por Categoría
Haz preguntas específicas sobre tus gastos para entender mejor tus hábitos. El bot entiende períodos de tiempo flexibles.

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `cuales fueron mis gastos en alimentos este mes?` | `🔎 Detalle de Gastos para Alimentos (del 2025-11-01 al 2025-11-30):`<br>... (lista de gastos) ... |
| `mostrame los gastos de auto y mascotas del mes pasado` | `🔎 Detalle de Gastos para Auto, Mascotas (del 2025-10-01 al 2025-10-31):`<br>... (lista de gastos) ... |

#### 8. Editar o Eliminar el Último Gasto
¿Te equivocaste? Puedes corregir o borrar tu última entrada fácilmente.

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `borra el ultimo gasto` | `🗑️ Gasto eliminado con éxito:`<br>`  - Descripción: cafe`<br>`  - Monto: 5000` |
| `el ultimo gasto no era 5000, eran 4500` | `✏️ Gasto actualizado con éxito!`<br><br>`*Antes:*`<br>`  - Desc: cafe, Monto: 5000, Cat: Salidas`<br><br>`*Ahora:*`<br>`  - Desc: cafe, Monto: 4500, Cat: Salidas` |
| `cambia la categoria del ultimo a alimentos` | `✏️ Gasto actualizado con éxito!`<br>... (mensaje similar) ... |

#### 9. Pedir Ayuda y Manejo de Errores
Si no estás seguro de qué hacer o el bot no te entiende, te ofrecerá ayuda.

| Comando (Lo que dices tú) | Respuesta del Bot |
| :--- | :--- |
| `ayuda` o `/help` | `¡Hola! Soy tu asistente de finanzas. Esto es todo lo que puedo hacer por ti:`<br>... (lista completa de comandos) ...<br>[Botón: 📊 Pedir Resumen de Hoy] |
| `mandale saludos a mi tia` | `😕 No entendí tu mensaje.`<br>`Recuerda que puedes registrar gastos, ingresos o pedir resúmenes.`<br>... (ejemplos) ...<br>[Botón: ❓ Ver todos los comandos] |

#### 10. Alertas de Presupuesto (Automáticas)
Estas alertas se envían automáticamente después de registrar un gasto que cruza un umbral.

| Situación | Respuesta del Bot (Automática) |
| :--- | :--- |
| Un gasto hace que superes el 85% de tu presupuesto. | `⚠️ ¡Atención! ⚠️`<br>`Ya has utilizado más del 85% de tu presupuesto para 'Alimentos'.`<br>`Gastado este mes: 70,000.00 de 80,000.00 PESOS.` |
| Un gasto hace que superes el 100% de tu presupuesto. | `🚨 ¡Alerta de Presupuesto! 🚨`<br>`Acabas de superar el 100% de tu presupuesto para 'Alimentos'.`<br>`Gastado este mes: 82,500.00 de 80,000.00 PESOS.` |

## Instalación y Configuración

Sigue estos pasos para poner en marcha tu propio bot.

#### Prerrequisitos
*   Python 3.9 o superior.
*   Una cuenta de Telegram y un token de bot (créalo hablando con [@BotFather](https://t.me/BotFather)).
*   Una cuenta de Google y una API Key de Google Gemini (consíguela en [Google AI Studio](https://aistudio.google.com/)).
*   `ffmpeg` instalado en tu sistema (necesario para el procesamiento de audio).

#### Pasos de Instalación
1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/Juanchoalric/flux.git
    cd tu-repositorio
    ```

2.  **Crea un entorno virtual y actívalo:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura las variables de entorno:**
    *   Crea un archivo llamado `.env` en la raíz del proyecto.
    *   Añade tus claves y IDs:
        ```env
        TELEGRAM_TOKEN="TU_TOKEN_DE_TELEGRAM"
        GEMINI_API_KEY="TU_API_KEY_DE_GEMINI"
        GOOGLE_SHEET_ID="EL_ID_DE_TU_HOJA_DE_CALCULO"
        ```

5.  **Configura Google Sheets:**
    *   Crea una nueva Hoja de Cálculo en Google Sheets.
    *   Copia su ID desde la URL (la cadena larga de caracteres entre `/d/` y `/edit`).
    *   Crea una **cuenta de servicio** en Google Cloud Console, descarga el archivo de credenciales `JSON` y guárdalo en la raíz del proyecto con el nombre `service_account.json`.
    *   **Comparte** tu Hoja de Cálculo con el email de la cuenta de servicio (lo encontrarás en el archivo JSON) dándole permisos de "Editor".
    *   Crea **tres** hojas dentro del archivo: `Gastos`, `Presupuestos` y `Categorias`, cada una con sus encabezados correspondientes.

## Ejecución
Para iniciar el bot, simplemente ejecuta el archivo principal:
```bash
python main.py```

## Estructura del Proyecto
```
.
├── main.py                 # Punto de entrada, inicia el bucle principal.
├── flow.py                 # Define la arquitectura y conexiones de los nodos.
├── nodes.py                # Contiene la lógica de cada paso del flujo.
├── requirements.txt        # Lista de dependencias de Python.
├── .env                    # Archivo para guardar tus claves secretas (no subir a git).
├── service_account.json    # Credenciales para la API de Google Sheets.
├── .gitignore              # Archivo para ignorar ciertos archivos en git.
├── fly.toml                # Configuración para desplegar en Fly.io.'
├── Dockerfile              # Archivo para construir la imagen de Docker.
├── .dockerignore           # Archivo para ignorar ciertos archivos al construir la imagen de Docker.
└── utils/
    ├── __init__.py
    ├── call_llm.py         # Utilidad para interactuar con la IA de Gemini.
    ├── gsheets_api.py      # Utilidad para leer y escribir en Google Sheets.
    └── telegram_api.py     # Utilidad para interactuar con la API de Telegram.
```


## 6. **☁️ Despliegue en Fly.io**

Una vez que el bot funciona correctamente en tu máquina local, sigue estos pasos para desplegarlo en la nube y que funcione 24/7.

### Paso 1: Iniciar Sesión en Fly.io

Abre tu terminal en la carpeta raíz del proyecto y autentícate con la CLI de Fly.io. Esto abrirá una ventana en tu navegador para que inicies sesión.

```bash
fly auth login```

### Paso 2: Lanzar la Aplicación por Primera Vez

Este comando analizará tu `Dockerfile` y creará el archivo de configuración `fly.toml` para tu aplicación.

```bash
fly launch
```

Fly te hará algunas preguntas. Responde de la siguiente manera:
*   `? App Name (leave blank to generate one):` Presiona **Enter** para que genere un nombre aleatorio o escribe uno personalizado.
*   `? Select region:` Elige la región más cercana a ti (ej. `scl` para Santiago, Chile).
*   `? Would you like to set up a Postgresql database now?` Responde **No**.
*   `? Would you like to set up an Upstash Redis database now?` Responde **No**.
*   `? Would you like to deploy now?` Responde **No** (es mejor configurar los secretos primero).

### Paso 3: Configurar los Secretos en la Nube

Los "secretos" son el equivalente a tu archivo `.env`, pero almacenados de forma segura en los servidores de Fly.io. Ejecuta estos comandos uno por uno en tu terminal, reemplazando los valores de ejemplo con tus credenciales reales.

```bash
fly secrets set TELEGRAM_TOKEN="tu_token_de_telegram"
fly secrets set GEMINI_API_KEY="tu_api_key_de_gemini"
fly secrets set GOOGLE_SHEET_ID="el_id_de_tu_google_sheet"
fly secrets set TZ="America/Buenos_Aires" # Ajusta esto a tu zona horaria
```

Para las credenciales de Google, el comando es multi-línea. Copia y pega el bloque completo, reemplazando el texto del medio con el contenido de tu archivo `service_account.json`:
```bash
fly secrets set GCP_SERVICE_ACCOUNT_JSON='''
(Pega aquí el contenido COMPLETO de tu archivo service_account.json)
'''
```

### Paso 4: Desplegar la Aplicación

Ahora que la configuración y los secretos están listos, ejecuta el comando final para construir la imagen de tu bot y lanzarla en la nube.
```bash
fly deploy
```
Este proceso puede tardar unos minutos. Fly.io te mostrará el progreso de la construcción y el despliegue.