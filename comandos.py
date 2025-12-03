# comandos.py
"""
Modulo de Comandos 
Todas las operaciones del sistema como comandos
Bajo acoplamiento - recibe instancia de FileSystem
"""

from abc import ABC, abstractmethod
from typing import List

class Comando(ABC):
    """Interfaz base para todos los comandos"""
    
    @abstractmethod
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        """Ejecuta el comando con los argumentos proporcionados"""
        pass
    
    @abstractmethod
    def obtener_nombre(self) -> str:
        """Retorna el nombre del comando"""
        pass
    
    def obtener_uso(self) -> str:
        """Retorna el uso del comando"""
        return f"Uso: {self.obtener_nombre()} [argumentos]"

class ComandoCD(Comando):
    """
    Comando para cambiar directorio (maneja rutas absolutas y múltiples niveles)
    
    Este comando se aplica para la navegación dentro del árbol de directorios del sistema de archivos.
    Permite al usuario cambiar su ubicación actual (contexto) a otra carpeta, soportando:
    1. Rutas relativas (ej: "cd fotos", "cd ..")
    2. Rutas absolutas (ej: "cd C:/Documentos")
    3. Navegación compleja (ej: "cd ../Proyectos/Python")
    """
    
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if not argumentos:
            return self.obtener_uso()
        
        ruta = argumentos[0]
        sistema.registrar_operacion(f"cd {ruta}")
        
        # Manejar rutas absolutas (que empiezan con C:)
        if ruta.startswith(sistema.unidad_raiz):
            return self._manejar_ruta_absoluta(sistema, ruta)
        # Manejar rutas relativas con múltiples niveles
        elif '/' in ruta or '\\' in ruta:
            return self._manejar_ruta_relativa(sistema, ruta)
        # Manejar casos simples: .. o nombre de carpeta
        else:
            if ruta == "..":
                return self._retroceder_directorio(sistema)
            else:
                return self._cambiar_directorio(sistema, ruta)
    
    def _manejar_ruta_absoluta(self, sistema, ruta: str) -> str:
        """Maneja rutas absolutas (desde la raíz)"""
        # Normalizar la ruta: reemplazar \ por / y eliminar la unidad
        ruta_normalizada = ruta.replace('\\', '/')
        if ruta_normalizada.startswith(sistema.unidad_raiz + '/'):
            ruta_normalizada = ruta_normalizada[len(sistema.unidad_raiz)+1:]
        elif ruta_normalizada == sistema.unidad_raiz:
            ruta_normalizada = ""
        
        # Si la ruta está vacía, ir a la raíz
        if not ruta_normalizada:
            sistema.directorio_actual = sistema.raiz
            sistema.ruta_actual = sistema.unidad_raiz
            return f"Directorio actual: {sistema.ruta_actual}"
        
        # Dividir la ruta en partes
        partes = ruta_normalizada.split('/')
        # Empezar desde la raíz
        directorio_actual = sistema.raiz
        ruta_actual = sistema.unidad_raiz
        
        for parte in partes:
            if not parte or parte == '.':
                continue
            elif parte == '..':
                if directorio_actual.padre:
                    directorio_actual = directorio_actual.padre
                    # Actualizar ruta_actual
                    if directorio_actual == sistema.raiz:
                        ruta_actual = sistema.unidad_raiz
                    else:
                        # Recortar la última parte de la ruta
                        partes_ruta = ruta_actual.split('/')
                        if len(partes_ruta) > 1:
                            ruta_actual = '/'.join(partes_ruta[:-1])
                        else:
                            ruta_actual = sistema.unidad_raiz
            else:
                siguiente = None
                for elemento in directorio_actual.contenido:
                    if (hasattr(elemento, 'nombre') and 
                        elemento.nombre.lower() == parte.lower() and 
                        elemento.tipo == "carpeta"):
                        siguiente = elemento
                        break
                if siguiente is None:
                    return f"Error: No se encuentra el directorio: {parte}"
                directorio_actual = siguiente
                if ruta_actual.endswith('/'):
                    ruta_actual += parte
                else:
                    ruta_actual += '/' + parte
        
        sistema.directorio_actual = directorio_actual
        sistema.ruta_actual = ruta_actual
        return f"Directorio actual: {sistema.ruta_actual}"
    
    def _manejar_ruta_relativa(self, sistema, ruta: str) -> str:
        """Maneja rutas relativas con múltiples niveles"""
        # Normalizar la ruta: reemplazar \ por /
        ruta_normalizada = ruta.replace('\\', '/')
        partes = ruta_normalizada.split('/')
        
        directorio_actual = sistema.directorio_actual
        ruta_actual = sistema.ruta_actual
        
        for parte in partes:
            if not parte or parte == '.':
                continue
            elif parte == '..':
                if directorio_actual.padre:
                    directorio_actual = directorio_actual.padre
                    # Actualizar ruta_actual
                    if directorio_actual == sistema.raiz:
                        ruta_actual = sistema.unidad_raiz
                    else:
                        # Recortar la última parte de la ruta
                        partes_ruta = ruta_actual.split('/')
                        if len(partes_ruta) > 1:
                            ruta_actual = '/'.join(partes_ruta[:-1])
                        else:
                            ruta_actual = sistema.unidad_raiz
            else:
                siguiente = None
                for elemento in directorio_actual.contenido:
                    if (hasattr(elemento, 'nombre') and 
                        elemento.nombre.lower() == parte.lower() and 
                        elemento.tipo == "carpeta"):
                        siguiente = elemento
                        break
                if siguiente is None:
                    return f"Error: No se encuentra el directorio: {parte}"
                directorio_actual = siguiente
                if ruta_actual.endswith('/'):
                    ruta_actual += parte
                else:
                    ruta_actual += '/' + parte
        
        sistema.directorio_actual = directorio_actual
        sistema.ruta_actual = ruta_actual
        return f"Directorio actual: {sistema.ruta_actual}"
    
    def _retroceder_directorio(self, sistema) -> str:
        """Retrocede al directorio padre usando la referencia del objeto"""
        if sistema.directorio_actual.padre is None:
            return "Ya estas en el directorio raiz"
        
        sistema.directorio_actual = sistema.directorio_actual.padre
        
        partes = sistema.ruta_actual.split('/')
        sistema.ruta_actual = '/'.join(partes[:-1]) or sistema.unidad_raiz
        
        return f"Directorio actual: {sistema.ruta_actual}"
    
    def _cambiar_directorio(self, sistema, nombre_carpeta: str) -> str:
        """Cambia a un directorio especifico buscando el objeto"""
        
        carpeta_destino = None
        for elemento in sistema.directorio_actual.contenido:
            if (hasattr(elemento, 'nombre') and 
                elemento.nombre.lower() == nombre_carpeta.lower() and 
                elemento.tipo == "carpeta"):
                carpeta_destino = elemento
                break
        
        if carpeta_destino:
            sistema.directorio_actual = carpeta_destino
            
            if sistema.ruta_actual.endswith(':'): 
                sistema.ruta_actual = f"{sistema.ruta_actual}/{nombre_carpeta}"
            else:
                sistema.ruta_actual = f"{sistema.ruta_actual}/{nombre_carpeta}"
                
            return f"Directorio actual: {sistema.ruta_actual}"
        
        return f"Error: El directorio '{nombre_carpeta}' no existe o no es una carpeta."
    
    def obtener_nombre(self) -> str:
        return "cd"
    
    def obtener_uso(self) -> str:
        return "cd <ruta> (puede ser relativa o absoluta)"

class ComandoMKDIR(Comando):
    """
    Comando para crear directorios (acepta rutas destino)
    
  
    Este comando se utiliza para extender la estructura del sistema de archivos creando nuevas carpetas.
    Se aplica validando previamente que el nombre sea válido y que no exista ya un elemento con el mismo nombre.
    También soporta la creación en rutas remotas sin necesidad de moverse (ej: "mkdir Documentos/Nuevos").
    """
    
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if not argumentos:
            return self.obtener_uso()
        
        ruta_completa = argumentos[0]
        
        # Si la ruta contiene separadores, se trata de una ruta destino
        if '/' in ruta_completa or '\\' in ruta_completa:
            return self._crear_directorio_en_ruta(sistema, ruta_completa)
        else:
            return self._crear_directorio_actual(sistema, ruta_completa)
    
    def _crear_directorio_en_ruta(self, sistema, ruta_completa: str) -> str:
        """Crea un directorio en una ruta específica"""
        # Normalizar la ruta
        ruta_normalizada = ruta_completa.replace('\\', '/')
        # Separar la ruta del nombre del directorio
        if '/' in ruta_normalizada:
            partes = ruta_normalizada.split('/')
            nombre_directorio = partes[-1]
            ruta_destino = '/'.join(partes[:-1])
        else:
            nombre_directorio = ruta_completa
            ruta_destino = ""
        
        # Guardar el estado actual
        directorio_original = sistema.directorio_actual
        ruta_original = sistema.ruta_actual
        
        # Navegar a la ruta destino (usando el comando CD)
        comando_cd = ComandoCD()
        resultado_cd = comando_cd.ejecutar(sistema, [ruta_destino])
        if resultado_cd.startswith("Error"):
            return resultado_cd
        
        # Crear el directorio en el destino
        resultado_creacion = self._crear_directorio_actual(sistema, nombre_directorio)
        
        # Restaurar el directorio original
        sistema.directorio_actual = directorio_original
        sistema.ruta_actual = ruta_original
        
        return resultado_creacion
    
    def _crear_directorio_actual(self, sistema, nombre_carpeta: str) -> str:
        """Crea un directorio en el directorio actual"""
        
        if not self._validar_nombre(nombre_carpeta):
            return f"Nombre de carpeta invalido: {nombre_carpeta}"
        
        nombre_normalizado = nombre_carpeta.lower()
        for elemento in sistema.directorio_actual.contenido:
            if (hasattr(elemento, 'nombre') and 
                elemento.nombre.lower() == nombre_normalizado):
                return f"Error: Ya existe un elemento llamado '{elemento.nombre}' en este directorio."
        
        from entidades_fs import Carpeta
        nueva_carpeta = Carpeta(nombre_carpeta, padre=sistema.directorio_actual)
        sistema.directorio_actual.agregar_elemento(nueva_carpeta)
        
        sistema.registrar_operacion(f"mkdir {nombre_carpeta}")
        sistema.respaldar_automatico()
        
        return f'Carpeta "{nombre_carpeta}" creada exitosamente en {sistema.ruta_actual}'
    
    def _validar_nombre(self, nombre: str) -> bool:
        """Valida que el nombre sea adecuado"""
        caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return all(caracter not in nombre for caracter in caracteres_invalidos) and nombre.strip()
    
    def obtener_nombre(self) -> str:
        return "mkdir"
    
    def obtener_uso(self) -> str:
        return "mkdir <ruta> (puede incluir una ruta destino)"

class ComandoTYPE(Comando):
    """
    Comando para crear archivos con contenido ( acepta rutas destino)
    
    Este comando permite la creación de archivos de texto simulados con contenido.
    Se aplica para demostrar la capacidad del sistema de manejar diferentes tipos de entidades (Archivos vs Carpetas).
    Al igual que mkdir, soporta la creación en rutas específicas.
    """
    
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if len(argumentos) < 2:
            return self.obtener_uso()
        
        ruta_completa = argumentos[0]
        contenido = ' '.join(argumentos[1:]).strip('"')
        
        # Si la ruta contiene separadores, se trata de una ruta destino
        if '/' in ruta_completa or '\\' in ruta_completa:
            return self._crear_archivo_en_ruta(sistema, ruta_completa, contenido)
        else:
            return self._crear_archivo_actual(sistema, ruta_completa, contenido)
    
    def _crear_archivo_en_ruta(self, sistema, ruta_completa: str, contenido: str) -> str:
        """Crea un archivo en una ruta específica"""
        # Normalizar la ruta
        ruta_normalizada = ruta_completa.replace('\\', '/')
        # Separar la ruta del nombre del archivo
        if '/' in ruta_normalizada:
            partes = ruta_normalizada.split('/')
            nombre_archivo = partes[-1]
            ruta_destino = '/'.join(partes[:-1])
        else:
            nombre_archivo = ruta_completa
            ruta_destino = ""
        
        # Guardar el estado actual
        directorio_original = sistema.directorio_actual
        ruta_original = sistema.ruta_actual
        
        # Navegar a la ruta destino (usando el comando CD)
        comando_cd = ComandoCD()
        resultado_cd = comando_cd.ejecutar(sistema, [ruta_destino])
        if resultado_cd.startswith("Error"):
            return resultado_cd
        
        # Crear el archivo en el destino
        resultado_creacion = self._crear_archivo_actual(sistema, nombre_archivo, contenido)
        
        # Restaurar el directorio original
        sistema.directorio_actual = directorio_original
        sistema.ruta_actual = ruta_original
        
        return resultado_creacion
    
    def _crear_archivo_actual(self, sistema, nombre_archivo: str, contenido: str) -> str:
        """Crea un archivo en el directorio actual"""
        
        if not self._validar_nombre_archivo(nombre_archivo):
            return f"Nombre de archivo invalido: {nombre_archivo}"
        
        nombre_normalizado = nombre_archivo.lower()
        for elemento in sistema.directorio_actual.contenido:
            if (hasattr(elemento, 'nombre') and 
                elemento.nombre.lower() == nombre_normalizado):
                return f"Error: Ya existe un elemento llamado '{elemento.nombre}' en este directorio."
        
        from entidades_fs import Archivo
        nuevo_archivo = Archivo(nombre_archivo, contenido)
        sistema.directorio_actual.agregar_elemento(nuevo_archivo)
        
        sistema.registrar_operacion(f'type {nombre_archivo} "{contenido}"')
        sistema.respaldar_automatico()
        
        return (f'Archivo "{nombre_archivo}" creado correctamente en {sistema.ruta_actual}\n'
                f'Contenido guardado: "{contenido}"')
    
    def _validar_nombre_archivo(self, nombre: str) -> bool:
        """Valida que el nombre de archivo sea adecuado"""
        caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return (all(caracter not in nombre for caracter in caracteres_invalidos) 
                and nombre.strip() and '.' in nombre)
    
    def obtener_nombre(self) -> str:
        return "type"
    
    def obtener_uso(self) -> str:
        return 'type <ruta_archivo> "<contenido>" (puede incluir una ruta destino)'

class ComandoRMDIR(Comando):
    """
    Comando para eliminar directorios ( soporta /s y /q)
    
    Este comando gestiona la eliminación de carpetas del sistema.
    Se aplica con lógica de seguridad: por defecto no permite borrar carpetas que contengan archivos.
    Implementa el flag '/s' para permitir el borrado recursivo.
    """
    
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if not argumentos:
            return self.obtener_uso()
        
        # Parsear flags y nombre de carpeta
        flags = []
        nombre_carpeta = ""
        for arg in argumentos:
            if arg.startswith('/'):
                flags.append(arg.upper())
            else:
                nombre_carpeta = arg
        
        if not nombre_carpeta:
            return "Error: Se requiere especificar un directorio"
        
        # Buscar carpeta case-insensitive
        carpeta_a_eliminar = None
        for elemento in sistema.directorio_actual.contenido:
            if (hasattr(elemento, 'nombre') and 
                elemento.nombre.lower() == nombre_carpeta.lower() and 
                elemento.tipo == "carpeta"):
                carpeta_a_eliminar = elemento
                break
        
        if carpeta_a_eliminar is None:
            return f"Error: La carpeta '{nombre_carpeta}' no existe en este directorio."
        
        # Verificar si la carpeta está vacía, a menos que se use /s
        if not carpeta_a_eliminar.contenido.esta_vacia() and '/S' not in flags:
            return f"Error: La carpeta '{carpeta_a_eliminar.nombre}' no está vacía. Use /s para eliminar recursivamente."
        
        # Si se usa /s, eliminar recursivamente
        if '/S' in flags:
            self._eliminar_recursivamente(sistema, carpeta_a_eliminar)
        else:
            # Eliminación normal (solo si está vacía)
            eliminado = sistema.directorio_actual.eliminar_elemento(carpeta_a_eliminar)
            if not eliminado:
                return f"Error interno al intentar eliminar la carpeta '{nombre_carpeta}'."
        
        sistema.registrar_operacion(f"rmdir {carpeta_a_eliminar.nombre}")
        sistema.respaldar_automatico()
        return f'Carpeta "{carpeta_a_eliminar.nombre}" eliminada exitosamente de {sistema.ruta_actual}'
    
    def _eliminar_recursivamente(self, sistema, carpeta):
        """Elimina recursivamente una carpeta y todo su contenido"""
        # Primero eliminar todo el contenido de la carpeta
        while not carpeta.contenido.esta_vacia():
            elemento = carpeta.contenido.desencolar()
            if elemento.tipo == "carpeta":
                self._eliminar_recursivamente(sistema, elemento)
            else:
                # Es un archivo, se elimina directamente
                pass  # Al desencolar, ya se elimina de la cola
        # Luego eliminar la carpeta misma del directorio padre
        sistema.directorio_actual.eliminar_elemento(carpeta)
    
    def obtener_nombre(self) -> str:
        return "rmdir"
    
    def obtener_uso(self) -> str:
        return "rmdir <nombre_carpeta> [/s] [/q]"

class ComandoDIR(Comando):
    """
    Comando para listar contenido de directorios ( acepta rutas destino)
    
    Este comando se usa para visualizar el estado actual del sistema de archivos.
    Se aplica recorriendo la lista de hijos del nodo (carpeta) actual o del nodo especificado en la ruta.
    Es fundamental para que el usuario verifique el resultado de sus operaciones anteriores.
    """
    
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        ruta = argumentos[0] if argumentos else ""
        
        if ruta:
            # Si se proporciona una ruta, listar ese directorio
            return self._listar_ruta(sistema, ruta)
        else:
            # Listar el directorio actual
            return self._listar_actual(sistema)
    
    def _listar_ruta(self, sistema, ruta: str) -> str:
        """Lista el contenido de una ruta específica"""
        # Guardar el estado actual
        directorio_original = sistema.directorio_actual
        ruta_original = sistema.ruta_actual
        
        # Navegar a la ruta destino (usando el comando CD)
        comando_cd = ComandoCD()
        resultado_cd = comando_cd.ejecutar(sistema, [ruta])
        if resultado_cd.startswith("Error"):
            return resultado_cd
        
        # Listar el directorio destino
        resultado_listado = self._listar_actual(sistema)
        
        # Restaurar el directorio original
        sistema.directorio_actual = directorio_original
        sistema.ruta_actual = ruta_original
        
        return resultado_listado
    
    def _listar_actual(self, sistema) -> str:
        """Lista el contenido del directorio actual"""
        sistema.registrar_operacion("dir")
        
        resultado = f"Directorio de {sistema.ruta_actual}\n"
        resultado += "-" * 40 + "\n"
        
        elementos = sistema.directorio_actual.listar_elementos()
        
        if not elementos:
            resultado += "El directorio esta vacio\n"
        else:
            for elemento in elementos:
                resultado += f"{elemento}\n"
        
        resultado += f"\nTotal: {len(elementos)} elemento(s)"
        return resultado
    
    def obtener_nombre(self) -> str:
        return "dir"
    
    def obtener_uso(self) -> str:
        return "dir [ruta] (lista el contenido del directorio actual o de la ruta especificada)"

class ComandoLOG(Comando):
    """Comando para mostrar historial de operaciones"""
    
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        sistema.registrar_operacion("log")
        
        resultado = "--- Historial de Operaciones (LIFO) ---\n"
        
        from estructuras_datos import Pila
        pila_temp = Pila()
        historial = []
        
        while not sistema.historial_operaciones.esta_vacia():
            operacion = sistema.historial_operaciones.desapilar()
            historial.append(operacion)
            pila_temp.apilar(operacion)
        
        while not pila_temp.esta_vacia():
            sistema.historial_operaciones.apilar(pila_temp.desapilar())
        
        for operacion in reversed(historial):
            resultado += operacion + "\n"
        
        return resultado
    
    def obtener_nombre(self) -> str:
        return "log"
    
    def obtener_uso(self) -> str:
        return "log (muestra el historial de operaciones)"

class ComandoClearLog(Comando):
    """Comando para limpiar historial"""
    
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        sistema.limpiar_historial()
        sistema.limpiar_errores()
        sistema.registrar_operacion("clear log")
        return "El historial de errores y operaciones ha sido limpiado."
    
    def obtener_nombre(self) -> str:
        return "clear log"
    
    def obtener_uso(self) -> str:
        return "clear log (limpia el historial de operaciones y errores)"