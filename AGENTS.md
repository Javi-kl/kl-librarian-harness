# AGENTS.md — kl-librarian-harness

## Qué es este repo
Agente que gestiona un vault de notas `.md` (Logseq como primer caso). Runtime: Pydantic AI. Single-user, monolito modular, sin RAG.
Decisiones: `docs/architecture.md` (ADRs) · Requisitos: `docs/` (RF/RNF). No duplicar esos documentos aquí.

## Estado y alcance
- Fase actual: F1 (MVP): 3 tools + 1 acción (duplicados) + aprobación + traza + runtime + evals base.
- No adelantar fases ni añadir funcionalidad no pedida. Piezas o librerías nuevas → preguntar antes.

## Comandos
- Entorno ya montado (flake.nix + `.venv`): ejecutar dentro de él; no recrearlo.
- Tests: `pytest`
- Lint/formato: `ruff check --fix .` · `ruff format .`
- Tipos: `basedpyright`
- Todo: `pre-commit run --all-files`

## Verificación (antes de decir "hecho")
Ejecutar los checks que apliquen al cambio y reportar el resultado. Si algo falla: decirlo y arreglarlo. Si algo no se pudo ejecutar: decirlo.

## Idioma
- Docstrings, comentarios y documentación: español.
- Identificadores, nombres de tests y mensajes de commit: inglés.
- Respuestas al usuario: español.

## Estructura
- Código en `app/`, por capas del mapa (`docs/architecture.md`): acciones · guardrails · herramientas · runtime + transversales (contexto, sesión, observabilidad, evals). Nombres de carpetas pendientes de fijar: no crear carpetas nuevas sin acordarlo.
- Tests en `tests/`, espejando `app/`.

## Código
- Python 3.14 · pydantic-ai v2 (no v1: los ejemplos de internet usan otros nombres).
- Tipos en todo lo público.
- Tools con nombre estable en inglés: `search_text`, `edit_note`, `delete_note`. El docstring de una tool es su contrato para el modelo: si cambia el comportamiento, cambia el docstring.
- Comentarios solo para el porqué; sin `print` (usar `logging`), sin código comentado, sin secretos en el repo.
- Errores internos: excepciones. `{ok, ...}` solo como contrato de las tools.
- No duplicar documentación: comportamiento → prompt; uso de tools → docstrings; políticas → código.

## Tests
- `pytest`. Un archivo por módulo.
- Nombre: `test_<unidad>__<escenario>__<resultado_esperado>` en inglés. Ej.: `test_search_text__more_than_15_hits__returns_top_15_sorted_by_hits`.
- Deterministas: sin llamadas reales a APIs de modelos.
- Bug: primero el test que lo reproduce, después el arreglo.

## Flujo y permisos (estrictos)
- Sin permiso explícito no se modifica ni se crea nada: primero explicar y proponer.
- No hacer commit ni push salvo petición explícita.
- Cambios pequeños y enfocados; no tocar archivos no relacionados.
- Preguntar antes de: añadir dependencias · cambios estructurales · requisitos ambiguos.
- No inventar APIs: consultar la documentación de la versión instalada.
- Decisión técnica relevante → proponer ADR, sin redactarlo sin OK.

## Dónde está la verdad
`docs/` (architecture + requisitos). Lo que no esté escrito: preguntar, no asumir.
