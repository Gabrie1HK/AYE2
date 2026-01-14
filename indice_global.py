"""
Indice Global de Archivos usando Arbol B.
Almacena referencias a todos los archivos del sistema y permite busquedas
por nombre (exacto o parcial) y por rangos de tamaño.
"""

import math
from typing import List, Optional


class ArchivoIndexEntry:
    """Entrada de indice para un archivo."""

    def __init__(
        self,
        nombre: str,
        ruta_completa: str,
        tamano_kb: int,
        fecha_creacion: str = "",
        fecha_modificacion: str = "",
        extension: str = "",
    ):
        self.nombre = nombre
        self.ruta_completa = ruta_completa
        self.tamano_kb = tamano_kb
        self.fecha_creacion = fecha_creacion
        self.fecha_modificacion = fecha_modificacion
        self.extension = extension

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "ruta_completa": self.ruta_completa,
            "tamano_kb": self.tamano_kb,
            "fecha_creacion": self.fecha_creacion,
            "fecha_modificacion": self.fecha_modificacion,
            "extension": self.extension,
        }

    @staticmethod
    def from_dict(data: dict) -> "ArchivoIndexEntry":
        return ArchivoIndexEntry(
            data.get("nombre", ""),
            data.get("ruta_completa", ""),
            int(data.get("tamano_kb", 0)),
            data.get("fecha_creacion", ""),
            data.get("fecha_modificacion", ""),
            data.get("extension", ""),
        )


class BTreeNode:
    """Nodo de un Arbol B."""

    def __init__(self, grado_minimo: int, es_hoja: bool = True):
        self.grado = grado_minimo
        self.es_hoja = es_hoja
        self.claves: List[str] = []
        self.valores: List[List[ArchivoIndexEntry]] = []
        self.hijos: List["BTreeNode"] = []


class BTree:
    """Implementacion basica de Arbol B para cadenas."""

    def __init__(self, grado_minimo: int = 2):
        if grado_minimo < 2:
            raise ValueError("El grado minimo del Arbol B debe ser al menos 2")
        self.grado = grado_minimo
        self.raiz = BTreeNode(grado_minimo)

    def buscar_exacta(self, clave: str) -> List[ArchivoIndexEntry]:
        return self._buscar(self.raiz, clave.lower())

    def _buscar(self, nodo: BTreeNode, clave: str) -> List[ArchivoIndexEntry]:
        i = 0
        while i < len(nodo.claves) and clave > nodo.claves[i]:
            i += 1
        if i < len(nodo.claves) and clave == nodo.claves[i]:
            return nodo.valores[i]
        if nodo.es_hoja:
            return []
        return self._buscar(nodo.hijos[i], clave)

    def insertar(self, clave: str, entrada: ArchivoIndexEntry):
        clave = clave.lower()
        raiz = self.raiz
        if len(raiz.claves) == (2 * self.grado) - 1:
            nueva_raiz = BTreeNode(self.grado, es_hoja=False)
            nueva_raiz.hijos.append(raiz)
            self._dividir_hijo(nueva_raiz, 0, raiz)
            self.raiz = nueva_raiz
            self._insertar_no_lleno(nueva_raiz, clave, entrada)
        else:
            self._insertar_no_lleno(raiz, clave, entrada)

    def _insertar_no_lleno(self, nodo: BTreeNode, clave: str, entrada: ArchivoIndexEntry):
        i = len(nodo.claves) - 1
        if nodo.es_hoja:
            while i >= 0 and clave < nodo.claves[i]:
                i -= 1
            if i >= 0 and nodo.claves[i] == clave:
                nodo.valores[i].append(entrada)
                return
            nodo.claves.insert(i + 1, clave)
            nodo.valores.insert(i + 1, [entrada])
        else:
            while i >= 0 and clave < nodo.claves[i]:
                i -= 1
            i += 1
            hijo = nodo.hijos[i]
            if len(hijo.claves) == (2 * self.grado) - 1:
                self._dividir_hijo(nodo, i, hijo)
                if clave > nodo.claves[i]:
                    i += 1
            self._insertar_no_lleno(nodo.hijos[i], clave, entrada)

    def _dividir_hijo(self, padre: BTreeNode, indice: int, hijo: BTreeNode):
        t = self.grado
        nuevo = BTreeNode(t, hijo.es_hoja)

        clave_mediana = hijo.claves[t - 1]
        valor_mediano = hijo.valores[t - 1]

        # Claves y valores que se mueven al nuevo nodo
        nuevo.claves = hijo.claves[t:]
        nuevo.valores = hijo.valores[t:]
        hijo.claves = hijo.claves[: t - 1]
        hijo.valores = hijo.valores[: t - 1]

        # Si no es hoja, mover hijos
        if not hijo.es_hoja:
            nuevo.hijos = hijo.hijos[t:]
            hijo.hijos = hijo.hijos[:t]

        padre.hijos.insert(indice + 1, nuevo)
        padre.claves.insert(indice, clave_mediana)
        padre.valores.insert(indice, valor_mediano)

    def recorrer(self) -> List[ArchivoIndexEntry]:
        resultado: List[ArchivoIndexEntry] = []
        self._recorrer(self.raiz, resultado)
        return resultado

    def _recorrer(self, nodo: BTreeNode, acumulado: List[ArchivoIndexEntry]):
        if nodo.es_hoja:
            for valores in nodo.valores:
                acumulado.extend(valores)
        else:
            for i, valores in enumerate(nodo.valores):
                self._recorrer(nodo.hijos[i], acumulado)
                acumulado.extend(valores)
            self._recorrer(nodo.hijos[-1], acumulado)

    def buscar_por_fragmento(self, fragmento: str) -> List[ArchivoIndexEntry]:
        fragmento = fragmento.lower()
        coincidencias: List[ArchivoIndexEntry] = []
        self._buscar_fragmento(self.raiz, fragmento, coincidencias)
        return coincidencias

    def _buscar_fragmento(self, nodo: BTreeNode, fragmento: str, acumulado: List[ArchivoIndexEntry]):
        if nodo.es_hoja:
            for clave, valores in zip(nodo.claves, nodo.valores):
                if fragmento in clave:
                    acumulado.extend(valores)
        else:
            for i, (clave, valores) in enumerate(zip(nodo.claves, nodo.valores)):
                self._buscar_fragmento(nodo.hijos[i], fragmento, acumulado)
                if fragmento in clave:
                    acumulado.extend(valores)
            self._buscar_fragmento(nodo.hijos[-1], fragmento, acumulado)


class IndiceGlobalArchivos:
    """Fachada del índice global basado en Arbol B."""

    def __init__(self, grado_minimo: int = 2):
        self.grado_minimo = grado_minimo
        self.arbol = BTree(grado_minimo)

    @staticmethod
    def calcular_tamano_kb(contenido: str) -> int:
        if contenido is None:
            return 0
        bytes_len = len(contenido.encode("utf-8"))
        return max(1, math.ceil(bytes_len / 1024))

    def limpiar(self):
        self.arbol = BTree(self.grado_minimo)

    def insertar_archivo(self, archivo, ruta_completa: str):
        entrada = ArchivoIndexEntry(
            archivo.nombre,
            ruta_completa,
            self.calcular_tamano_kb(getattr(archivo, "contenido", "")),
            getattr(archivo, "fecha_creacion", ""),
            getattr(archivo, "fecha_modificacion", ""),
            getattr(archivo, "extension", ""),
        )
        self.arbol.insertar(archivo.nombre.lower(), entrada)

    def eliminar_por_ruta(self, ruta_completa: str) -> bool:
        """Elimina una entrada exacta por ruta. Reconstruye el árbol si encuentra coincidencia."""
        ruta_norm = self._normalizar_ruta(ruta_completa)
        restantes = [e for e in self.arbol.recorrer() if self._normalizar_ruta(e.ruta_completa) != ruta_norm]
        if len(restantes) == len(self.arbol.recorrer()):
            return False
        self._reconstruir_desde_lista(restantes)
        return True

    def eliminar_por_prefijo(self, prefijo: str) -> int:
        """Elimina todas las entradas cuyo path comience con el prefijo indicado. Retorna cuantas eliminó."""
        pref = self._normalizar_ruta(prefijo)
        entradas = self.arbol.recorrer()
        restantes = [e for e in entradas if not self._normalizar_ruta(e.ruta_completa).startswith(pref)]
        eliminados = len(entradas) - len(restantes)
        if eliminados > 0:
            self._reconstruir_desde_lista(restantes)
        return eliminados

    def renombrar_ruta(self, ruta_anterior: str, nombre_nuevo: str, ruta_nueva: str) -> bool:
        """Actualiza nombre y ruta de una entrada exacta. Reconstruye a partir de la lista resultante."""
        ruta_old = self._normalizar_ruta(ruta_anterior)
        actualizado = False
        entradas = []
        for entrada in self.arbol.recorrer():
            if self._normalizar_ruta(entrada.ruta_completa) == ruta_old:
                entrada.nombre = nombre_nuevo
                entrada.ruta_completa = ruta_nueva
                actualizado = True
            entradas.append(entrada)
        if actualizado:
            self._reconstruir_desde_lista(entradas)
        return actualizado


    def buscar_parcial(self, fragmento: str) -> List[ArchivoIndexEntry]:
        return sorted(
            self.arbol.buscar_por_fragmento(fragmento),
            key=lambda e: (e.nombre.lower(), e.ruta_completa.lower()),
        )

    def buscar_rango(self, minimo_kb: Optional[int], maximo_kb: Optional[int]) -> List[ArchivoIndexEntry]:
        resultado = []
        for entrada in self.arbol.recorrer():
            if minimo_kb is not None and entrada.tamano_kb < minimo_kb:
                continue
            if maximo_kb is not None and entrada.tamano_kb > maximo_kb:
                continue
            resultado.append(entrada)
        return sorted(resultado, key=lambda e: (e.tamano_kb, e.ruta_completa.lower()))

    def buscar_combinado(
        self,
        fragmento: Optional[str],
        minimo_kb: Optional[int],
        maximo_kb: Optional[int],
    ) -> List[ArchivoIndexEntry]:
        candidatos = (
            self.arbol.buscar_por_fragmento(fragmento)
            if fragmento
            else self.arbol.recorrer()
        )
        resultado = []
        for entrada in candidatos:
            if minimo_kb is not None and entrada.tamano_kb < minimo_kb:
                continue
            if maximo_kb is not None and entrada.tamano_kb > maximo_kb:
                continue
            resultado.append(entrada)
        return sorted(
            resultado,
            key=lambda e: (e.nombre.lower(), e.tamano_kb, e.ruta_completa.lower()),
        )

    def serializar(self) -> List[dict]:
        return [entrada.to_dict() for entrada in self.arbol.recorrer()]

    def deserializar(self, datos: List[dict]):
        self.limpiar()
        for entrada_dict in datos:
            entrada = ArchivoIndexEntry.from_dict(entrada_dict)
            self.arbol.insertar(entrada.nombre.lower(), entrada)

    def resumen(self) -> int:
        return len(self.arbol.recorrer())

    # --- utilidades privadas ---
    @staticmethod
    def _normalizar_ruta(ruta: str) -> str:
        return ruta.replace("\\", "/").strip()

    def _reconstruir_desde_lista(self, entradas: List[ArchivoIndexEntry]):
        self.limpiar()
        for entrada in entradas:
            self.arbol.insertar(entrada.nombre.lower(), entrada)
