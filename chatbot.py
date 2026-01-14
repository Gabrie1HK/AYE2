"""
Modulo de Chatbot IA
Traduce lenguaje natural a comandos usando Gemini.
"""

import os
import re

import google.generativeai as genai
from dotenv import load_dotenv

from configuracion import Configuracion

# Cargar variables de entorno desde .env
load_dotenv()


class ChatbotIA:
    """
    Chatbot que usa la API de Gemini para interpretar lenguaje natural.

    Actúa como un adaptador entre el sistema local y la API externa de IA,
    traduciendo la intención del usuario a comandos técnicos que el sistema pueda entender.
    """

    def __init__(self, config: Configuracion):
        self.config = config
        self.modelo = self._inicializar_modelo()

    def _inicializar_modelo(self):
        """Inicializa el modelo de Gemini"""
        try:
            api_key_actual = os.getenv("GEMINI_API_KEY")

            if not api_key_actual:
                print("ADVERTENCIA: No se encontró la variable de entorno GEMINI_API_KEY en el archivo .env")
                return None

            genai.configure(api_key=api_key_actual)
            modelo_configurado = self.config.obtener_modelo_ia()
            return genai.GenerativeModel(modelo_configurado)
        except Exception as e:
            print(f"Error inicializando modelo IA: {e}")
            return None

    def interpretar_comando(self, texto_usuario: str) -> str:
        """Interpreta lenguaje natural y devuelve comando"""
        if not self.config.datos["habilitar_chatbot"]:
            return "ERROR: Chatbot desactivado"

        if not self.modelo:
            return "ERROR: Modelo IA no inicializado (Verifica tu API KEY)"

        try:
            prompt = self._crear_prompt_interpretacion(texto_usuario)
            respuesta = self.modelo.generate_content(prompt)
            comando = respuesta.text.strip()
            comando = comando.replace("`", "").replace("bash", "").strip()
            return self._validar_comando(comando)
        except Exception as e:
            print(f"\n[DEBUG] Error de conexión con Gemini API: {e}")
            print("[DEBUG] Intentando usar interpretación local de respaldo...\n")
            return self._fallback_interpretar(texto_usuario)

    def _fallback_interpretar(self, texto: str) -> str:
        """Interprete simple de lenguaje natural a comandos (solo si falla internet/API)."""
        texto_l = texto.lower()

        if "crear" in texto_l and "carpeta" in texto_l:
            match = re.search(r"llamada\s+([\w\.]+)", texto_l)
            if match:
                return f"mkdir {match.group(1)}"
            parts = texto_l.split()
            return f"mkdir {parts[-1]}"

        if any(x in texto_l for x in ["abre", "ir a", "cambia", "entra", "muevete", "muévete"]):
            if ".." in texto_l or "atras" in texto_l or "anterior" in texto_l:
                return "cd .."

            palabras = texto_l.split()
            ignorar = ["la", "carpeta", "a", "el", "directorio", "muevete", "muévete", "entra", "en"]
            posibles_nombres = [p for p in palabras if p not in ignorar]

            if posibles_nombres:
                return f"cd {posibles_nombres[-1]}"

        if "que hay" in texto_l or "listar" in texto_l or "muestra" in texto_l:
            return "dir"

        if "historial" in texto_l and ("limpia" in texto_l or "borrar" in texto_l):
            return "clear log"
        if "historial" in texto_l:
            return "log"

        return "ERROR"

    def _crear_prompt_interpretacion(self, texto: str) -> str:
        """Crea el prompt para la interpretacion"""
        return f"""
        Actúa como un traductor de comandos para un sistema de archivos simulado en Python.
        Tu única tarea es convertir la frase del usuario en un comando técnico exacto.

        COMANDOS DISPONIBLES:
        - cd <ruta>
        - mkdir <nombre>
        - type <nombre> "<contenido>"
        - rmdir <nombre>  (añade /s si implica borrar todo o forzar)
        - dir <ruta>
        - log
        - clear log

        EJEMPLOS:
        Usuario: "Crea una carpeta llamada Fotos" -> Respuesta: mkdir Fotos
        Usuario: "Muévete a la carpeta Fotos" -> Respuesta: cd Fotos
        Usuario: "Entra en documentos" -> Respuesta: cd Documentos
        Usuario: "Que hay aqui?" -> Respuesta: dir
        Usuario: "Borra la carpeta temporal" -> Respuesta: rmdir /s Temporal
        Usuario: "Limpia el historial" -> Respuesta: clear log
        Usuario: "Crea notas.txt que diga hola" -> Respuesta: type notas.txt "hola"

        ENTRADA DEL USUARIO: "{texto}"

        RESPUESTA (SOLO EL COMANDO, SIN EXPLICACIONES):
        """

    def _validar_comando(self, comando: str) -> str:
        """Valida que el comando generado sea valido"""
        comandos_validos = [
            "cd",
            "mkdir",
            "type",
            "rmdir",
            "dir",
            "log",
            "clear log",
            "index",
        ]
        if not comando:
            return "ERROR"

        comando_base = comando.split()[0].lower()
        if comando_base in comandos_validos:
            return comando
        return "ERROR"
