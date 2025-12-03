# sistema_archivos.py
"""
Modulo del Sistema de Archivos - Logica central
Resolucion de rutas, chatbot IA, backup JSON, log
Acoplamiento medio - solo con comandos y entidades
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from estructuras_datos import Pila
from entidades_fs import Carpeta, Archivo
from comandos import (ComandoCD, ComandoMKDIR, ComandoTYPE, 
                     ComandoRMDIR, ComandoDIR, ComandoLOG, ComandoClearLog)

class Configuracion:
    """
    Maneja la configuracion del sistema
    
    Esta clase centraliza todos los parámetros configurables del sistema (persistencia).
    Permite separar la lógica del código de los valores variables (como rutas o API keys),
    facilitando el mantenimiento y la modificación del comportamiento sin tocar el código fuente.
    """
    
    def __init__(self, archivo_config: str = "config.json"):
        self.archivo_config = archivo_config
        self.datos = self._cargar_configuracion()
    
    def _cargar_configuracion(self) -> Dict:
        """Carga la configuracion por defecto o desde archivo"""
        config_por_defecto = {
            "ruta_respaldos": "backups/",
            "comandos_activados": ["cd", "mkdir", "type", "rmdir", "dir", "log", "clear log"],
            "habilitar_chatbot": True,
            "unidad_raiz": "C:",
            "log_operaciones": True,
            "modelo_ia": "gemini-2.5-flash"
        }
        
        try:
            if os.path.exists(self.archivo_config):
                with open(self.archivo_config, 'r') as f:
                    config_cargada = json.load(f)
                    return {**config_por_defecto, **config_cargada}
        except Exception as e:
            print(f"Error cargando configuracion: {e}")
        
        return config_por_defecto
    
    def guardar_configuracion(self) -> bool:
        """Guarda la configuracion en archivo JSON"""
        try:
            with open(self.archivo_config, 'w') as f:
                json.dump(self.datos, f, indent=4)
            return True
        except Exception as e:
            print(f"Error guardando configuracion: {e}")
            return False
    
    def comando_activado(self, comando: str) -> bool:
        """Verifica si un comando esta activado"""
        return comando in self.datos["comandos_activados"]
    
    def obtener_ruta_respaldos(self) -> str:
        """Obtiene la ruta de respaldos"""
        return self.datos["ruta_respaldos"]
    
    def obtener_modelo_ia(self) -> str:
        """Obtiene el modelo de IA configurado"""
        return self.datos.get("modelo_ia", "gemini-2.5-flash")

class ChatbotIA:
    """
    Chatbot que usa la API de Gemini para interpretar lenguaje natural
    
    Esta clase actúa como un 'Adaptador' o interfaz entre nuestro sistema local y la API externa de IA.
    Su función principal es traducir la intención del usuario (lenguaje natural) a comandos técnicos
    que el sistema pueda entender, encapsulando toda la complejidad de la comunicación HTTP y autenticación.
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

        # Intentar usar el modelo remoto
        try:
            prompt = self._crear_prompt_interpretacion(texto_usuario)
            respuesta = self.modelo.generate_content(prompt)
            comando = respuesta.text.strip()
            # Limpieza básica por si el modelo devuelve comillas o markdown
            comando = comando.replace('`', '').replace('bash', '').strip()
            return self._validar_comando(comando)
            
        except Exception as e:
            print(f"\n[DEBUG] Error de conexión con Gemini API: {e}")
            print("[DEBUG] Intentando usar interpretación local de respaldo...\n")
            return self._fallback_interpretar(texto_usuario)

    def _fallback_interpretar(self, texto: str) -> str:
        """Interprete simple de lenguaje natural a comandos (Solo si falla internet/API)."""
        texto_l = texto.lower()

        # Crear carpeta
        if "crear" in texto_l and "carpeta" in texto_l:
            match = re.search(r"llamada\s+([\w\.]+)", texto_l)
            if match: return f"mkdir {match.group(1)}"
            parts = texto_l.split()
            return f"mkdir {parts[-1]}" # Intenta tomar la ultima palabra

        # Cambiar directorio (Añadido 'muevete')
        if any(x in texto_l for x in ["abre", "ir a", "cambia", "entra", "muevete", "muévete"]):
            if ".." in texto_l or "atras" in texto_l or "anterior" in texto_l:
                return "cd .."
            
            # Buscar el nombre de la carpeta
            palabras = texto_l.split()
            # Heurística simple: tomar la última palabra si no es una palabra común
            ignorar = ["la", "carpeta", "a", "el", "directorio", "muevete", "muévete", "entra", "en"]
            posibles_nombres = [p for p in palabras if p not in ignorar]
            
            if posibles_nombres:
                return f"cd {posibles_nombres[-1]}"

        # Listar
        if "que hay" in texto_l or "listar" in texto_l or "muestra" in texto_l:
            return "dir"

        # Historial
        if "historial" in texto_l and ("limpia" in texto_l or "borrar" in texto_l):
            return "clear log"
        if "historial" in texto_l:
            return "log"

        return 'ERROR'
    
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
        comandos_validos = ["cd", "mkdir", "type", "rmdir", "dir", "log", "clear log"]
        if not comando: return "ERROR"
        
        comando_base = comando.split()[0].lower()
        if comando_base in comandos_validos:
            return comando
        return "ERROR"

class GestorRespaldos:
    """
    Maneja los respaldos automaticos del sistema
    
    Implementa la persistencia del estado del sistema.
    Utiliza técnicas de serialización (convertir objetos en memoria a formato JSON) para guardar
    snapshots del sistema, permitiendo la recuperación de datos y auditoría de operaciones.
    """
    
    def __init__(self, sistema, config):
        self.sistema = sistema
        self.config = config
    
    def respaldar_automatico(self) -> str:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            ruta_respaldos = self.config.obtener_ruta_respaldos()
            os.makedirs(ruta_respaldos, exist_ok=True)
            archivo_respaldo = f"{ruta_respaldos}respaldo_{timestamp}.json"
            
            datos_respaldo = {
                "fecha_respaldo": timestamp,
                "ruta_actual": self.sistema.ruta_actual,
                "historial_operaciones": self._serializar_pila(self.sistema.historial_operaciones),
                "errores": self._serializar_pila(self.sistema.errores),
                "sistema_archivos": self._serializar_arbol(self.sistema.raiz)
            }
            
            with open(archivo_respaldo, 'w', encoding='utf-8') as f:
                json.dump(datos_respaldo, f, indent=4, ensure_ascii=False)
            return f"Respaldo automatico realizado en {archivo_respaldo}"
        except Exception as e:
            return f"Error en respaldo automatico: {str(e)}"
    
    def cargar_ultimo_respaldo(self) -> bool:
        """Carga el ultimo respaldo disponible"""
        try:
            ruta_respaldos = self.config.obtener_ruta_respaldos()
            if not os.path.exists(ruta_respaldos):
                return False
            
            archivos = [f for f in os.listdir(ruta_respaldos) if f.startswith("respaldo_") and f.endswith(".json")]
            if not archivos:
                return False
            
            ultimo_respaldo = sorted(archivos)[-1]
            ruta_completa = os.path.join(ruta_respaldos, ultimo_respaldo)
            
            print(f"[Sistema] Cargando ultimo respaldo: {ultimo_respaldo}")
            
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            # Restaurar historial y errores
            self.sistema.historial_operaciones = self._deserializar_pila(datos.get("historial_operaciones", []))
            self.sistema.errores = self._deserializar_pila(datos.get("errores", []))
            
            # Restaurar sistema de archivos
            if "sistema_archivos" in datos:
                self.sistema.raiz = self._deserializar_arbol(datos["sistema_archivos"], None)
                # Restaurar ruta actual (simplificado: volver a raiz si es complejo, o intentar navegar)
                # Por seguridad y simplicidad, al cargar backup volvemos a raiz o intentamos restaurar
                self.sistema.directorio_actual = self.sistema.raiz
                self.sistema.ruta_actual = self.sistema.unidad_raiz
                
                # Intentar restaurar la ruta guardada si existe
                ruta_guardada = datos.get("ruta_actual", self.sistema.unidad_raiz)
                if ruta_guardada != self.sistema.unidad_raiz:
                    # Navegacion basica para restaurar contexto
                    comando_cd = ComandoCD()
                    comando_cd.ejecutar(self.sistema, [ruta_guardada])
            
            return True
        except Exception as e:
            print(f"Error cargando respaldo: {e}")
            return False

    def _serializar_arbol(self, carpeta) -> dict:
        """Convierte recursivamente el arbol de carpetas a diccionario"""
        contenido_serializado = []
        # Iterar sobre la Cola de contenido
        for elemento in carpeta.contenido:
            if elemento.tipo == "carpeta":
                contenido_serializado.append(self._serializar_arbol(elemento))
            else:
                contenido_serializado.append({
                    "tipo": "archivo",
                    "nombre": elemento.nombre,
                    "contenido": elemento.contenido,
                    "fecha_creacion": elemento.fecha_creacion,
                    "fecha_modificacion": elemento.fecha_modificacion
                })
        
        return {
            "tipo": "carpeta",
            "nombre": carpeta.nombre,
            "contenido": contenido_serializado,
            "fecha_creacion": carpeta.fecha_creacion,
            "fecha_modificacion": carpeta.fecha_modificacion
        }

    def _deserializar_arbol(self, datos_nodo: dict, padre) -> object:
        """Reconstruye recursivamente el arbol de objetos"""
        if datos_nodo["tipo"] == "carpeta":
            nueva_carpeta = Carpeta(datos_nodo["nombre"], padre)
            nueva_carpeta.fecha_creacion = datos_nodo.get("fecha_creacion", "")
            nueva_carpeta.fecha_modificacion = datos_nodo.get("fecha_modificacion", "")
            
            for hijo_datos in datos_nodo["contenido"]:
                hijo_obj = self._deserializar_arbol(hijo_datos, nueva_carpeta)
                nueva_carpeta.agregar_elemento(hijo_obj)
            return nueva_carpeta
        else:
            nuevo_archivo = Archivo(datos_nodo["nombre"], datos_nodo.get("contenido", ""))
            nuevo_archivo.fecha_creacion = datos_nodo.get("fecha_creacion", "")
            nuevo_archivo.fecha_modificacion = datos_nodo.get("fecha_modificacion", "")
            return nuevo_archivo

    def _serializar_pila(self, pila) -> list:
        elementos = []
        pila_temp = Pila()
        while not pila.esta_vacia():
            elemento = pila.desapilar()
            elementos.append(elemento)
            pila_temp.apilar(elemento)
        while not pila_temp.esta_vacia():
            pila.apilar(pila_temp.desapilar())
        return elementos # Retorna lista [tope, ..., fondo] o [fondo, ..., tope]? 
        # Al desapilar obtenemos el tope primero. Append lo pone en indice 0.
        # Si queremos guardar orden cronologico inverso (LIFO), esta bien.
    
    def _deserializar_pila(self, lista_elementos: list) -> Pila:
        """Reconstruye una pila desde una lista"""
        pila = Pila()
        # La lista viene de _serializar_pila que extrajo: Tope, Tope-1, ... Fondo
        # Si insertamos en ese orden en una nueva pila:
        # Apilar(Tope) -> Pila: [Tope]
        # Apilar(Tope-1) -> Pila: [Tope-1, Tope] -> EL ORDEN SE INVIERTE
        # Para mantener el orden original, debemos iterar la lista al revés
        for elemento in reversed(lista_elementos):
            pila.apilar(elemento)
        return pila

class SistemaArchivos:
    """
    Clase principal del sistema de archivos
    
    Esta es la clase 'Fachada' (Facade) o Controlador principal.
    Orquesta la interacción entre todos los subsistemas:
    1. Estructura de datos (Árbol de directorios)
    2. Intérprete de comandos (Patrón Command)
    3. Inteligencia Artificial
    4. Sistema de logs y respaldos
    Mantiene el estado global de la aplicación (ruta actual, raíz, historial).
    """
    
    def __init__(self):
        self.config = Configuracion()
        self.unidad_raiz = self.config.datos["unidad_raiz"]
        self.raiz = Carpeta(self.unidad_raiz, padre=None)
        self.directorio_actual = self.raiz
        self.ruta_actual = self.unidad_raiz
        self.historial_operaciones = Pila()
        self.errores = Pila()
        self.chatbot = ChatbotIA(self.config)
        self.gestor_respaldos = GestorRespaldos(self, self.config)
        
        self.comandos = self._cargar_comandos()
        
        # Intentar cargar respaldo, si falla, cargar datos de prueba
        if not self.gestor_respaldos.cargar_ultimo_respaldo():
            print("[Sistema] No se encontraron respaldos previos. Iniciando con datos de prueba.")
            self._inicializar_datos_prueba()
        else:
            print("[Sistema] Sistema restaurado desde el ultimo punto de control.")
    
    def _cargar_comandos(self) -> dict:
        return {
            "cd": ComandoCD(),
            "mkdir": ComandoMKDIR(),
            "type": ComandoTYPE(),
            "rmdir": ComandoRMDIR(),
            "dir": ComandoDIR(),
            "log": ComandoLOG(),
            "clear log": ComandoClearLog()
        }
    
    def _inicializar_datos_prueba(self):
        carpeta_docs = Carpeta("Documentos", padre=self.raiz)
        carpeta_proyectos = Carpeta("Proyectos", padre=carpeta_docs)
        archivo_notas = Archivo("Notas.txt", "Notas importantes del sistema")
        archivo_tareas = Archivo("Tareas.txt", "Lista de tareas pendientes")
        
        carpeta_proyectos.agregar_elemento(archivo_tareas)
        carpeta_docs.agregar_elemento(carpeta_proyectos)
        carpeta_docs.agregar_elemento(archivo_notas)
        self.raiz.agregar_elemento(carpeta_docs)
    
    def registrar_operacion(self, operacion: str):
        if self.config.datos["log_operaciones"]:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            self.historial_operaciones.apilar(f"{timestamp} {operacion}")
    
    def registrar_error(self, error: str):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.errores.apilar(f"{timestamp} {error}")
    
    def respaldar_automatico(self):
        return self.gestor_respaldos.respaldar_automatico()
    
    def limpiar_historial(self):
        while not self.historial_operaciones.esta_vacia():
            self.historial_operaciones.desapilar()
    
    def limpiar_errores(self):
        while not self.errores.esta_vacia():
            self.errores.desapilar()
    
    def ejecutar_comando(self, entrada: str) -> str:
        """
        Ejecuta un comando. 
        Logica:
        1. ¿Empieza con un comando conocido (cd, mkdir, etc)? -> Ejecutar Directo.
        2. ¿No? -> Enviar a Chatbot IA para traducir -> Ejecutar resultado.
        """
        resultado = ""
        entrada_str = entrada.strip()
        if not entrada_str: return ""

        # 1. Verificar si es un comando directo conocido
        comando_detectado = None
        # Ordenamos por longitud para detectar 'clear log' antes que 'log' si fuera necesario
        claves_comandos = sorted(self.comandos.keys(), key=len, reverse=True)
        
        for cmd in claves_comandos:
            # Check simple: empieza por el comando + espacio o es el comando exacto
            if entrada_str.lower() == cmd or entrada_str.lower().startswith(cmd + " "):
                comando_detectado = cmd
                break
        
        # 2. Si no es un comando directo, usar IA
        if comando_detectado is None:
            if self.config.datos["habilitar_chatbot"]:
                # Llamada a la API
                print(f"[Sistema] Analizando entrada con IA...")
                comando_traducido = self.chatbot.interpretar_comando(entrada_str)

                if "ERROR" in comando_traducido:
                    return f"Chatbot IA: No pude entender la solicitud '{entrada_str}'.\nDetalle: {comando_traducido}"
                
                # Éxito en la traducción
                resultado += f"Chatbot IA: Entendido. Ejecutando: {comando_traducido}\n"
                entrada_str = comando_traducido
                
                # Volvemos a extraer el comando base del resultado de la IA
                for cmd in claves_comandos:
                    if entrada_str.lower().startswith(cmd):
                        comando_detectado = cmd
                        break
            else:
                return "Error: Comando no reconocido y Chatbot desactivado."

        # 3. Ejecucion final
        if comando_detectado:
            if self.config.comando_activado(comando_detectado):
                argumentos_str = entrada_str[len(comando_detectado):].strip()
                # Truco para manejar argumentos con comillas correctamente si fuera necesario, 
                # por ahora split() basico sirve para la mayoria excepto type con espacios en contenido
                if 'type' in comando_detectado and '"' in argumentos_str:
                     # Parseo manual rapido para type para respetar comillas
                     parts = argumentos_str.split(' ', 1)
                     argumentos = [parts[0]] + ([parts[1]] if len(parts)>1 else [])
                else:
                    argumentos = argumentos_str.split()
                
                try:
                    resultado += self.comandos[comando_detectado].ejecutar(self, argumentos)
                except Exception as e:
                    self.registrar_error(str(e))
                    resultado += f"Excepción ejecutando comando: {e}"
            else:
                resultado += f"El comando '{comando_detectado}' está desactivado."
        else:
            resultado += "Error fatal: La IA generó un comando que el sistema no reconoce."

        return resultado
    
    def iniciar_consola(self):
        print("=== Sistema de Consola Inteligente con Chatbot de IA ===")
        print(f"Modelo: {self.config.obtener_modelo_ia()}")
        print("Comandos directos: cd, mkdir, type, rmdir, dir, log, clear log")
        print("Puedes escribir en lenguaje natural (ej: 'crea carpeta fotos').")
        print("Escribe 'salir' para terminar.\n")
        
        while True:
            try:
                prompt = f"{self.ruta_actual}> "
                entrada = input(prompt).strip()
                
                if entrada.lower() == 'salir':
                    self.config.guardar_configuracion()
                    break
                
                if entrada:
                    resultado = self.ejecutar_comando(entrada)
                    print(resultado)
                    print()
                    
            except KeyboardInterrupt:
                print("\nSaliendo...")
                self.config.guardar_configuracion()
                break
            except Exception as e:
                print(f"Error inesperado en main loop: {e}")