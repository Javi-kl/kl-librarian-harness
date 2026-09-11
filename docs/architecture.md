## Qué es el sistema
	- Agente que gestiona vault de .md, runtime prestado, single-user, sin RAG.
---
## Mapa
 ### Este mapa esta vivo y necesita adaptarse y actualizarse de forma continau, por ej, las acciones son corregibles o matizables.
  ```
  Acciones (dominio)      ← Duplicados · Corregir · Reorganizar…
  Guardrails / Permisos   ← envuelve acciones: nada se escribe sin aprobación
  Herramientas            ← acceso al vault: texto · estructura · fuzzy
  Runtime (prestado)      ← bucle Pydantic AI
  ─────────────────────────────────────────────
  Transversales: contexto (rellena el prompt) · sesión (estado entre runs)
                 observabilidad (traza todo) · evals (mide trayectoria)
  ```

---
# ADRs
 ## ADR-001 -- pendiente de cerrar
  decisión:: Pydantic AI como runtime.
  porque:: Por coherencia con mi stack actual y el beneficio que conlleva, además de poder centrarme en aprender otros conceptos, me sirve una calidad estandar, no necesito lo mas top en este punto.
  trade-off:: quizas no sea el mejor haciendo esa función, falta investigar este punto mejor.
  alternativa:: LangGraph -- descartado por complejidad frente al objetivo de aprender.
 ## ADR-002
  decisión:: Monolito modular con shared minimo.
  porque:: evolución de anterior monolito que quedo desorganizado, single-user.
  trade-off:: no aprender otras arquitecturas, riesgo de shared/ demasiado grande.
  alternativa:: monolito clásico (desorganizado si crece) y microservicios (complejidad para single-user)
 ## ADR-003
  decisión:: tool buscar_texto(términos) en Python; output = top 15 notas {path, título, contenido, hits} ordenadas por hits".
  porque:: grep no normaliza acentos/case → igual habría que preprocesar con Python + ya que iteramos, devolvemos la nota completa con estructura, porque la acción (duplicados) compara contenido y el agente juzga sobre notas completas.
  trade-off:: coste de parsear y buscar en todos los archivos en cada llamada del modelo a la tool.; dejar archivos fuera por demasiadas coincidencias.
 ## ADR-004
  decisión:: tools de gestión primitivas al estilo Claude Code (leer, escribir, borrar), compuestas por el agente dentro del bucle.
  porque:: es el estándar de la industria, cada tool tiene blast radius acotado y auditable, y la seguridad se concentra en la capa de permisos (pieza profunda del proyecto).
  trade-off:: aceptar que el agente no elija bien las secuencias -- mitigando ese riesgo con reglas en código.
 ## ADR-005
  decisión:: Guardrails F1: política de aprobación de 3 niveles (leer libre, escribir pide, borrar pide SIEMPRE) + reglas en código: read-before-wirte (no mutar un path no leído en la ejecución) y borrado = mover a trash/
  porque:: la seguridad se hace cumplir en código, no en el prompt del modelo: el prompt se puede eludir. La papelera hace reversible el borrado por error.
  alternativa:: auto-aprobar escritura y preguntar solo por borrado - descartada: deja pasar sobrescrituras malas sin revisión; reabrir con más capas en futuras fases del proyecto.
