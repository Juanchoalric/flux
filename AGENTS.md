# Agent Skills

| Skill | Description | Documentation |
|-------|-------------|---------------|
| **Alta Prioridad** | | |
| `pocketflow` | Guía para construir sistemas LLM con PocketFlow | [SKILL.md](.agent/skills/pocketflow/SKILL.md) |
| `pocketflow-design` | Template para documentar proyectos PocketFlow | [SKILL.md](.agent/skills/pocketflow-design/SKILL.md) |
| `python-telegram-bot` | Guía para python-telegram-bot | [SKILL.md](.agent/skills/python-telegram-bot/SKILL.md) |
| `google-sheets` | Guía para Google Sheets API con gspread | [SKILL.md](.agent/skills/google-sheets/SKILL.md) |
| `gemini-api` | Guía para Google Generative AI (Gemini) | [SKILL.md](.agent/skills/gemini-api/SKILL.md) |
| **Media Prioridad** | | |
| `docker` | Guía para Docker y containerización | [SKILL.md](.agent/skills/docker/SKILL.md) |
| `fly-io` | Guía para Fly.io deployment | [SKILL.md](.agent/skills/fly-io/SKILL.md) |
| `python-logging` | Guía para Python logging | [SKILL.md](.agent/skills/python-logging/SKILL.md) |
| `python-testing` | Guía para pytest y testing | [SKILL.md](.agent/skills/python-testing/SKILL.md) |

---

## 🧪 Regla de Testing (OBLIGATORIA)

Antes de **cualquier commit, merge, o deploy**, se DEBE cumplir:

1. **Correr tests**: Ejecutar `python -m pytest tests/ -v` y verificar que pasen
2. **Nuevos features**: Crear tests para código nuevo en `tests/`
3. **Modificaciones**: Actualizar tests existentes si el comportamiento cambia
4. **Coverage**: Mantener la cobertura de tests (>100 tests)

### Flujo obligatorio:
```
codigo nuevo/modificado → escribir tests → correr tests → commit → push
```

**No hay excepciones** - ni "es solo un cambio menor", ni "ya funciona", ni "tengo prensa". Sin tests passing, no se sube código.
