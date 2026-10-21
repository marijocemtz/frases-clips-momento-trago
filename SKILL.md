---
name: frases-clips-momento-trago
description: Genera FRASES CLIPS MOMENTO TRAGO. (frases para clips de los DJ sets de TRAGO.) y aprende de los likes y dislikes del equipo. Úsala cuando digan "vamos a generar frases para MOMENTO TRAGO.", "frases para DJ set", "frases para clips", "/frases", o pidan abrir el banco de frases aprobadas o sus listas.
---

# FRASES CLIPS MOMENTO TRAGO.

Claude solo hace lo creativo. Todo lo demás lo hace `scripts/frases.py` (sin gastar tokens). En los comandos, cambia `S` por la carpeta base de esta skill (Claude Code la muestra al cargarla; normalmente `~/.claude/skills/frases-clips-momento-trago`). Habla en español, tuteando, corto y sin palabras técnicas.

## 1. Inicio
```bash
python3 "S/scripts/frases.py" inicio
```
- Si `sesion_pendiente` es true: quedó una ronda sin Terminé. Corre `cierre` (paso 5) antes de seguir.
- Si `repo` dice que no pudo bajar lo nuevo, avisa en una línea y sigue.

## 2. Preguntas
Pregunta con AskUserQuestion, todo en una sola llamada (solo lo que no te hayan dicho ya):
- **Temática** (texto libre; da 3-4 ideas como opciones).
- **Contexto** (opcional; ofrece "Sin contexto").
- **Cuántas**: 1, 10, 15, 20, 30 o la que escriban (máx. 100).
- **% que se refiere al local TRAGO.**: 0, 20, 40 o 60.

## 3. Generar
```bash
python3 "S/scripts/frases.py" prompt --tema "…" --contexto "…" --n 15 --pct 40
```
Devuelve `prompt`, `salida` y `modelo`. Lanza UN subagente (Agent, `subagent_type: general-purpose`, `model` = el `modelo` que devolvió: "haiku" o "sonnet") con este encargo exacto:
> Lee el archivo `<prompt>` y sigue sus instrucciones. Escribe tu respuesta, y nada más, en `<salida>` con la herramienta Write. Responde solo "listo".

No leas el prompt tú. Di en una línea "Escribiendo las frases…" y espera el aviso de que el subagente terminó (no leas su transcripción). Luego:
```bash
python3 "S/scripts/frases.py" cargar
```
Si falla, relanza el subagente una vez.

## 4. Página
Corre en **segundo plano** (`run_in_background: true`):
```bash
python3 "S/scripts/frases.py" servir
```
Abre la página en el navegador. Di en una línea: "Te abrí la página: dale 👍 o 👎 y pica Terminé cuando acabes." y termina tu turno. Cuando picas Terminé el comando acaba y te despierta solo. No lo vigiles ni lo leas mientras corre.

Para solo ver el banco o acomodar listas (sin generar): `servir --solo-banco` en segundo plano.

## 5. Cierre (cuando `servir` termina, o al inicio si quedó pendiente)
```bash
python3 "S/scripts/frases.py" cierre
```
Ya borra las sin calificar, guarda la ronda y sube aprobadas y listas al repo. Con su salida:

**Reglas nuevas** (solo si hay `dislikes`):
1. Compara cada razón con `reglas_aprendidas` y con las reglas base de `references/reglas.md` que apliquen.
   - Misma idea que una regla existente: no escribas otra; suma el ejemplo a esa línea (`… (ej. "frase")`).
   - Choca con una regla vieja: pregunta cuál se queda.
   - Idea nueva: redáctala en una línea, concreta y accionable.
2. Mira también `likes_textos`: si varias aprobadas comparten una mecánica clara que no está escrita, propón una regla de "esto sí funciona".
3. Enséñalas en el chat, una línea cada una, y di cuáles solo sumaron ejemplo. Espera su ok.
4. Con el ok, edita la sección `## Reglas aprendidas` de `references/reglas.md` (una línea `- ` por regla) y sube:
   ```bash
   python3 "S/scripts/frases.py" guardar -m "Reglas nuevas: <resumen corto>"
   ```
5. Si hay más de `tope_reglas` reglas aprendidas, propón juntar las parecidas y aplica solo con ok.

**Modelo**: si `evaluacion` es `PROPONER_SONNET`, di: "Las últimas 3 rondas salieron con más de la mitad en 👎 aunque ya agregamos reglas. ¿Cambio a Sonnet 5.5? Gasta más pero escribe mejor." Con ok: `frases.py modelo sonnet`. Si dice que no: `frases.py modelo rechazar`.

Si `guardado` no dice "subido al repo", explica en una línea qué pasó (sin internet, choque con lo de otra persona) y que los datos están a salvo en la compu.

Cierra con una línea: cuántas aprobó y si quiere otra ronda.

## Reglas
- Nunca leas `datos/` completo ni los dislikes viejos: los scripts ya dan la muestra.
- No escribas frases en el chat: siempre van a la página.
- TRAGO. y MOMENTO TRAGO. siempre con punto.
