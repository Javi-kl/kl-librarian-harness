## RFs
  (Qué hace el sistema)
	- RF-01
	  > **Como** dueño de la KB, **quiero** que el agente encuentre duplicados reales en mi KB -- explorando por su cuenta a partir de lo que le cuento, o yendo al tema que yo le señale -- **para** no buscarlos a mano.
		- **C1 - Encuentra**
		  DADO QUE el vault de prueba tiene contenido repetido real y conocido, entre notas o dentro de una misma nota,
		  CUANDO le pido los duplicados de ese tema,
		  ENTONCES ese duplicado está entre los hallazgos.
		- **C2 - Encuentra explorando**
		  DADO QUE le conté de qué va la KB,
		  CUANDO le pido duplicados sin señalarle tema,
		  ENTONCES al menos uno de los hallazgos lo reconozco como contenido repetido real.
		- **C3 - Reales**
		  DADO QUE el agente me presenta hallazgos,
		  CUANDO los reviso abriendo las notas que señala,
		  ENTONCES ninguno es inventado o falso.
		- **C4 - Tema limpio**
		  DADO QUE el tema no tiene duplicados,
		  CUANDO lo pido,
		  ENTONCES me dice que no encontró(no rellena con parecidos).
		- **C5 - Rutas para comprobar**
		  DADO QUE recibo los hallazgos, CUANDO voy a trabajar con uno, ENTONCES trae las rutas, las secciones o bloques afectados y fragmentos breves que permiten comprobar qué contenido se repite.
		- **C6 - Revisar antes de consolidar**
		  DADO QUE el agente encuentra contenido repetido,
		  CUANDO propone revisarlo,
		  ENTONCES explica qué se repite y qué aporta cada parte, sin dar por hecho que haya que juntarlas o eliminar alguna; puedo descartarlo, aportar contexto o pedir una propuesta de edición.

  ---
	- RF-02
	  > **Como** dueño de la KB, **quiero** ver y aprobar cada escritura y cada borrado antes de que ocurra, **para** poder confiar en su resultado.
		- **C1 - Nada sin mi OK**
		  DADO QUE el agente va a escribir o borrar,
		  CUANDO llega el momento de ejecutarlo,
		  ENTONCES me pide mi OK y no ejecuta nada hasta tenerlo.
		- **C2 - Veo qué apruebo**
		  DADO QUE me pide aprobación para escribir,
		  CUANDO la reviso,
		  ENTONCES veo el cambio concreto que se hará (el diff), no una descripción.
		- **C3 - Rechazo**
		  DADO QUE me pide aprobación,
		  CUANDO rechazo,
		  ENTONCES no se ejecuta nada de eso y el run se detiene.
		- **C4 - Aprobado = escrito**
		  DADO QUE apruebo el cambio que se me mostró,
		  CUANDO se ejecuta,
		  ENTONCES el contenido escrito es idéntico al que vi al aprobar.
		- **C5 - Borrado recuperable**
		  DADO QUE apruebo un borrado,
		  CUANDO se ejecuta,
		  ENTONCES la página queda en trash y puedo recuperarla.
  ---
	RF-03
	  > **Como** dueño de la KB, **quiero** que el agente me proponga la consolidación del contenido repetido mostrándome el diff de cómo quedarían las páginas, **para** poder comprobar el resultado antes de aprobarlo.
		- **C1 - Propone**
		  DADO QUE hay un duplicado real localizado,
		  CUANDO le pido solucionarlo,
		  ENTONCES me presenta una propuesta concreta de consolidación — cómo quedarán los bloques afectados y dónde queda el contenido; puede redactar una versión nueva que combine las aportaciones, sin limitarse a elegir una versión existente y descartar otra.
		- **C2 - Cómo quedaría**
		  DADO QUE me presenta la propuesta,
		  CUANDO la reviso,
		  ENTONCES veo el diff de todas las páginas afectadas (cómo queda cada una).
		- **C3 - Nada se pierde**
		  DADO QUE apruebo la consolidación y se ejecuta,
		  CUANDO abro la página que recibe el contenido,
		  ENTONCES  sigue todo lo que aportaban las páginas de origen — también los detalles únicos de cada versión.
		- **C4 - Queda limpio**
		  DADO QUE la consolidación se ejecutó,
		  CUANDO le pido de nuevo los duplicados de ese tema,
		  ENTONCES ya no señala ese contenido. (si faltó recortar una página, salta).
		- **C5 - Decisiones explícitas**
		  DADO QUE las versiones contienen diferencias que no pueden resolverse con la información disponible,
		  CUANDO el agente propone consolidarlas,
		  ENTONCES hace explícitas esas diferencias y las decisiones pendientes, conserva las variantes necesarias o me pide la decisión que falta; no elige ni elimina una variante silenciosamente ni presenta una suposición como un hecho.
---
## RNFs
   (Cómo de bien lo hace(calidad) o bajo qué límites(restricción).
	- RNF-01
	  > **Como** dueño de la KB, **quiero** que todo lo que hace el agente quede en la traza y sea consultable, **para** poder auditar sus acciones y confiar en lo que hizo."
		- **C1 - Todo en la traza**
		  DADO QUE el run ha terminado,
		  CUANDO abro la traza,
		  ENTONCES veo cada escritura/borrado con mi decisión (aprobado/rechazado) y su resultado.
---
