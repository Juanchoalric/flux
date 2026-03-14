---
name: pocketflow
description: >
  Guía para construir sistemas LLM con PocketFlow.
  Trigger: Cuando el proyecto usa PocketFlow o el usuario quiere implementar Agentic Coding.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Proyecto Python que usa PocketFlow
- User pide ayuda con agentic coding o diseño de flows LLM
- Necesidad de implementar: Node, Flow, Batch, Async, Agent, RAG, MapReduce, Workflow

## Agentic Coding Protocol

| Step | Human | AI |
|------|-------|-----|
| 1. Requirements | ★★★ | ★☆☆ |
| 2. Flow Design | ★★☆ | ★★☆ |
| 3. Utilities | ★★☆ | ★★☆ |
| 4. Data | ★☆☆ | ★★★ |
| 5. Node | ★☆☆ | ★★★ |
| 6. Implementation | ★☆☆ | ★★★ |
| 7. Optimization | ★★☆ | ★★☆ |
| 8. Reliability | ★☆☆ | ★★★ |

**Regla clave**: "Keep it simple, stupid!" - Empezar simple, diseñar ANTES de implementar.

## Core Patterns

### Node (prep → exec → post)

```python
class MyNode(Node):
    def prep(self, shared):
        # Leer de shared store
        return shared["input"]
    
    def exec(self, prep_res):
        # Lógica (LLM calls, APIs) - NO acceder shared
        return call_llm(prep_res)
    
    def post(self, shared, prep_res, exec_res):
        # Escribir a shared + decidir siguiente acción
        shared["output"] = exec_res
        return "default"  # o "action_name" para branching
```

### Flow (conectar nodes)

```python
node_a >> node_b              # default transition
node_a - "action" >> node_b   # named action
flow = Flow(start=node_a)
flow.run(shared)
```

### Shared Store

```python
shared = {
    "input": {...},
    "results": {},
    "config": {...}
}
```

### BatchNode

```python
class ProcessItems(BatchNode):
    def prep(self, shared):
        # Retorna un iterable (lista, generator)
        return shared["items"]
    
    def exec(self, item):
        # Se ejecuta por cada item
        return process(item)
    
    def post(self, shared, prep_res, exec_res_list):
        # exec_res_list tiene TODOS los resultados
        shared["results"] = exec_res_list
        return "default"
```

### AsyncNode

```python
class MyAsyncNode(AsyncNode):
    async def prep_async(self, shared):
        return await fetch_data(shared["url"])
    
    async def exec_async(self, prep_res):
        return await call_llm_async(prep_res)
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["result"] = exec_res
        return "default"

# Usar con AsyncFlow
flow = AsyncFlow(start=my_async_node)
await flow.run_async(shared)
```

## Design Patterns

| Pattern | Cuándo usarlo |
|---------|---------------|
| **Workflow** | Chain de tareas secuenciales |
| **Agent** | Decisiones dinámicas basadas en contexto |
| **RAG** | Retrieval + Generation (2-stage: offline indexing, online query) |
| **MapReduce** | Procesar grandes datasets (map = BatchNode, reduce = aggregation) |
| **Batch** | Múltiples items independientes |
| **Async** | I/O paralelo o esperar feedback |

## Fault Tolerance

```python
# Retry con backoff
node = MyNode(max_retries=3, wait=10)

# Fallback en vez de crash
class MyNode(Node):
    def exec_fallback(self, prep_res, exc):
        return "fallback_result"
    
    def post(self, shared, prep_res, exec_res):
        shared["result"] = exec_res
        return "default"
```

## Project Structure

```
my_project/
├── main.py
├── nodes.py
├── flow.py
├── utils/
│   ├── __init__.py
│   ├── call_llm.py
│   └── search_web.py
├── requirements.txt
└── docs/
    └── design.md
```

**requirements.txt**:
```
pocketflow
PyYAML
```

## Utilities (no incluidas - implementar vos)

- `call_llm.py` - Wrapper para OpenAI, Anthropic, Gemini, Ollama
- `get_embedding.py` - Embeddings
- `search_web.py` - Web search

> **Why not built-in?** PocketFlow cree que es mala práctica tener APIs vendor-specific hardcodeadas. Vas a querer cambiar vendors, usar fine-tuned models, o correr local.

## Commands

```bash
pip install pocketflow
```

## Resources

- **Repo**: https://github.com/the-pocket/PocketFlow
- **Design Template**: Ver skill `pocketflow-design` para docs/design.md
