#!/usr/bin/env python3
"""Candado: un POV o un "Cuando…" no cierra con dos puntos. Correr: python3 scripts/test_frases.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frases import sin_dos_puntos

casos = [
    ("POV: tu tío se sabe el corrido completo y tú ni sabías: 🙈💙", "POV: tu tío se sabe el corrido completo y tú ni sabías 🙈💙"),
    ("Cuando la cumbia se vuelve perreo y nadie se queda sentado: 🙊💙", "Cuando la cumbia se vuelve perreo y nadie se queda sentado 🙊💙"),
    ("cómo cuando el DJ se pone navideño:", "cómo cuando el DJ se pone navideño"),
    ("POV: eres el DJ de la facultad de psicología 🙊💙", "POV: eres el DJ de la facultad de psicología 🙊💙"),
    ("Yo: ya me voy, mañana trabajo / El DJ: 🙊💙", "Yo: ya me voy, mañana trabajo / El DJ: 🙊💙"),
    ("Las mezclas que hace el DJ cuando estoy en el baño: 🙈💙", "Las mezclas que hace el DJ cuando estoy en el baño: 🙈💙"),
    ("POV: son las 3 am y el DJ hace esto:\nTE ESTOY DICIENDO 💙", "POV: son las 3 am y el DJ hace esto:\nTE ESTOY DICIENDO 💙"),
]
mal = [(a, sin_dos_puntos(a), b) for a, b in casos if sin_dos_puntos(a) != b]

# Revisión de cargar: copias fuera, renglón largo castigado, se respetan las de TRAGO.
from frases import revisar, elegir, ejemplos, plano
refs = ejemplos()
if plano("Yo: ya no voy a salir / La dj: (5.4 M)") not in refs:
    mal.append(("banco-djs.md", "no se leyó", "ejemplos del banco"))
f = lambda t, nota=8, trago=False: {"t": t, "nota": nota, "trago": trago}
for t, esperado in [("Yo: ya no voy a salir / La DJ: 🙊💙", None),
                    ("Mi tía pidió otra ronda / La DJ: 💙", 8),
                    ("Mi tía pidió otra ronda de tequila con limón y sal porque según ella hoy sí se baila hasta el amanecer: 💙", 5)]:
    if revisar(f(t), refs) != esperado:
        mal.append((t, revisar(f(t), refs), esperado))
cands = [f("a", 9), f("b", 8), f("c", 7, True), f("d", 3, True), f("e", 6)]
if [x["t"] for x in elegir(cands, 3, 1)] != ["c", "a", "b"]:
    mal.append(("elegir", [x["t"] for x in elegir(cands, 3, 1)], ["c", "a", "b"]))
for a, r, b in mal:
    print("FALLA", repr(a), "->", repr(r), "esperado", repr(b))
print("bien" if not mal else "%d fallas" % len(mal))
sys.exit(1 if mal else 0)
