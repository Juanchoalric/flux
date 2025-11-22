def get_detect_intent_prompt(today_str: str, message_text: str) -> str:
    return f"""
    Analiza el mensaje del usuario y clasifica su intención.
    La fecha de hoy es {today_str}.
    Responde ÚNICAMENTE con un objeto JSON.

    Las intenciones posibles son: "REGISTRAR_GASTO", "REGISTRAR_INGRESO", "CONSULTAR_GASTOS", "DEFINIR_PRESUPUESTO", "CONSULTAR_PRESUPUESTO","AGREGAR_CATEGORIA", "CONSULTAR_GASTOS_POR_CATEGORIA", "PEDIR_AYUDA", "EDITAR_ULTIMO_GASTO", "ELIMINAR_ULTIMO_GASTO", "OTRO".

    **REGLAS PARA EXTRACCIÓN DE FECHAS:**
    - Para "CONSULTAR_GASTOS" y "CONSULTAR_GASTOS_POR_CATEGORIA", DEBES extraer "start_date" y "end_date" en formato "YYYY-MM-DD".
    - "este mes": Calcula el primer y último día del mes actual.
    - "mes pasado": Calcula el primer y último día del mes anterior.
    - "ayer": Ambas fechas son el día de ayer.
    - "últimos 10 días": Calcula desde hace 10 días hasta hoy.

    Ejemplos:
    - "borra el ultimo gasto" -> {{"intent": "ELIMINAR_ULTIMO_GASTO", "entities": {{}}}}
    - "el ultimo gasto no era 5000, eran 4500" -> {{"intent": "EDITAR_ULTIMO_GASTO", "entities": {{}}}}
    - "gaste 5000 en cafe" -> {{"intent": "REGISTRAR_GASTO", "entities": {{}}}}
    - "cargué 100000 de mi sueldo" -> {{"intent": "REGISTRAR_INGRESO", "entities": {{}}}}
    - "cuanto gaste hoy?" -> {{"intent": "CONSULTAR_GASTOS", "entities": {{"start_date": "{today_str}", "end_date": "{today_str}"}}}}
    - "agrega categoria de Viajes" -> {{"intent": "AGREGAR_CATEGORIA", "entities": {{}}}}
    - "la ultima va para servicios" -> {{"intent": "EDITAR_ULTIMO_GASTO", "entities": {{}}}}
    - "era de comida" -> {{"intent": "EDITAR_ULTIMO_GASTO", "entities": {{}}}}
    - "me equivoque, era nafta" -> {{"intent": "EDITAR_ULTIMO_GASTO", "entities": {{}}}}
    - "fijar presupuesto de 20000 para Salidas" -> {{"intent": "DEFINIR_PRESUPUESTO", "entities": {{}}}}
    - "como voy con el presupuesto de alimentos" -> {{"intent": "CONSULTAR_PRESUPUESTO", "entities": {{"category": "alimentos"}}}}
    - "gastos en salidas la semana pasada" -> {{"intent": "CONSULTAR_GASTOS_POR_CATEGORIA", "entities": {{"categories": ["salidas"], "start_date": "...", "end_date": "..."}}}}
    - "ayuda" -> {{"intent": "PEDIR_AYUDA", "entities": {{}}}}
    - "hola" -> {{"intent": "OTRO", "entities": {{}}}}

    Mensaje a analizar: "{message_text}"
    """

def get_edit_expense_prompt(categories_str: str, message_text: str) -> str:
    return f"""
    Analiza la solicitud del usuario para editar su último gasto.
    Extrae ÚNICAMENTE los campos que el usuario quiere cambiar: "amount", "category", o "description".
    Responde con un objeto JSON. Si un campo no se menciona, no lo incluyas.
    Para "category", DEBES elegir uno de los siguientes valores: [{categories_str}].

    Ejemplos:
    - "el ultimo no era 10000, eran 9500" -> {{"amount": 9500}}
    - "cambia la categoria a salidas" -> {{"category": "salidas"}}
    - "la descripcion era cafe con amigos" -> {{"description": "cafe con amigos"}}
    - "eran 1200 de supermercado en la categoria alimentos" -> {{"amount": 1200, "description": "supermercado", "category": "alimentos"}}

    Solicitud a analizar: "{message_text}"
    """

def get_add_category_prompt(message_text: str) -> str:
    return f"""
    Analyze the following text and extract the names of all new categories the user wants to add.
    Respond ONLY with a JSON object with the key "category_names", which must be an array of strings.

    Examples:
    - Text: "Quiero agregar la categoría Viajes" -> {{"category_names": ["Viajes"]}}
    - Text: "agregar Mascotas y Gimnasio a mis categorías" -> {{"category_names": ["Mascotas", "Gimnasio"]}}
    - Text: "nuevas categorias: Inversiones, Salud y Educación" -> {{"category_names": ["Inversiones", "Salud", "Educación"]}}

    Text to analyze: "{message_text}"
    """

def get_parse_expense_prompt(categories_str: str, message_text: str) -> str:
    return f"""
    Analiza el siguiente texto y extrae todos los gastos que encuentres.
    Responde ÚNICAMENTE con un array de objetos JSON.

    **REGLAS IMPORTANTES:**
    1.  El formato de cada objeto DEBE ser EXACTAMENTE: {{"amount": <numero>, "category": "<categoria>", "description": "<descripcion>"}}.
    2.  La clave "description" DEBE contener el detalle del gasto (ej: "supermercado", "cafe con amigos").
    3.  Para la clave "category", DEBES elegir uno de los siguientes valores: [{categories_str}]. Si no encaja, usa "otros".
    4.  NO inventes claves nuevas como "currency" o "establishment".

    **EJEMPLOS DE CLASIFICACIÓN:**
    - Texto: "fui al super y gaste 12000" -> [{{"amount": 12000, "category": "alimentos", "description": "supermercado"}}]
    - Texto: "2500 en un cafe con medialunas" -> [{{"amount": 2500, "category": "salidas", "description": "cafe con medialunas"}}]
    - Texto: "hice un gasto de 28000 pesos en medicamento ibupirac" -> [{{"amount": 28000, "category": "medicamentos", "description": "medicamento ibupirac"}}]
    - Texto: "cargué nafta por 15000 y 3000 de un peaje" -> [{{"amount": 15000, "category": "auto", "description": "nafta"}}, {{"amount": 3000, "category": "auto", "description": "peaje"}}]

    Texto a analizar: "{message_text}"
    """

def get_parse_income_prompt(message_text: str) -> str:
    return f"""
    Analiza el siguiente texto y extrae el monto y la descripción del ingreso.
    Responde ÚNICAMENTE con un objeto JSON con las claves "amount" y "description".

    Ejemplos:
    - Texto: "cargué 150000 de mi sueldo" -> {{"amount": 150000, "description": "sueldo"}}
    - Texto: "me pagaron 20000 por el proyecto freelance" -> {{"amount": 20000, "description": "proyecto freelance"}}

    Texto a analizar: "{message_text}"
    """

def get_parse_budget_prompt(message_text: str) -> str:
    return f"""
    Analiza el siguiente texto y extrae la categoría y el monto para un presupuesto.
    Responde ÚNICAMENTE con un objeto JSON con las claves "category" y "amount".
    La categoría debe ser una sola palabra y en minúsculas.

    Ejemplos:
    - Texto: "Quiero fijar un presupuesto de 50000 para Alimentos" -> {{"category": "alimentos", "amount": 50000}}
    - Texto: "presupuesto para salidas: 25000" -> {{"category": "salidas", "amount": 25000}}
    - Texto: "Setea 10000 en Ocio" -> {{"category": "ocio", "amount": 10000}}

    Texto a analizar: "{message_text}"
    """

def get_monthly_analysis_prompt(data_str: str, last_month_name: str) -> str:
    return f"""
    Eres un analista financiero personal. Tu tarea es crear un resumen mensual claro y útil para un usuario basado en sus datos de gastos.
    El resumen debe ser amigable, perspicaz y estar formateado en Markdown para Telegram.

    Aquí están los datos de gastos de los últimos dos meses:
    ```json
    {data_str}
    ```

    **Instrucciones para el Resumen:**
    1.  **Título:** Comienza con un título claro, por ejemplo: "📈 Resumen Financiero de {last_month_name}".
    2.  **Comparación General:** Compara el gasto total del mes pasado con el mes anterior. Indica si subió o bajó y en qué porcentaje aproximado.
    3.  **Top 3 Categorías:** Muestra las 3 categorías en las que más se gastó el mes pasado, con sus montos.
    4.  **Análisis de Tendencias:** Identifica 1 o 2 cambios significativos entre los meses. Por ejemplo: "Tu gasto en 'Salidas' aumentó un 40% este mes" o "Lograste reducir tus gastos en 'Otros'".
    5.  **Key Points (Puntos Clave):** Revisa las descripciones de los `raw_expenses` del mes pasado y menciona 1 o 2 gastos inusuales o de alto valor que destaquen. Por ejemplo: "Se destaca una compra importante en 'Regalos' por la descripción 'Aniversario'".
    6.  **Conclusión:** Termina con una frase corta y motivadora.

    Genera únicamente el texto del resumen.
    """

def get_analyze_receipt_prompt(categories_str: str) -> str:
    return f"""
    Analiza esta imagen de un ticket de compra, factura o recibo.
    Tu tarea es extraer los ítems comprados y el total.
    
    Responde ÚNICAMENTE con un array de objetos JSON válido.
    
    Reglas:
    1. Formato: [{{"amount": numero, "category": "categoria", "description": "descripcion breve"}}]
    2. Solo devolve el total. No devuelvas ítems individuales.
    3. Categorías permitidas: [{categories_str}]. Si no encaja, usa "otros".
    4. Descripción: Sé conciso pero descriptivo, agrega detalles utiles, como la marca o el producto (ej: "Supermercado en Changomas", "Cena en Willison", "Nafta en YPF").
    5. Si la imagen NO es un recibo o no es legible, devuelve un array vacío [].

    Ejemplo de salida:
    [
        {{"amount": 4500, "category": "alimentos", "description": "compra carniceria"}}
    ]
    """