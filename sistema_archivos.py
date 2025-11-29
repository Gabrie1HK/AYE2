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

from estructuras_datos import Pila
from entidades_fs import Carpeta, Archivo
from comandos import (ComandoCD, ComandoMKDIR, ComandoTYPE, 
                     ComandoRMDIR, ComandoDIR, ComandoLOG, ComandoClearLog)

class Configuracion:
    """Maneja la configuracion del sistema"""
    
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
    """Chatbot que usa la API de Gemini para interpretar lenguaje natural"""
    
    def __init__(self, config: Configuracion):
        self.config = config
        self.modelo = self._inicializar_modelo()
    
    def _inicializar_modelo(self):
        """Inicializa el modelo de Gemini con gemini-2.5-flash"""
        try:
            genai.configure(api_key="AIzaSyBhzixVZkatrkrPrF9I8xL9zgeuYhBq2Uc")
            modelo_configurado = self.config.obtener_modelo_ia()
            return genai.GenerativeModel(modelo_configurado)
        except Exception as e:
            print(f"Error inicializando modelo IA {self.config.obtener_modelo_ia()}: {e}")
            try:
                print("Intentando con gemini-pro como fallback...")
                return genai.GenerativeModel('gemini-pro')
            except Exception as fallback_error:
                print(f"Error con fallback tambien: {fallback_error}")
                return None
    
    def interpretar_comando(self, texto_usuario: str) -> str:
        """Interpreta lenguaje natural y devuelve comando"""
        if not self.config.datos["habilitar_chatbot"]:
            return "ERROR: Chatbot desactivado"
        
        # Intentar usar el modelo remoto si está inicializado; si falla, usar parser local
        try:
            if self.modelo:
                prompt = self._crear_prompt_interpretacion(texto_usuario)
                respuesta = self.modelo.generate_content(prompt)
                comando = respuesta.text.strip()
                comando_validado = self._validar_comando(comando)
                if comando_validado != "ERROR":
                    return comando_validado
                # si el modelo devolvió ERROR o un comando inválido, probar fallback local
        except Exception:
            # ignorar y usar fallback local
            pass

        # Fallback local: interpretar mediante reglas simples (sin dependencia externa)
        return self._fallback_interpretar(texto_usuario)

    def _fallback_interpretar(self, texto: str) -> str:
        """Interprete simple de lenguaje natural a comandos.

        Esta función usa patrones y heurísticas sencillas para cubrir casos comunes
        cuando el modelo de IA no está disponible o no puede interpretar el texto.
        """
        texto_l = texto.lower()

        # Crear carpeta
        patrones_mkdir = [
            r"crear una carpeta llamada\s+[\"']?(?P<name>[\w\s\-_.]+)[\"']?",
            r"crear carpeta llamada\s+[\"']?(?P<name>[\w\s\-_.]+)[\"']?",
            r"quiero crear una carpeta(?: llamada)?\s+[\"']?(?P<name>[\w\s\-_.]+)[\"']?",
            r"crea una carpeta(?: llamada)?\s+[\"']?(?P<name>[\w\s\-_.]+)[\"']?",
            r"crear carpeta\s+[\"']?(?P<name>[\w\s\-_.]+)[\"']?",
        ]
        for pat in patrones_mkdir:
            m = re.search(pat, texto_l)
            if m:
                nombre = m.group('name').strip()
                return f"mkdir {nombre}"

        # Cambiar directorio / abrir carpeta
        patrones_cd = [
            r"abre la carpeta\s+[\"']?(?P<name>[\w\s\-_./\\:]+)[\"']?",
            r"ir a la carpeta\s+[\"']?(?P<name>[\w\s\-_./\\:]+)[\"']?",
            r"cambia a la carpeta\s+[\"']?(?P<name>[\w\s\-_./\\:]+)[\"']?",
            r"regresa a la carpeta anterior",
            r"volver al directorio padre",
        ]
        for pat in patrones_cd:
            m = re.search(pat, texto_l)
            if m:
                if 'regresa' in pat or 'volver' in pat:
                    return "cd .."
                nombre = m.group('name').strip()
                # Normalizar barra inicial a unidad
                if nombre.startswith('/'):
                    nombre = self.config.datos.get('unidad_raiz', 'C:') + nombre
                return f"cd {nombre}"

        # Crear archivo con contenido
        m = re.search(r"crear un archivo llamado\s+[\"']?(?P<file>[\w\s\-_.]+\.[a-z0-9]+)[\"']?\s+con el texto\s+[\"'](?P<text>.+)[\"']", texto_l)
        if m:
            archivo = m.group('file').strip()
            contenido = m.group('text').strip()
            return f'type {archivo} "{contenido}"'

        # Borrar carpeta
        patrones_rmdir = [
            r"elimina la carpeta\s+[\"']?(?P<name>[\w\s\-_./\\:]+)[\"']?",
            r"borra la carpeta\s+[\"']?(?P<name>[\w\s\-_./\\:]+)[\"']?",
            r"borra la carpeta temporal",
        ]
        for pat in patrones_rmdir:
            m = re.search(pat, texto_l)
            if m:
                if m.groupdict().get('name'):
                    nombre = m.group('name').strip()
                    # Si es ruta absoluta que empieza con '/', anteponer unidad
                    if nombre.startswith('/'):
                        nombre = self.config.datos.get('unidad_raiz', 'C:') + nombre
                    return f"rmdir /s {nombre}"
                else:
                    # caso general: borrar carpeta genérica
                    return "rmdir /s "

        # Listar directorio
        m = re.search(r"que hay en la carpeta\s+[\"']?(?P<name>[\w\s\-_./\\:]+)[\"']?", texto_l)
        if m:
            nombre = m.group('name').strip()
            if nombre.startswith('/'):
                nombre = self.config.datos.get('unidad_raiz', 'C:') + nombre
            return f"dir {nombre}"

        # Historial / limpiar historial
        if 'historial' in texto_l or 'registro' in texto_l or 'operaciones' in texto_l:
            if 'limpia' in texto_l or 'borra' in texto_l or 'elimina' in texto_l:
                return 'clear log'
            return 'log'

        return 'ERROR'
    
    def _crear_prompt_interpretacion(self, texto: str) -> str:
        """Crea el prompt para la interpretacion optimizado para gemini-2.5-flash"""
        return f"""
        Eres un asistente que traduce lenguaje natural a comandos de sistema de archivos.
        Comandos disponibles: cd, mkdir, type, rmdir, dir, log, clear log.
        
        TEXTO DEL USUARIO: "{texto}"
        
        INSTRUCCIONES:
        1. Analiza la intencion del usuario
        2. Selecciona el comando mas apropiado
        3. Devuelve SOLO el comando en formato exacto
        4. Si no es claro, devuelve "ERROR"
        
        EJEMPLOS:
        "Abre la carpeta Documentos" -> "cd Documentos"
        "Crea una carpeta llamada Fotos" -> "mkdir Fotos"
        "Muestrame lo que hay en esta carpeta" -> "dir"
        "Elimina la carpeta Temporal" -> "rmdir Temporal"
        "Limpia el historial" -> "clear log"
        "Crea un archivo notas.txt con hola mundo" -> 'type notas.txt "hola mundo"'
        
        RESPUESTA (solo el comando):
        """
    
    def _validar_comando(self, comando: str) -> str:
        """Valida que el comando generado sea valido"""
        comandos_validos = ["cd", "mkdir", "type", "rmdir", "dir", "log", "clear log"]
        
        if comando == "ERROR":
            return comando
        
        comando_base = comando.split()[0] if comando else ""
        
        if comando_base in comandos_validos:
            return comando
        else:
            return "ERROR"

class GestorRespaldos:
    """Maneja los respaldos automaticos del sistema"""
    
    def __init__(self, sistema, config):
        self.sistema = sistema
        self.config = config
    
    def respaldar_automatico(self) -> str:
        """Realiza respaldo automatico en formato JSON"""
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
                "modelo_ia_utilizado": self.config.obtener_modelo_ia()
            }
            
            with open(archivo_respaldo, 'w', encoding='utf-8') as f:
                json.dump(datos_respaldo, f, indent=4, ensure_ascii=False)
            
            return f"Respaldo automatico realizado en {archivo_respaldo}"
            
        except Exception as e:
            self.sistema.registrar_error(f"Error en respaldo: {str(e)}")
            return f"Error en respaldo automatico: {str(e)}"
    
    def _serializar_pila(self, pila) -> list:
        """Convierte una pila en lista para serializacion"""
        elementos = []
        pila_temp = Pila()
        
        while not pila.esta_vacia():
            elemento = pila.desapilar()
            elementos.append(elemento)
            pila_temp.apilar(elemento)
        
        while not pila_temp.esta_vacia():
            pila.apilar(pila_temp.desapilar())
        
        return elementos

class SistemaArchivos:
    """Clase principal del sistema de archivos"""
    
    def __init__(self):
        self.config = Configuracion()
        self.unidad_raiz = self.config.datos["unidad_raiz"]
        # CORRECCIÓN CRÍTICA: La raiz se crea con padre=None y se guarda como atributo
        self.raiz = Carpeta(self.unidad_raiz, padre=None)
        self.directorio_actual = self.raiz
        self.ruta_actual = self.unidad_raiz
        self.historial_operaciones = Pila()
        self.errores = Pila()
        self.chatbot = ChatbotIA(self.config)
        self.gestor_respaldos = GestorRespaldos(self, self.config)
        
        self.comandos = self._cargar_comandos()
        self._inicializar_datos_prueba()
        
        print(f"Modelo de IA configurado: {self.config.obtener_modelo_ia()}")
    
    def _cargar_comandos(self) -> dict:
        """Carga todos los comandos disponibles"""
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
        """Inicializa datos de prueba por defecto"""
        # CORRECCIÓN: Las carpetas de prueba se crean con referencias de padre correctas
        # y se agregan a la raíz, no al directorio actual
        carpeta_docs = Carpeta("Documentos", padre=self.raiz)
        carpeta_proyectos = Carpeta("Proyectos", padre=carpeta_docs)
        archivo_notas = Archivo("Notas.txt", "Notas importantes del sistema")
        archivo_tareas = Archivo("Tareas.txt", "Lista de tareas pendientes")
        
        carpeta_proyectos.agregar_elemento(archivo_tareas)
        carpeta_docs.agregar_elemento(carpeta_proyectos)
        carpeta_docs.agregar_elemento(archivo_notas)
        self.raiz.agregar_elemento(carpeta_docs)
        
        self.registrar_operacion("Sistema inicializado con datos de prueba")
    
    def registrar_operacion(self, operacion: str):
        """Registra una operacion en el historial"""
        if self.config.datos["log_operaciones"]:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            self.historial_operaciones.apilar(f"{timestamp} {operacion}")
    
    def registrar_error(self, error: str):
        """Registra un error en el sistema"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.errores.apilar(f"{timestamp} {error}")
    
    def respaldar_automatico(self):
        """Realiza respaldo automatico"""
        return self.gestor_respaldos.respaldar_automatico()
    
    def obtener_historial(self) -> list:
        """Obtiene el historial de operaciones"""
        return list(self.historial_operaciones)
    
    def limpiar_historial(self):
        """Limpia el historial de operaciones"""
        while not self.historial_operaciones.esta_vacia():
            self.historial_operaciones.desapilar()
    
    def limpiar_errores(self):
        """Limpia la pila de errores"""
        while not self.errores.esta_vacia():
            self.errores.desapilar()
    
    def ejecutar_comando(self, entrada: str) -> str:
        """Ejecuta un comando directo o interpretado por IA"""
        resultado = ""
        entrada_str = entrada.strip()

        # Intentar detectar un comando habilitado (soporta comandos de varias palabras como 'clear log')
        comando_encontrado = None
        for cmd in sorted(self.comandos.keys(), key=lambda x: -len(x)):
            if entrada_str.lower().startswith(cmd.lower()):
                comando_encontrado = cmd
                break

        if comando_encontrado is None:
            # No es un comando directo: intentar interpretar con chatbot si esta habilitado
            if self.config.datos["habilitar_chatbot"]:
                comando_traducido = self.chatbot.interpretar_comando(entrada_str)

                if comando_traducido.startswith("ERROR"):
                    return f"Chatbot IA: No pude entender el comando. Error: {comando_traducido}"
                else:
                    resultado += f"Chatbot IA: Comando interpretado correctamente.\n"
                    resultado += f"Comando generado: {comando_traducido}\n\n"
                    entrada_str = comando_traducido
                    # volver a buscar comando encontrado
                    for cmd in sorted(self.comandos.keys(), key=lambda x: -len(x)):
                        if entrada_str.lower().startswith(cmd.lower()):
                            comando_encontrado = cmd
                            break
            else:
                return "Chatbot desactivado. Usa comandos directos."

        if comando_encontrado is None:
            return f"Comando no reconocido: '{entrada_str}'. Usa 'help' para ver comandos disponibles."

        # Extraer argumentos (lo que sigue al comando encontrado)
        resto = entrada_str[len(comando_encontrado):].strip()
        argumentos = resto.split() if resto else []

        # Ejecutar si el comando esta activado en configuracion
        if self.config.comando_activado(comando_encontrado):
            try:
                resultado += self.comandos[comando_encontrado].ejecutar(self, argumentos)
            except Exception as e:
                error_msg = f"Error ejecutando comando: {str(e)}"
                self.registrar_error(error_msg)
                resultado += error_msg
        else:
            resultado += f"Comando '{comando_encontrado}' desactivado en configuracion."

        return resultado
    
    def iniciar_consola(self):
        """Bucle principal de la consola"""
        print("=== Sistema de Consola Inteligente con Chatbot de IA ===")
        print(f"Modelo: {self.config.obtener_modelo_ia()}")
        print("Comandos disponibles: cd, mkdir, type, rmdir, dir, log, clear log")
        print("Tambien puedes usar lenguaje natural. Escribe 'salir' para terminar.\n")
        
        while True:
            try:
                prompt = f"{self.ruta_actual}> "
                entrada = input(prompt).strip()
                
                if entrada.lower() == 'salir':
                    print("Saliendo del sistema...")
                    self.config.guardar_configuracion()
                    break
                
                if entrada.lower() == 'help':
                    self._mostrar_ayuda()
                    continue
                
                if entrada.lower() == 'modelo':
                    print(f"Modelo de IA actual: {self.config.obtener_modelo_ia()}")
                    continue
                
                if entrada:
                    resultado = self.ejecutar_comando(entrada)
                    print(resultado)
                    print()
                    
            except KeyboardInterrupt:
                print("\nSaliendo del sistema...")
                self.config.guardar_configuracion()
                break
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                print(error_msg)
                self.registrar_error(error_msg)
    
    def _mostrar_ayuda(self):
        """Muestra ayuda de comandos"""
        print("\n=== Ayuda del Sistema ===")
        print(f"Modelo de IA: {self.config.obtener_modelo_ia()}")
        for nombre, comando in self.comandos.items():
            if self.config.comando_activado(nombre):
                print(f"{nombre}: {comando.obtener_uso()}")
        print("\nComandos especiales:")
        print("help - Muestra esta ayuda")
        print("modelo - Muestra el modelo de IA en uso")
        print("salir - Termina el programa")
        print("\nTambien puedes usar lenguaje natural para los comandos.")
        print()