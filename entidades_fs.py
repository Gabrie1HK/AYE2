# entidades_fs.py
"""
Modulo de Entidades del Sistema de Archivos
Estructuras: lista enlazada de unidades, arbol n-ario de carpetas,
arbol binario de archivos por carpeta.
"""

from datetime import datetime
from typing import Callable, List, Optional, Tuple


class ElementoSistemaArchivos:
    """Base para archivos y carpetas."""

    def __init__(self, nombre: str, tipo: str):
        self.nombre = nombre
        self.tipo = tipo
        self.fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.fecha_modificacion = self.fecha_creacion

    def actualizar_modificacion(self):
        self.fecha_modificacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return f"[{self.tipo.upper()}] {self.nombre}"

    def __repr__(self):
        return f"{self.tipo.capitalize()}(nombre='{self.nombre}')"


class Archivo(ElementoSistemaArchivos):
    """Archivo de texto (hoja)."""

    def __init__(self, nombre: str, contenido: str = ""):
        super().__init__(nombre, "archivo")
        self.contenido = contenido
        self.extension = self._obtener_extension(nombre)

    def _obtener_extension(self, nombre: str) -> str:
        return nombre.split(".")[-1] if "." in nombre else ""

    def escribir(self, contenido: str):
        self.contenido = contenido
        self.actualizar_modificacion()

    def leer(self) -> str:
        return self.contenido

    def __str__(self):
        return f"[ARCHIVO] {self.nombre} ({len(self.contenido)} bytes)"


class NodoArchivoBinario:
    """Nodo para arbol binario de archivos (ordenado por nombre)."""

    def __init__(self, archivo: Archivo):
        self.archivo = archivo
        self.izq: Optional["NodoArchivoBinario"] = None
        self.der: Optional["NodoArchivoBinario"] = None


class Carpeta(ElementoSistemaArchivos):
    """Carpeta como nodo de arbol n-ario; contiene subcarpetas y un BST de archivos."""

    def __init__(self, nombre: str, padre=None):
        super().__init__(nombre, "carpeta")
        self.subcarpetas: List["Carpeta"] = []
        self.archivos_raiz: Optional[NodoArchivoBinario] = None
        self.padre = padre

    # --- Carpetas (n-ario) ---
    def agregar_carpeta(self, carpeta: "Carpeta"):
        self.subcarpetas.append(carpeta)
        self.actualizar_modificacion()

    def buscar_carpeta(self, nombre: str) -> Optional["Carpeta"]:
        nombre_lower = nombre.lower()
        for carpeta in self.subcarpetas:
            if carpeta.nombre.lower() == nombre_lower:
                return carpeta
        return None

    def eliminar_carpeta(self, carpeta: "Carpeta") -> bool:
        try:
            self.subcarpetas.remove(carpeta)
            self.actualizar_modificacion()
            return True
        except ValueError:
            return False

    # --- Archivos (BST) ---
    def agregar_archivo(self, archivo: Archivo) -> bool:
        if self.archivos_raiz is None:
            self.archivos_raiz = NodoArchivoBinario(archivo)
            self.actualizar_modificacion()
            return True
        inserted = self._insertar_archivo(self.archivos_raiz, archivo)
        if inserted:
            self.actualizar_modificacion()
        return inserted

    def _insertar_archivo(self, nodo: NodoArchivoBinario, archivo: Archivo) -> bool:
        if archivo.nombre.lower() == nodo.archivo.nombre.lower():
            return False
        if archivo.nombre.lower() < nodo.archivo.nombre.lower():
            if nodo.izq:
                return self._insertar_archivo(nodo.izq, archivo)
            nodo.izq = NodoArchivoBinario(archivo)
            return True
        if nodo.der:
            return self._insertar_archivo(nodo.der, archivo)
        nodo.der = NodoArchivoBinario(archivo)
        return True

    def buscar_archivo(self, nombre: str) -> Optional[Archivo]:
        nodo = self._buscar_nodo_archivo(self.archivos_raiz, nombre.lower())
        return nodo.archivo if nodo else None

    def _buscar_nodo_archivo(self, nodo: Optional[NodoArchivoBinario], nombre_lower: str) -> Optional[NodoArchivoBinario]:
        if nodo is None:
            return None
        if nombre_lower == nodo.archivo.nombre.lower():
            return nodo
        if nombre_lower < nodo.archivo.nombre.lower():
            return self._buscar_nodo_archivo(nodo.izq, nombre_lower)
        return self._buscar_nodo_archivo(nodo.der, nombre_lower)

    def eliminar_archivo(self, nombre: str) -> bool:
        eliminado, nueva_raiz = self._eliminar_archivo(self.archivos_raiz, nombre.lower())
        if eliminado:
            self.archivos_raiz = nueva_raiz
            self.actualizar_modificacion()
        return eliminado

    def _eliminar_archivo(self, nodo: Optional[NodoArchivoBinario], nombre_lower: str) -> Tuple[bool, Optional[NodoArchivoBinario]]:
        if nodo is None:
            return False, None
        if nombre_lower < nodo.archivo.nombre.lower():
            eliminado, nodo.izq = self._eliminar_archivo(nodo.izq, nombre_lower)
            return eliminado, nodo
        if nombre_lower > nodo.archivo.nombre.lower():
            eliminado, nodo.der = self._eliminar_archivo(nodo.der, nombre_lower)
            return eliminado, nodo
        # Encontrado
        if nodo.izq is None:
            return True, nodo.der
        if nodo.der is None:
            return True, nodo.izq
        # Reemplazar por sucesor
        sucesor = self._min_nodo(nodo.der)
        nodo.archivo = sucesor.archivo
        eliminado, nodo.der = self._eliminar_archivo(nodo.der, sucesor.archivo.nombre.lower())
        return True, nodo

    def _min_nodo(self, nodo: NodoArchivoBinario) -> NodoArchivoBinario:
        actual = nodo
        while actual.izq:
            actual = actual.izq
        return actual

    # --- Recorridos de archivos ---
    def _recorrer_archivos(self, nodo: Optional[NodoArchivoBinario], visita: Callable[[Archivo], None], orden: str):
        if nodo is None:
            return
        if orden == "preorden":
            visita(nodo.archivo)
        self._recorrer_archivos(nodo.izq, visita, orden)
        if orden == "inorden":
            visita(nodo.archivo)
        self._recorrer_archivos(nodo.der, visita, orden)
        if orden == "postorden":
            visita(nodo.archivo)

    def archivos_en_orden(self, orden: str = "inorden") -> List[Archivo]:
        salida: List[Archivo] = []
        self._recorrer_archivos(self.archivos_raiz, salida.append, orden)
        return salida

    # --- Utilidades mixtas ---
    def listar_elementos(self) -> List[ElementoSistemaArchivos]:
        elementos: List[ElementoSistemaArchivos] = []
        elementos.extend(sorted(self.subcarpetas, key=lambda c: c.nombre.lower()))
        elementos.extend(sorted(self.archivos_en_orden("inorden"), key=lambda a: a.nombre.lower()))
        return elementos

    def buscar_elemento(self, nombre: str) -> Optional[ElementoSistemaArchivos]:
        carpeta = self.buscar_carpeta(nombre)
        if carpeta:
            return carpeta
        return self.buscar_archivo(nombre)

    def eliminar_elemento(self, elemento) -> bool:
        if getattr(elemento, "tipo", "") == "carpeta":
            return self.eliminar_carpeta(elemento)
        if getattr(elemento, "tipo", "") == "archivo":
            return self.eliminar_archivo(elemento.nombre)
        return False

    def esta_vacia(self):
        return not self.subcarpetas and self.archivos_raiz is None

    def recorrer_subcarpetas_postorden(self) -> List["Carpeta"]:
        resultado: List[Carpeta] = []

        def dfs(carpeta: "Carpeta"):
            for sub in carpeta.subcarpetas:
                dfs(sub)
            resultado.append(carpeta)

        dfs(self)
        return resultado

    def __str__(self):
        return f"[CARPETA] {self.nombre} ({len(self.subcarpetas)} carpetas, {len(self.archivos_en_orden('inorden'))} archivos)"


class UnidadAlmacenamiento:
    """Unidad (C:, D:, etc.) en lista enlazada simple."""

    def __init__(self, nombre: str):
        nombre_norm = nombre.rstrip(":") + ":"
        self.nombre = nombre_norm
        self.raiz = Carpeta(nombre_norm, padre=None)
        self.siguiente: Optional["UnidadAlmacenamiento"] = None

    def __str__(self):
        return f"Unidad {self.nombre}"