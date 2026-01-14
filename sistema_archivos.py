"""
Modulo del Sistema de Archivos - Logica central
Resolucion de rutas, chatbot IA, backup JSON, log
Acoplamiento medio - solo con comandos y entidades
"""

from datetime import datetime

from chatbot import ChatbotIA
from comandos import (
    ComandoCD,
    ComandoDIR,
    ComandoLOG,
    ComandoMKDIR,
    ComandoRMDIR,
    ComandoTYPE,
    ComandoClearLog,
    ComandoIndexSearch,
    ComandoRM,
    ComandoRename,
    ComandoBackup,
)
from configuracion import Configuracion
from entidades_fs import Carpeta, Archivo, UnidadAlmacenamiento
from estructuras_datos import Pila
from respaldos import GestorRespaldos
from indice_global import IndiceGlobalArchivos


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
        self.unidades = self._crear_unidades(self.config.datos.get("unidades", ["C:"]))
        self.unidad_actual = self.unidades  # cabeza de la lista enlazada
        self.directorio_actual = self.unidad_actual.raiz
        self.ruta_actual = self.unidad_actual.nombre
        self.historial_operaciones = Pila()
        self.errores = Pila()
        self.chatbot = ChatbotIA(self.config)
        self.indice_global = IndiceGlobalArchivos()
        self.gestor_respaldos = GestorRespaldos(self, self.config)

        self.comandos = self._cargar_comandos()

        if not self.gestor_respaldos.cargar_ultimo_respaldo():
            print("[Sistema] No se encontraron respaldos previos. Iniciando con datos de prueba.")
            self._inicializar_datos_prueba()
        else:
            print("[Sistema] Sistema restaurado desde el ultimo punto de control.")

        # Siempre reconstruir el indice global al iniciar
        self.reconstruir_indice_global()
    
    def _cargar_comandos(self) -> dict:
        return {
            "cd": ComandoCD(),
            "mkdir": ComandoMKDIR(),
            "type": ComandoTYPE(),
            "rmdir": ComandoRMDIR(),
            "rm": ComandoRM(),
            "rename": ComandoRename(),
            "dir": ComandoDIR(),
            "log": ComandoLOG(),
            "clear log": ComandoClearLog(),
            "index": ComandoIndexSearch(),
            "backup": ComandoBackup(),
            "respaldar": ComandoBackup(),
        }

    def _crear_unidades(self, nombres: list) -> UnidadAlmacenamiento:
        cabeza = None
        anterior = None
        for nombre in nombres:
            unidad = UnidadAlmacenamiento(nombre)
            if cabeza is None:
                cabeza = unidad
            if anterior:
                anterior.siguiente = unidad
            anterior = unidad
        return cabeza
    
    def _inicializar_datos_prueba(self):
        carpeta_docs = Carpeta("Documentos", padre=self.unidad_actual.raiz)
        carpeta_proyectos = Carpeta("Proyectos", padre=carpeta_docs)
        archivo_notas = Archivo("Notas.txt", "Notas importantes del sistema")
        archivo_tareas = Archivo("Tareas.txt", "Lista de tareas pendientes")
        
        carpeta_proyectos.agregar_archivo(archivo_tareas)
        carpeta_docs.agregar_carpeta(carpeta_proyectos)
        carpeta_docs.agregar_archivo(archivo_notas)
        self.unidad_actual.raiz.agregar_carpeta(carpeta_docs)
    
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

    def construir_ruta(self, nombre: str) -> str:
        """Construye la ruta completa usando la ruta actual."""
        base = self.ruta_actual.rstrip('/')
        return f"{base}/{nombre}" if base else nombre

    def _obtener_unidad(self, nombre_unidad: str) -> UnidadAlmacenamiento:
        nombre_norm = nombre_unidad.rstrip(":") + ":"
        actual = self.unidades
        while actual:
            if actual.nombre.lower() == nombre_norm.lower():
                return actual
            actual = actual.siguiente
        return None

    def resolver_ruta(self, ruta: str):
        """Resuelve ruta a (unidad, carpeta o None, mensaje_error)."""
        ruta_norm = ruta.replace('\\', '/').strip()
        unidad = self.unidad_actual
        carpeta_actual = self.directorio_actual

        # Detectar unidad explicita
        if len(ruta_norm) >= 2 and ruta_norm[1] == ':':
            unidad_nombre = ruta_norm[:2]
            unidad = self._obtener_unidad(unidad_nombre)
            if unidad is None:
                return None, None, f"Error: La unidad {unidad_nombre} no existe."
            ruta_norm = ruta_norm[2:]
            carpeta_actual = unidad.raiz

        # Ruta absoluta desde raiz
        if ruta_norm.startswith('/'):
            ruta_norm = ruta_norm.lstrip('/')
            carpeta_actual = unidad.raiz

        # Si queda vacio, devolver raiz
        if not ruta_norm:
            return unidad, carpeta_actual, None

        partes = [p for p in ruta_norm.split('/') if p not in ('', '.')]
        actual = carpeta_actual
        for parte in partes:
            if parte == '..':
                if actual.padre:
                    actual = actual.padre
                continue
            siguiente = actual.buscar_carpeta(parte)
            if siguiente is None:
                return None, None, f"Error: El directorio '{parte}' no existe."
            actual = siguiente
        return unidad, actual, None

    def ruta_absoluta(self, carpeta: Carpeta) -> str:
        partes = []
        actual = carpeta
        while actual and actual.padre is not None:
            partes.append(actual.nombre)
            actual = actual.padre
        # actual es raiz de la unidad
        unidad_nombre = actual.nombre if actual else self.unidad_actual.nombre
        return unidad_nombre if not partes else f"{unidad_nombre}/{'/'.join(reversed(partes))}"

    def reconstruir_indice_global(self):
        """Reconstruye el índice global B-Tree desde el árbol de carpetas."""
        # Limpia y repuebla el B-Tree global con todos los archivos de todas las unidades
        self.indice_global.limpiar()

        def recorrer_carpeta(carpeta: Carpeta, base: str):
            for archivo in carpeta.archivos_en_orden("inorden"):
                ruta = f"{base}/{archivo.nombre}" if base else archivo.nombre
                self.indice_global.insertar_archivo(archivo, ruta)
            for sub in carpeta.subcarpetas:
                ruta_sub = f"{base}/{sub.nombre}" if base else sub.nombre
                recorrer_carpeta(sub, ruta_sub)

        unidad = self.unidades
        while unidad:
            recorrer_carpeta(unidad.raiz, unidad.nombre)
            unidad = unidad.siguiente
    
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
            if self.config.datos["habilitar_chatbot"] and self.chatbot:
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
        print("Comandos directos: cd, mkdir, type, rm, rename, rmdir, dir, log, clear log, index, backup")
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