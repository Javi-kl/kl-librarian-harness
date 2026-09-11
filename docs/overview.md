
### Misión
  *Construir un agente que gestione una base de conocimiento de archivos de texto
  -- con mi vault de Logseq como primer caso real
  -- detectando duplicados, proponiendo reorganización y añadiendo conocimiento
  -- bajo mi aprobación y trazabilidad -- construyendo el harness completo:
  herramientas, contexto, sesión , permisos, observabilidad y evals.*  
---
---
## Docs
	- docs/architecture.md <- ADRs

---
## Características principales
  > Se investigan y rellenan `on-demand` (lo que necesite la `fase` en progreso )  
	### Componentes del harness
	- [[tools-kl-librarian-harness]]
	- [[runtime-pydantic-ai]]
	- [[Contexto-kl-librarian-harness]]
	- [[Sesión-kl-librarian-harness]]
	- [[guardrails-kl-librarian-harness]] ← (pieza profunda y transversal)
	- [[Observabilidad-kl-librarian-harness]] (transversal)
	- [[Evals-kl-librarian-harness]] (transversal)

---

	### Capacidades del agente
	- Detectar-duplicados-kl-librarian-harness
	- Corregir-KB-kl-librarian-harness
	- Proponer-reorganización-kl-librarian-harness
	- Proponer-conocimiento-kl-librarian-harness (BETA → F6)

---
- ## Fases
	- LATER [[F1-Tajada-vertical-mínima]] <- (MVP)
	  logseq.order-list-type:: number
	  > La **menor** combinación que funciona de punta a punta (esto sirve para cualquier proyecto) y para validarlo de forma rápida.  
		- **Descripción**
		  3 tools + 1 acción + aprobación + trazas + runtime PydanticAI + evals base.  
	- [[F2-Ampliar-herramientas-y-acciones]]
	  logseq.order-list-type:: number
		- **Descripción**
		  Más tools + acciones sobre lo existente + barrido completo + sesión  
	- [[F3-Guardrails-y-seguridad]]
	  logseq.order-list-type:: number
	  > Parte transversal y más profunda que el resto, donde debes enfocarte.  
		- **Descripción**
		  Permisos, seguridad y observabilidad.  
	- [[F4-Evals-y-endurecimiento]]
	  logseq.order-list-type:: number
		- **Descripción**
		  Evals de trayectoria en CI + pulido.  
	- [[F6-Accion-Proponer-conocimiento]]
	  logseq.order-list-type:: number
		- **Descripción**
		  Integrar contenido (tú aportás, el agente coloca)  
	- [[F5-Demo]]
	  logseq.order-list-type:: number
-
---
