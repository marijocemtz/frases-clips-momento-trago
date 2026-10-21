#!/usr/bin/env python3
"""FRASES CLIPS MOMENTO TRAGO.: todo lo mecánico de la skill (sin gastar Claude).

Comandos:
  inicio                         baja lo nuevo del repo y dice cómo está todo
  prompt --tema T [--contexto C] --n N --pct P
                                 arma el pedido para el generador en .sesion/prompt.md
  cargar                         lee .sesion/salida.jsonl (lo que escribió el generador)
  servir                         abre la página en localhost y espera a que piquen Terminé
  cierre                         borra pendientes, guarda dislikes y la ronda, sube al repo
  guardar -m "mensaje"           sube datos y reglas al repo (con fila si alguien guardó antes)
  modelo haiku|sonnet|rechazar   cambia el modelo o rechaza la propuesta de cambio
"""
import argparse, datetime, getpass, json, os, random, re, subprocess, sys, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, "datos")
SESION = os.path.join(RAIZ, ".sesion")
REFS = os.path.join(RAIZ, "references")
CONFIG = os.path.join(DATOS, "config.json")
CONFIG_BASE = {"modelo": "haiku", "prueba_inicio": None, "prueba_dias": 30,
               "umbral_rondas": 3, "umbral_dislike": 0.5, "rechazado_en": None, "tope_reglas": 40}
INACTIVO_SEG = 3 * 3600


# ---------- utilidades ----------
def ahora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def nuevo_id():
    return "%x%04x" % (int(time.time() * 1000), random.randrange(65536))


def leer(p, defecto=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defecto


def escribir(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def carpeta(nombre):
    p = os.path.join(DATOS, nombre)
    os.makedirs(p, exist_ok=True)
    return [x for x in (leer(os.path.join(p, f)) for f in sorted(os.listdir(p)) if f.endswith(".json")) if x]


def git(*args, check=False):
    r = subprocess.run(["git", "-C", RAIZ] + list(args), capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError((r.stderr or r.stdout).strip())
    return r


def autor():
    n = git("config", "user.name").stdout.strip()
    return n or getpass.getuser()


def config():
    c = dict(CONFIG_BASE)
    c.update(leer(CONFIG, {}))
    return c


def reglas_aprendidas():
    try:
        s = open(os.path.join(REFS, "reglas.md"), encoding="utf-8").read()
    except OSError:
        return []
    parte = s.split("## Reglas aprendidas", 1)[-1] if "## Reglas aprendidas" in s else ""
    return [l for l in parte.splitlines() if l.startswith("- ")]


# ---------- inicio ----------
def cmd_inicio(_):
    r = git("pull", "--rebase", "--autostash")
    bajo = "sin repo remoto" if r.returncode and "no tracking" in (r.stderr + r.stdout) else \
        ("no pude bajar lo nuevo: " + (r.stderr or r.stdout).strip()[:200] if r.returncode else "al día")
    c = config()
    pendiente = os.path.exists(os.path.join(SESION, "ronda.json"))
    prueba = "sin empezar"
    if c["prueba_inicio"]:
        dias = (datetime.date.today() - datetime.date.fromisoformat(c["prueba_inicio"][:10])).days
        prueba = "terminada" if dias > c["prueba_dias"] else "día %d de %d" % (dias + 1, c["prueba_dias"])
    print(json.dumps({
        "repo": bajo, "modelo": c["modelo"], "prueba_modelo": prueba,
        "aprobadas": len(carpeta("aprobadas")), "listas": len(carpeta("listas")),
        "reglas_aprendidas": len(reglas_aprendidas()), "tope_reglas": c["tope_reglas"],
        "sesion_pendiente": pendiente}, ensure_ascii=False, indent=1))


# ---------- prompt ----------
def muestra(tema):
    aprob = sorted(carpeta("aprobadas"), key=lambda g: g.get("creada", ""), reverse=True)
    tema_l = (tema or "").lower()
    elegidas, vistos = [], set()
    def tomar(lista, tope):
        n = 0
        for g in lista:
            if n >= tope:
                break
            if g["id"] not in vistos:
                vistos.add(g["id"]); elegidas.append(g); n += 1
    tomar([g for g in aprob if g.get("fav")], 15)
    tomar([g for g in aprob if tema_l and tema_l in (g.get("tema") or "").lower()], 15)
    tomar(aprob, 20)
    return elegidas


def ya_salieron():
    rondas = sorted(carpeta("rondas"), key=lambda r: r.get("fecha", ""), reverse=True)
    textos = []
    for r in rondas:
        textos += r.get("frases", [])
        if len(textos) >= 100:
            break
    return textos[:100]


def cmd_prompt(a):
    n = max(1, min(100, a.n))
    pct = max(0, min(100, a.pct))
    n_trago = round(n * pct / 100)
    reglas = open(os.path.join(REFS, "reglas.md"), encoding="utf-8").read()
    banco = open(os.path.join(REFS, "banco.md"), encoding="utf-8").read()
    p = [reglas, "", banco]
    m = muestra(a.tema)
    if m:
        p += ["", "# Aprobadas por el equipo (haz más con esta mecánica, sin repetirlas)"]
        p += ["- %s%s%s" % ("★ " if g.get("fav") else "", g["t"], " [IMAGEN: %s]" % g["img"] if g.get("img") else "") for g in m]
    previas = ya_salieron()
    if previas:
        p += ["", "# Ya salieron en rondas pasadas (no las repitas ni cambies solo palabras)"] + ["- " + t for t in previas]
    if n_trago == 0:
        con = "ninguna menciona TRAGO."
    elif n_trago == n:
        con = "todas se refieren al local TRAGO. de forma natural"
    else:
        con = "exactamente %d de %d se refieren al local TRAGO.; las otras %d no lo mencionan. Repártelas." % (n_trago, n, n - n_trago)
    p += ["", "# Pedido de hoy",
          "Temática: " + a.tema,
          "Contexto: " + (a.contexto or "(sin contexto: frases para probar voz y públicos)"),
          "Cantidad: " + ("1 sola frase, la mejor que tengas." if n == 1 else "%d frases." % n),
          "Con TRAGO.: " + con,
          "", "# Formato de salida (obligatorio)",
          "Una frase por línea, cada línea un objeto JSON y nada más; sin numerar, sin texto antes ni después:",
          '{"t": "texto de la frase con sus emojis al final 🙊💙", "img": "", "trago": false}',
          'Usa "img" solo si una imagen completa el chiste (descripción breve, ej. "vaso de TRAGO."). "trago" es true si la frase o su imagen se refieren al local.']
    os.makedirs(SESION, exist_ok=True)
    with open(os.path.join(SESION, "prompt.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(p) + "\n")
    escribir(os.path.join(SESION, "pedido.json"), {"tema": a.tema, "contexto": a.contexto or "", "n": n, "pct": pct,
                                                   "n_trago": n_trago, "modelo": config()["modelo"], "creada": ahora()})
    sal = os.path.join(SESION, "salida.jsonl")
    if os.path.exists(sal):
        os.remove(sal)
    print(json.dumps({"prompt": os.path.join(SESION, "prompt.md"), "salida": sal, "n": n, "n_trago": n_trago,
                      "modelo": config()["modelo"]}, ensure_ascii=False))


# ---------- cargar ----------
def sin_dos_puntos(t):
    """Un POV o un "Cuando…" de un renglón no cierra con ":" (el clip es la escena)."""
    if "/" in t or "\n" in t or not re.match(r"(pov\b|(c[oó]mo )?cuando\b)", t, re.I):
        return t
    return re.sub(r"\s*:(\s*[^\w\s\"'”»)]*)$", r"\1", t)


def cmd_cargar(_):
    sal = os.path.join(SESION, "salida.jsonl")
    pedido = leer(os.path.join(SESION, "pedido.json"))
    if not pedido or not os.path.exists(sal):
        sys.exit("No hay salida del generador en " + sal)
    ronda = []
    for linea in open(sal, encoding="utf-8"):
        linea = linea.strip().rstrip(",")
        if not linea.startswith("{"):
            continue
        try:
            o = json.loads(linea)
        except ValueError:
            continue
        t = sin_dos_puntos(str(o.get("t") or o.get("texto") or "").strip())
        if not t:
            continue
        img = str(o.get("img") or "").strip()
        ronda.append({"id": nuevo_id(), "t": t, "img": img, "trago": o.get("trago") is True or "TRAGO" in t + img,
                      "estado": None, "razon": ""})
    if not ronda:
        sys.exit("El generador no dejó ninguna frase válida.")
    escribir(os.path.join(SESION, "ronda.json"), {"id": nuevo_id(), "pedido": pedido, "frases": ronda})
    c = config()
    if not c["prueba_inicio"]:
        c["prueba_inicio"] = ahora()
        escribir(CONFIG, c)
    print(json.dumps({"frases": len(ronda), "con_trago": sum(f["trago"] for f in ronda)}))


# ---------- servir ----------
class Estado:
    lock = threading.Lock()
    ultimo = time.time()
    terminado = threading.Event()


def ronda_actual():
    return leer(os.path.join(SESION, "ronda.json"), {"frases": [], "pedido": {}})


def ruta_aprob(i):
    return os.path.join(DATOS, "aprobadas", re.sub(r"[^0-9a-z]", "", i) + ".json")


def ruta_lista(i):
    return os.path.join(DATOS, "listas", re.sub(r"[^0-9a-z]", "", i) + ".json")


def api(ruta, d):
    if ruta == "/api/estado":
        r = ronda_actual()
        return {"ronda": r["frases"], "pedido": r.get("pedido", {}), "aprobadas": carpeta("aprobadas"),
                "listas": carpeta("listas"), "autor": autor()}
    if ruta == "/api/calificar":
        r = ronda_actual()
        f = next((x for x in r["frases"] if x["id"] == d.get("id")), None)
        if not f:
            return {"error": "no existe"}
        f["estado"] = d.get("estado")
        f["razon"] = (d.get("razon") or "")[:500] if f["estado"] == "no" else ""
        escribir(os.path.join(SESION, "ronda.json"), r)
        p = ruta_aprob(f["id"])
        if f["estado"] == "si" and not os.path.exists(p):
            ped = r.get("pedido", {})
            escribir(p, {"id": f["id"], "t": f["t"], "img": f["img"], "trago": f["trago"], "tema": ped.get("tema", ""),
                         "contexto": ped.get("contexto", ""), "fav": False, "lista": "", "autor": autor(), "creada": ahora()})
        elif f["estado"] != "si" and os.path.exists(p):
            os.remove(p)
        return {"ok": True}
    if ruta == "/api/aprobada":
        p = ruta_aprob(d.get("id", ""))
        g = leer(p)
        if not g:
            return {"error": "no existe"}
        for k in ("fav", "lista"):
            if k in d:
                g[k] = d[k]
        escribir(p, g)
        return {"ok": True}
    if ruta == "/api/tirar":
        p = ruta_aprob(d.get("id", ""))
        if os.path.exists(p):
            os.remove(p)
        return {"ok": True}
    if ruta == "/api/lista":
        nombre = (d.get("nombre") or "").strip()[:60]
        if not nombre:
            return {"error": "falta nombre"}
        i = nuevo_id()
        escribir(ruta_lista(i), {"id": i, "nombre": nombre, "autor": autor(), "creada": ahora()})
        return {"ok": True, "id": i}
    if ruta == "/api/borrar-lista":
        i = d.get("id", "")
        for g in carpeta("aprobadas"):
            if g.get("lista") == i:
                g["lista"] = ""
                escribir(ruta_aprob(g["id"]), g)
        if os.path.exists(ruta_lista(i)):
            os.remove(ruta_lista(i))
        return {"ok": True}
    if ruta == "/api/terminar":
        Estado.terminado.set()
        return {"ok": True}
    return {"error": "ruta desconocida"}


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def responder(self, cuerpo, tipo="application/json; charset=utf-8", codigo=200):
        b = cuerpo if isinstance(cuerpo, bytes) else json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        Estado.ultimo = time.time()
        if self.path in ("/", "/index.html"):
            with open(os.path.join(RAIZ, "scripts", "app.html"), "rb") as f:
                return self.responder(f.read(), "text/html; charset=utf-8")
        if self.path == "/api/estado":
            with Estado.lock:
                return self.responder(api("/api/estado", {}))
        self.responder({"error": "no encontrado"}, codigo=404)

    def do_POST(self):
        Estado.ultimo = time.time()
        n = int(self.headers.get("Content-Length") or 0)
        try:
            d = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            d = {}
        with Estado.lock:
            self.responder(api(self.path, d))


def cmd_servir(a):
    if not os.path.exists(os.path.join(SESION, "ronda.json")) and not a.solo_banco:
        sys.exit("No hay ronda cargada.")
    srv = ThreadingHTTPServer(("127.0.0.1", a.puerto), Manejador)
    url = "http://localhost:%d/" % srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("Página abierta en " + url, flush=True)
    if not a.no_abrir:
        webbrowser.open(url)
    while not Estado.terminado.wait(5):
        if time.time() - Estado.ultimo > INACTIVO_SEG:
            print("INACTIVO: se cerró sola tras 3 horas sin uso.", flush=True)
            break
    else:
        time.sleep(0.5)
        print("TERMINADO", flush=True)
    srv.shutdown()


# ---------- cierre ----------
def evaluar(c):
    if c["modelo"] != "haiku" or not c["prueba_inicio"]:
        return None
    dias = (datetime.date.today() - datetime.date.fromisoformat(c["prueba_inicio"][:10])).days
    if dias > c["prueba_dias"]:
        return None
    rondas = sorted([r for r in carpeta("rondas") if r.get("modelo") == "haiku"
                     and (not c["rechazado_en"] or r.get("fecha", "") > c["rechazado_en"])],
                    key=lambda r: r.get("fecha", ""))
    ult = rondas[-c["umbral_rondas"]:]
    if len(ult) < c["umbral_rondas"]:
        return None
    malas = [r for r in ult if (r["likes"] + r["dislikes"]) and r["dislikes"] / (r["likes"] + r["dislikes"]) > c["umbral_dislike"]]
    return "PROPONER_SONNET" if len(malas) == len(ult) else None


def cmd_cierre(a):
    r = leer(os.path.join(SESION, "ronda.json"))
    if not r:
        print(json.dumps({"cerrada": False, "motivo": "no había sesión abierta"}))
        return
    fr = r["frases"]
    likes = [f for f in fr if f["estado"] == "si"]
    dislikes = [f for f in fr if f["estado"] == "no"]
    ped = r.get("pedido", {})
    fecha = ahora()
    if dislikes:
        escribir(os.path.join(DATOS, "dislikes", r["id"] + ".json"),
                 {"ronda": r["id"], "fecha": fecha, "autor": autor(), "tema": ped.get("tema", ""),
                  "frases": [{"t": f["t"], "razon": f["razon"]} for f in dislikes]})
    escribir(os.path.join(DATOS, "rondas", r["id"] + ".json"),
             {"id": r["id"], "fecha": fecha, "autor": autor(), "tema": ped.get("tema", ""), "modelo": ped.get("modelo", ""),
              "n": len(fr), "likes": len(likes), "dislikes": len(dislikes), "frases": [f["t"] for f in fr]})
    for f in os.listdir(SESION):
        os.remove(os.path.join(SESION, f))
    c = config()
    salida = {"cerrada": True, "tema": ped.get("tema", ""), "total": len(fr), "likes": len(likes),
              "sin_calificar_borradas": len(fr) - len(likes) - len(dislikes),
              "dislikes": [{"t": f["t"], "razon": f["razon"] or "(sin razón)"} for f in dislikes],
              "likes_textos": [f["t"] for f in likes],
              "reglas_aprendidas": reglas_aprendidas(), "tope_reglas": c["tope_reglas"],
              "evaluacion": evaluar(c)}
    salida["guardado"] = guardar("Ronda %s: %d aprobadas, %d dislikes (%s)" % (ped.get("tema", ""), len(likes), len(dislikes), autor()))
    print(json.dumps(salida, ensure_ascii=False, indent=1))


# ---------- guardar ----------
def guardar(msg):
    if git("rev-parse", "--is-inside-work-tree").returncode:
        return "no es repo git"
    git("add", "-A", ".")
    if git("diff", "--cached", "--quiet").returncode:
        git("commit", "-q", "-m", msg)
    if not git("remote").stdout.strip():
        return "guardado en tu compu (sin repo remoto)"
    for intento in range(4):
        if git("push", "-q").returncode == 0:
            return "subido al repo"
        r = git("pull", "--rebase", "--autostash", "-q")
        if r.returncode:
            git("rebase", "--abort")
            return "choque al juntar con lo de otra persona: " + (r.stderr or r.stdout).strip()[:300]
        time.sleep(1 + intento)
    return "no pude subir (revisa la conexión)"


def cmd_guardar(a):
    print(guardar(a.m))


def cmd_modelo(a):
    c = config()
    if a.cual == "rechazar":
        c["rechazado_en"] = ahora()
    else:
        c["modelo"] = a.cual
    escribir(CONFIG, c)
    print(guardar("Modelo: " + (c["modelo"] if a.cual != "rechazar" else "se queda " + c["modelo"])))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("inicio").set_defaults(f=cmd_inicio)
    x = s.add_parser("prompt"); x.set_defaults(f=cmd_prompt)
    x.add_argument("--tema", required=True); x.add_argument("--contexto", default="")
    x.add_argument("--n", type=int, required=True); x.add_argument("--pct", type=int, required=True)
    s.add_parser("cargar").set_defaults(f=cmd_cargar)
    x = s.add_parser("servir"); x.set_defaults(f=cmd_servir)
    x.add_argument("--puerto", type=int, default=0); x.add_argument("--no-abrir", action="store_true")
    x.add_argument("--solo-banco", action="store_true")
    s.add_parser("cierre").set_defaults(f=cmd_cierre)
    x = s.add_parser("guardar"); x.set_defaults(f=cmd_guardar); x.add_argument("-m", required=True)
    x = s.add_parser("modelo"); x.set_defaults(f=cmd_modelo); x.add_argument("cual", choices=["haiku", "sonnet", "rechazar"])
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
