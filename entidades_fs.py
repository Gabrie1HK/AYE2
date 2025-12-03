# entidades_fs.py
"""
Modulo de Entidades del Sistema de Archivos
Clases Archivo, Carpeta y ElementoSistemaArchivos
Bajo acoplamiento - usa estructuras_datos.Cola
"""

from datetime import datetime
from estructuras_datos import Cola

class ElementoSistemaArchivos:
    """
    Clase base para elementos del sistema de archivos
    
    Clase padre que implementa la Herencia.
    Define los atributos y comportamientos comunes (nombre, fechas) que compartirán
    tanto Archivos como Carpetas, promoviendo la reutilización de código y el Polimorfismo.
    """
    
    def __init__(self, nombre: str, tipo: str):
        self.nombre = nombre
        self.tipo = tipo
        self.fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.fecha_modificacion = self.fecha_creacion
    
    def actualizar_modificacion(self):
        """Actualiza la fecha de modificacion"""
        self.fecha_modificacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def __str__(self):
        return f"[{self.tipo.upper()}] {self.nombre}"
    
    def __repr__(self):
        return f"{self.tipo.capitalize()}(nombre='{self.nombre}')"

class Archivo(ElementoSistemaArchivos):
    """
    Representa un archivo en el sistema
    
    Especialización de un elemento que contiene datos (contenido).
    Representa las hojas del árbol del sistema de archivos (nodos sin hijos).
    """
    
    def __init__(self, nombre: str, contenido: str = ""):
        super().__init__(nombre, "archivo")
        self.contenido = contenido
        self.extension = self._obtener_extension(nombre)
    
    def _obtener_extension(self, nombre: str) -> str:
        """Obtiene la extension del archivo"""
        return nombre.split('.')[-1] if '.' in nombre else ""
    
    def escribir(self, contenido: str):
        """Escribe contenido en el archivo"""
        self.contenido = contenido
        self.actualizar_modificacion()
    
    def leer(self) -> str:
        """Lee el contenido del archivo"""
        return self.contenido
    
    def __str__(self):
        return f"[ARCHIVO] {self.nombre} ({len(self.contenido)} bytes)"

class Carpeta(ElementoSistemaArchivos):
    """
    Representa una carpeta en el sistema
    
    Especialización de un elemento que contiene otros elementos.
    Implementa el patrón Composite (una carpeta puede contener archivos u otras carpetas).
    Utiliza una estructura de datos lineal (Cola) para gestionar sus hijos, permitiendo
    operaciones de inserción y recorrido.
    """
    
    def __init__(self, nombre: str, padre=None):
        super().__init__(nombre, "carpeta")
        self.contenido = Cola()
        self.padre = padre
    
    def agregar_elemento(self, elemento):
        """Agrega un elemento a la carpeta"""
        self.contenido.encolar(elemento)
        self.actualizar_modificacion()
    
    def listar_elementos(self) -> list:
        """Lista todos los elementos de la carpeta"""
        return list(self.contenido)
    
    def buscar_elemento(self, nombre: str):
        """Busca un elemento por nombre"""
        for elemento in self.contenido:
            if elemento.nombre == nombre:
                return elemento
        return None
    
    def eliminar_elemento(self, elemento_a_eliminar):
        """Elimina un elemento especifico de la Cola de contenido"""
        if self.contenido.esta_vacia():
            return False
        
        nueva_cola = Cola()
        encontrado = False
        
        while not self.contenido.esta_vacia():
            elemento = self.contenido.desencolar()
            if elemento is elemento_a_eliminar:
                encontrado = True
            else:
                nueva_cola.encolar(elemento)
                
        self.contenido = nueva_cola
        self.actualizar_modificacion()
        return encontrado
    
    def esta_vacia(self):
        """Verifica si la carpeta esta vacía"""
        return self.contenido.esta_vacia()
    
    def __str__(self):
        return f"[CARPETA] {self.nombre} ({len(self.contenido)} elementos)"