# FRASES CLIPS MOMENTO TRAGO.

Skill de Claude Code que escribe frases para los clips de los DJ sets de TRAGO. y aprende de lo que el equipo aprueba o rechaza.

## Instalar
Necesitas Claude Code, Python 3 y la GitHub CLI (`gh`) con sesión iniciada.

```bash
gh repo clone marijocemtz/frases-clips-momento-trago ~/.claude/skills/frases-clips-momento-trago
```

Abre Claude Code y di: "vamos a generar frases para MOMENTO TRAGO."

## Cómo funciona
1. Baja lo nuevo del repo.
2. Te pregunta temática, contexto (opcional), cuántas (1 a 100) y qué porcentaje habla del local TRAGO.
3. Te abre una página en tu compu (localhost) para dar 👍 o 👎. Con 👎 escribes por qué.
4. Al picar Terminé: las sin calificar se borran, las aprobadas y las listas se suben al repo, y Claude te enseña las reglas nuevas para tu ok.

## Qué hay aquí
- `SKILL.md`: instrucciones para Claude.
- `references/reglas.md`: tono, mecanismos y reglas aprendidas.
- `references/banco.md`: frases de referencia.
- `scripts/frases.py`: todo lo mecánico (sin gastar Claude).
- `scripts/app.html`: la página.
- `datos/`: aprobadas, listas, dislikes, rondas y el modelo (`config.json`). Un archivo por frase para que no choquen dos personas guardando.

El primer mes usa Haiku 5.5; si 3 rondas seguidas salen con más de la mitad en 👎, propone pasar a Sonnet 5.5.
