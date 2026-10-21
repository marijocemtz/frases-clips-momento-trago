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
for a, r, b in mal:
    print("FALLA", repr(a), "->", repr(r), "esperado", repr(b))
print("bien" if not mal else "%d fallas" % len(mal))
sys.exit(1 if mal else 0)
