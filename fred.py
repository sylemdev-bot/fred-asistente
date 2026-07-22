# -- coding: utf-8 --
# =========================================================
#   FRED  -  Tu asistente personal por voz (estilo Jarvis)
#   Con interfaz visual (orbe), pausa de micrófono y charla abierta
# =========================================================
import os
import json
import asyncio
import tempfile
import webbrowser
import datetime
import threading
import math
import tkinter as tk

import speech_recognition as sr
import edge_tts
import pygame
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# ----------------- CONFIGURACIÓN -----------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOMBRE = "Fred"
VOZ = "es-MX-JorgeNeural"
ARCHIVO_MEMORIA = "memoria.json"
MODELO = "gemini-flash-latest"

# Rutas de apps de escritorio. Xbox y Steam usan protocolos que Windows
# reconoce directo. Unity Hub varía según instalación: ajusta la ruta
# de abajo a donde esté instalado en TU compu si el comando no funciona.
RUTA_UNITY_HUB = r"C:\Program Files\Unity Hub\Unity Hub.exe"

genai.configure(api_key=GEMINI_API_KEY)

# ----------------- MEMORIA (te conoce) -----------------
def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"sobre_ti": []}

def guardar_memoria(mem):
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memoria = cargar_memoria()

# ----------------- PERSONALIDAD -----------------
PERSONALIDAD = f"""
Eres {NOMBRE}, el asistente personal por voz del señor.
Hablas SIEMPRE en español, con un tono cálido, cercano y elegante.
Te diriges a él como "señor", con el respeto de un mayordomo,
pero lo quieres como si fuera tu hijo: eres protector, lo animas,
te alegras por él y le das consejos sinceros y honestos.

Eres un compañero de conversación completo: puedes platicar de cualquier
tema (cómo le fue en el día, sus planes, sus dudas), responder preguntas
de cultura general, resolver operaciones matemáticas simples, dar consejos,
opinar, contar datos curiosos, o simplemente charlar sin motivo. NUNCA
digas que no puedes responder algo o que no tienes esa información si es
una pregunta razonable (matemáticas, trivia, opiniones, charla casual);
intenta siempre dar una respuesta útil y natural, como lo haría una
persona culta y cercana.

Respondes CORTO y natural, como en una plática hablada (1 a 3 frases),
porque tus respuestas se van a leer en voz alta.
No uses emojis ni formato, solo texto para hablar.
"""

def contexto_memoria():
    datos = "\n".join(memoria["sobre_ti"]) or "Aún no sé mucho de él."
    return f"Cosas que sé del señor:\n{datos}"

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

modelo = genai.GenerativeModel(MODELO, system_instruction=PERSONALIDAD,
                                safety_settings=SAFETY_SETTINGS)
chat = modelo.start_chat(history=[])

# ----------------- INTERFAZ VISUAL (ORBE) -----------------
class VentanaFred:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Fred")
        self.ventana.geometry("300x300")
        self.ventana.configure(bg="#0d0d0d")

        self.canvas = tk.Canvas(self.ventana, width=300, height=300,
                                 bg="#0d0d0d", highlightthickness=0)
        self.canvas.pack()

        self.radio_base = 60
        self.orbe = self.canvas.create_oval(
            150 - self.radio_base, 150 - self.radio_base,
            150 + self.radio_base, 150 + self.radio_base,
            fill="#112233", outline="#33aaff"
        )
        self.texto_estado = self.canvas.create_text(
            150, 260, text="En espera...", fill="#55ccff",
            font=("Segoe UI", 11)
        )

        self.hablando = False
        self.microfono_activo = True
        self.fase = 0
        self._animar()

        self.canvas.bind("<Button-1>", self._alternar_microfono)

    def _alternar_microfono(self, event=None):
        self.microfono_activo = not self.microfono_activo
        if self.microfono_activo:
            self.canvas.itemconfig(self.texto_estado, text="Escuchando...")
        else:
            self.canvas.itemconfig(self.texto_estado, text="Micrófono en pausa (clic para reanudar)")

    def _animar(self):
        if self.hablando:
            self.fase += 0.25
            pulso = int(15 * (1 + math.sin(self.fase)))
            r = self.radio_base + pulso
            color = "#33ccff"
        elif not self.microfono_activo:
            r = self.radio_base
            color = "#552222"
        else:
            r = self.radio_base
            color = "#112233"

        self.canvas.coords(
            self.orbe, 150 - r, 150 - r, 150 + r, 150 + r
        )
        self.canvas.itemconfig(self.orbe, fill=color)
        self.ventana.after(40, self._animar)

    def set_hablando(self, activo, texto=None):
        self.hablando = activo
        estado = "Hablando..." if activo else "En espera..."
        if texto:
            estado = texto
        self.canvas.itemconfig(self.texto_estado, text=estado)

    def iniciar(self):
        self.ventana.mainloop()

ui = VentanaFred()

# ----------------- VOZ (TTS) -----------------
pygame.mixer.init()

async def _generar(texto, ruta):
    await edge_tts.Communicate(texto, VOZ).save(ruta)

def hablar(texto):
    print(f"{NOMBRE}: {texto}")
    ui.set_hablando(True, "Hablando...")
    ruta = os.path.join(tempfile.gettempdir(), "fred.mp3")
    asyncio.run(_generar(texto, ruta))
    pygame.mixer.music.load(ruta)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()
    ui.set_hablando(False, "En espera...")

# ----------------- OÍDO (STT) -----------------
reconocedor = sr.Recognizer()
mic = sr.Microphone()

def escuchar():
    if not ui.microfono_activo:
        pygame.time.wait(300)
        return ""

    ui.set_hablando(False, "Escuchando...")

    with mic as fuente:
        reconocedor.adjust_for_ambient_noise(fuente, duration=0.3)
        reconocedor.pause_threshold = 1.0
        try:
            audio = reconocedor.listen(fuente, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            return ""
        except Exception:
            return ""

    ui.set_hablando(False, "Pensando...")
    try:
        return reconocedor.recognize_google(audio, language="es-MX").lower()
    except Exception:
        return ""

# ----------------- ACCIONES -----------------
def ejecutar_accion(cmd):
    if "youtube" in cmd:
        webbrowser.open("https://youtube.com")
        hablar("Enseguida, señor. Abriendo YouTube.")
        return True

    if "spotify" in cmd:
        webbrowser.open("https://open.spotify.com")
        hablar("Abriendo Spotify, señor.")
        return True

    if "busca en google" in cmd or "buscar en google" in cmd:
        consulta = cmd.replace("busca en google", "").replace("buscar en google", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={consulta}")
        hablar(f"Buscando {consulta}, señor.")
        return True

    if "google" in cmd:
        webbrowser.open("https://google.com")
        hablar("Listo, señor.")
        return True

    if "qué hora" in cmd or "que hora" in cmd:
        hora = datetime.datetime.now().strftime("%I:%M")
        hablar(f"Son las {hora}, señor.")
        return True

    if "qué día" in cmd or "que dia" in cmd or "fecha" in cmd:
        fecha = datetime.datetime.now().strftime("%d de %B")
        hablar(f"Hoy es {fecha}, señor.")
        return True

    if "abre mis documentos" in cmd or "abre documentos" in cmd:
        os.startfile(os.path.expanduser("~\\Documents"))
        hablar("Abriendo sus documentos, señor.")
        return True

    if "abre el escritorio" in cmd or "abre mi escritorio" in cmd:
        os.startfile(os.path.expanduser("~\\Desktop"))
        hablar("Abriendo su escritorio, señor.")
        return True

    if "abre xbox" in cmd or "abre el xbox" in cmd:
        os.startfile("ms-xbox:")
        hablar("Abriendo la app de Xbox, señor.")
        return True

    if "abre steam" in cmd:
        os.startfile("steam:")
        hablar("Abriendo Steam, señor.")
        return True

    if "abre unity" in cmd:
        try:
            os.startfile(RUTA_UNITY_HUB)
            hablar("Abriendo Unity Hub, señor.")
        except Exception:
            hablar("No encontré Unity Hub en esa ruta, señor. Habría que revisar la ubicación en el código.")
        return True

    if "clima" in cmd or "temperatura" in cmd:
        try:
            resp = requests.get("https://wttr.in/?format=3&lang=es", timeout=6)
            hablar(f"Señor, {resp.text.strip()}")
        except Exception:
            hablar("No pude consultar el clima en este momento, señor.")
        return True

    return False

# ----------------- CEREBRO (IA) -----------------
def responder(cmd):
    prompt = f"{contexto_memoria()}\n\nEl señor dijo: {cmd}"
    texto = None
    intentos = 3
    for intento in range(intentos):
        try:
            texto = chat.send_message(prompt).text.strip()
            break
        except Exception as e:
            error_str = str(e)
            print("Error IA:", error_str)
            if "429" in error_str and intento < intentos - 1:
                pygame.time.wait(4000)
                continue
            texto = "Disculpe, señor, tuve un problema para pensar eso. Intentemos de nuevo en un momento."
            break
    hablar(texto)

# ----------------- BUCLE PRINCIPAL (en segundo plano) -----------------
def bucle_fred():
    hablar(f"A sus órdenes, señor. {NOMBRE} está despierto.")
    while True:
        texto = escuchar()
        if not texto:
            continue
        print(f"Tú: {texto}")

        if NOMBRE.lower() not in texto:
            continue

        cmd = texto.replace(NOMBRE.lower(), "").strip()

        if "adiós" in cmd or "hasta luego" in cmd or "duérmete" in cmd:
            hablar("Que descanse, señor. Aquí estaré.")
            break

        if cmd.startswith("recuerda que"):
            dato = cmd.replace("recuerda que", "").strip()
            memoria["sobre_ti"].append(dato)
            guardar_memoria(memoria)
            hablar("Lo tendré presente, señor.")
            continue

        if not ejecutar_accion(cmd):
            responder(cmd)

if __name__ == "__main__":
    hilo = threading.Thread(target=bucle_fred, daemon=True)
    hilo.start()
    ui.iniciar()