"""
Gestor de Respaldos
Serializa/deserializa el estado completo (unidades, arbol n-ario, BST de archivos e índice global).
"""

import json
import os
from datetime import datetime

from entidades_fs import Archivo, Carpeta, UnidadAlmacenamiento
from estructuras_datos import Pila


class GestorRespaldos:
    """
    Maneja los respaldos automaticos del sistema.

    Implementa la persistencia del estado del sistema serializando el arbol de directorios
    y los historiales de operaciones y errores.
    """

    def __init__(self, sistema, config):
        self.sistema = sistema
        self.config = config

    def respaldar_automatico(self) -> str:
        """Serializa unidades, carpetas (n-ario) y archivos (BST) en disco."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            ruta_respaldos = self.config.obtener_ruta_respaldos()
            os.makedirs(ruta_respaldos, exist_ok=True)
            archivo_respaldo = os.path.join(ruta_respaldos, f"respaldo_{timestamp}.json")

            datos_respaldo = {
                "fecha_respaldo": timestamp,
                "unidad_actual": getattr(self.sistema.unidad_actual, "nombre", ""),
                "ruta_actual": self.sistema.ruta_actual,
                "historial_operaciones": self._serializar_pila(self.sistema.historial_operaciones),
                "errores": self._serializar_pila(self.sistema.errores),
                "unidades": self._serializar_unidades(self.sistema.unidades),
                "indice_global": self.sistema.indice_global.serializar(),
            }

            with open(archivo_respaldo, "w", encoding="utf-8") as f:
                json.dump(datos_respaldo, f, indent=4, ensure_ascii=False)
            return f"Respaldo automatico realizado en {archivo_respaldo}"
        except Exception as e:
            return f"Error en respaldo automatico: {str(e)}"

    def cargar_ultimo_respaldo(self) -> bool:
        """Carga el ultimo respaldo disponible (unidades, rutas, pilas e índice)."""
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

            with open(ruta_completa, "r", encoding="utf-8") as f:
                datos = json.load(f)

            self.sistema.historial_operaciones = self._deserializar_pila(datos.get("historial_operaciones", []))
            self.sistema.errores = self._deserializar_pila(datos.get("errores", []))

            unidades_datos = datos.get("unidades")
            if unidades_datos:
                self.sistema.unidades = self._deserializar_unidades(unidades_datos)
                # Seleccionar unidad actual guardada
                nombre_unidad = datos.get("unidad_actual", "").rstrip(":") + ":"
                actual = self.sistema.unidades
                self.sistema.unidad_actual = actual
                while actual:
                    if actual.nombre.lower() == nombre_unidad.lower():
                        self.sistema.unidad_actual = actual
                        break
                    actual = actual.siguiente
                # Ajustar directorio actual con la ruta guardada
                ruta_guardada = datos.get("ruta_actual", self.sistema.unidad_actual.nombre)
                unidad_res, carpeta_res, error = self.sistema.resolver_ruta(ruta_guardada)
                if error:
                    self.sistema.directorio_actual = self.sistema.unidad_actual.raiz
                    self.sistema.ruta_actual = self.sistema.unidad_actual.nombre
                else:
                    self.sistema.unidad_actual = unidad_res
                    self.sistema.directorio_actual = carpeta_res
                    self.sistema.ruta_actual = self.sistema.ruta_absoluta(carpeta_res)

            indice_serializado = datos.get("indice_global")
            if indice_serializado:
                self.sistema.indice_global.deserializar(indice_serializado)
            else:
                self.sistema.reconstruir_indice_global()

            return True
        except Exception as e:
            print(f"Error cargando respaldo: {e}")
            return False

    def _serializar_unidades(self, cabeza: UnidadAlmacenamiento) -> list:
        unidades = []
        actual = cabeza
        while actual:
            unidades.append({
                "nombre": actual.nombre,
                "raiz": self._serializar_carpeta(actual.raiz),
            })
            actual = actual.siguiente
        return unidades

    def _serializar_carpeta(self, carpeta: Carpeta) -> dict:
        return {
            "tipo": "carpeta",
            "nombre": carpeta.nombre,
            "fecha_creacion": carpeta.fecha_creacion,
            "fecha_modificacion": carpeta.fecha_modificacion,
            "subcarpetas": [self._serializar_carpeta(sub) for sub in carpeta.subcarpetas],
            "archivos": [
                {
                    "tipo": "archivo",
                    "nombre": arch.nombre,
                    "contenido": arch.contenido,
                    "fecha_creacion": arch.fecha_creacion,
                    "fecha_modificacion": arch.fecha_modificacion,
                    "extension": arch.extension,
                }
                for arch in carpeta.archivos_en_orden("preorden")
            ],
        }

    def _deserializar_unidades(self, unidades_datos: list) -> UnidadAlmacenamiento:
        cabeza = None
        anterior = None
        for unidad_data in unidades_datos:
            unidad = UnidadAlmacenamiento(unidad_data.get("nombre", "C:"))
            unidad.raiz = self._deserializar_carpeta(unidad_data.get("raiz", {}), None)
            if cabeza is None:
                cabeza = unidad
            if anterior:
                anterior.siguiente = unidad
            anterior = unidad
        return cabeza

    def _deserializar_carpeta(self, datos_nodo: dict, padre) -> Carpeta:
        nueva_carpeta = Carpeta(datos_nodo.get("nombre", ""), padre)
        nueva_carpeta.fecha_creacion = datos_nodo.get("fecha_creacion", "")
        nueva_carpeta.fecha_modificacion = datos_nodo.get("fecha_modificacion", "")

        for sub_datos in datos_nodo.get("subcarpetas", []):
            sub_obj = self._deserializar_carpeta(sub_datos, nueva_carpeta)
            nueva_carpeta.agregar_carpeta(sub_obj)

        for arch_datos in datos_nodo.get("archivos", []):
            archivo_obj = Archivo(arch_datos.get("nombre", ""), arch_datos.get("contenido", ""))
            archivo_obj.fecha_creacion = arch_datos.get("fecha_creacion", "")
            archivo_obj.fecha_modificacion = arch_datos.get("fecha_modificacion", "")
            archivo_obj.extension = arch_datos.get("extension", archivo_obj.extension)
            nueva_carpeta.agregar_archivo(archivo_obj)

        return nueva_carpeta

    def _serializar_pila(self, pila) -> list:
        elementos = []
        pila_temp = Pila()
        while not pila.esta_vacia():
            elemento = pila.desapilar()
            elementos.append(elemento)
            pila_temp.apilar(elemento)
        while not pila_temp.esta_vacia():
            pila.apilar(pila_temp.desapilar())
        return elementos

    def _deserializar_pila(self, lista_elementos: list) -> Pila:
        """Reconstruye una pila desde una lista"""
        pila = Pila()
        for elemento in reversed(lista_elementos):
            pila.apilar(elemento)
        return pila
