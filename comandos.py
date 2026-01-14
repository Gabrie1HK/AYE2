# comandos.py
"""
Modulo de Comandos
Soporta multiunidades, arbol n-ario de carpetas y BST de archivos.
"""

from abc import ABC, abstractmethod
from typing import List


class Comando(ABC):
    """Interfaz base para comandos."""

    @abstractmethod
    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        pass

    @abstractmethod
    def obtener_nombre(self) -> str:
        pass

    def obtener_uso(self) -> str:
        return f"Uso: {self.obtener_nombre()} [argumentos]"


class ComandoCD(Comando):
    """Cambiar directorio (incluye salto de unidad)."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if not argumentos:
            return self.obtener_uso()
        ruta = argumentos[0]
        sistema.registrar_operacion(f"cd {ruta}")
        unidad, carpeta, error = sistema.resolver_ruta(ruta)
        if error:
            return error
        sistema.unidad_actual = unidad
        sistema.directorio_actual = carpeta
        sistema.ruta_actual = sistema.ruta_absoluta(carpeta)
        return f"Directorio actual: {sistema.ruta_actual}"

    def obtener_nombre(self) -> str:
        return "cd"

    def obtener_uso(self) -> str:
        return "cd <ruta> (soporta unidad, absoluta, relativa, ..)"


class ComandoMKDIR(Comando):
    """Crear carpeta en cualquier ruta/unidad."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if not argumentos:
            return self.obtener_uso()
        ruta_completa = argumentos[0]
        sistema.registrar_operacion(f"mkdir {ruta_completa}")
        ruta_norm = ruta_completa.replace('\\', '/')
        if '/' in ruta_norm:
            partes = [p for p in ruta_norm.split('/') if p != ""]
            nombre_carpeta = partes[-1]
            ruta_destino = '/'.join(partes[:-1])
        else:
            nombre_carpeta = ruta_norm
            ruta_destino = ""
        if not self._validar_nombre(nombre_carpeta):
            return f"Nombre de carpeta invalido: {nombre_carpeta}"
        unidad_destino, carpeta_destino, error = sistema.resolver_ruta(ruta_destino)
        if error:
            return error
        if carpeta_destino.buscar_carpeta(nombre_carpeta) or carpeta_destino.buscar_archivo(nombre_carpeta):
            return f"Error: Ya existe un elemento llamado '{nombre_carpeta}' en este directorio."
        from entidades_fs import Carpeta
        nueva_carpeta = Carpeta(nombre_carpeta, padre=carpeta_destino)
        carpeta_destino.agregar_carpeta(nueva_carpeta)
        sistema.unidad_actual = unidad_destino
        sistema.directorio_actual = carpeta_destino
        sistema.ruta_actual = sistema.ruta_absoluta(carpeta_destino)
        sistema.respaldar_automatico()
        sistema.reconstruir_indice_global()
        return f"Carpeta '{nombre_carpeta}' creada exitosamente en {sistema.ruta_absoluta(carpeta_destino)}"

    def _validar_nombre(self, nombre: str) -> bool:
        caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return all(c not in nombre for c in caracteres_invalidos) and nombre.strip()

    def obtener_nombre(self) -> str:
        return "mkdir"

    def obtener_uso(self) -> str:
        return "mkdir <ruta>"


class ComandoTYPE(Comando):
    """Crear archivo de texto en cualquier ruta/unidad."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if len(argumentos) < 2:
            return self.obtener_uso()
        ruta_completa = argumentos[0]
        contenido = ' '.join(argumentos[1:]).strip('"')
        ruta_norm = ruta_completa.replace('\\', '/')
        if '/' in ruta_norm:
            partes = [p for p in ruta_norm.split('/') if p != ""]
            nombre_archivo = partes[-1]
            ruta_destino = '/'.join(partes[:-1])
        else:
            nombre_archivo = ruta_norm
            ruta_destino = ""
        if not self._validar_nombre_archivo(nombre_archivo):
            return f"Nombre de archivo invalido: {nombre_archivo}"
        unidad_destino, carpeta_destino, error = sistema.resolver_ruta(ruta_destino)
        if error:
            return error
        if carpeta_destino.buscar_archivo(nombre_archivo) or carpeta_destino.buscar_carpeta(nombre_archivo):
            return f"Error: Ya existe un elemento llamado '{nombre_archivo}' en este directorio."
        from entidades_fs import Archivo
        nuevo_archivo = Archivo(nombre_archivo, contenido)
        if not carpeta_destino.agregar_archivo(nuevo_archivo):
            return f"Error: Ya existe un archivo llamado '{nombre_archivo}'."
        ruta_archivo = f"{sistema.ruta_absoluta(carpeta_destino)}/{nombre_archivo}"
        # Indexa el archivo en el B-Tree global
        sistema.indice_global.insertar_archivo(nuevo_archivo, ruta_archivo)
        sistema.unidad_actual = unidad_destino
        sistema.directorio_actual = carpeta_destino
        sistema.ruta_actual = sistema.ruta_absoluta(carpeta_destino)
        sistema.registrar_operacion(f'type {ruta_archivo} "{contenido}"')
        sistema.respaldar_automatico()
        return (f"Archivo '{nombre_archivo}' creado correctamente en {sistema.ruta_absoluta(carpeta_destino)}\n"
                f"Contenido guardado: \"{contenido}\"")

    def _validar_nombre_archivo(self, nombre: str) -> bool:
        caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return all(c not in nombre for c in caracteres_invalidos) and nombre.strip() and '.' in nombre

    def obtener_nombre(self) -> str:
        return "type"

    def obtener_uso(self) -> str:
        return 'type <ruta_archivo> "<contenido>"'


class ComandoRM(Comando):
    """Eliminar archivos individuales."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if not argumentos:
            return self.obtener_uso()
        ruta_objetivo = argumentos[0]
        ruta_norm = ruta_objetivo.replace('\\', '/').strip()
        nombre_archivo = ruta_norm.split('/')[-1]
        ruta_destino = '/'.join(ruta_norm.split('/')[:-1])
        unidad_destino, carpeta_destino, error = sistema.resolver_ruta(ruta_destino)
        if error:
            return error
        archivo = carpeta_destino.buscar_archivo(nombre_archivo)
        if archivo is None:
            return f"Error: El archivo '{nombre_archivo}' no existe en este directorio."
        if not carpeta_destino.eliminar_archivo(nombre_archivo):
            return f"Error interno al eliminar '{nombre_archivo}'."
        ruta_archivo = f"{sistema.ruta_absoluta(carpeta_destino)}/{nombre_archivo}"
        sistema.unidad_actual = unidad_destino
        sistema.directorio_actual = carpeta_destino
        sistema.ruta_actual = sistema.ruta_absoluta(carpeta_destino)
        sistema.registrar_operacion(f"rm {ruta_objetivo}")
        # Quita la ruta del indice B-Tree global
        sistema.indice_global.eliminar_por_ruta(ruta_archivo)
        sistema.respaldar_automatico()
        return f"Archivo '{nombre_archivo}' eliminado correctamente."

    def obtener_nombre(self) -> str:
        return "rm"

    def obtener_uso(self) -> str:
        return "rm <ruta_archivo>"


class ComandoRename(Comando):
    """Renombrar archivos o carpetas."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if len(argumentos) < 2:
            return self.obtener_uso()
        ruta_origen = argumentos[0].replace('\\', '/').strip()
        nuevo_nombre = argumentos[1].strip()
        if not self._validar_nombre(nuevo_nombre):
            return f"Nombre de archivo invalido: {nuevo_nombre}"
        partes = [p for p in ruta_origen.split('/') if p != ""]
        nombre_actual = partes[-1]
        ruta_destino = '/'.join(partes[:-1])
        unidad_destino, carpeta_destino, error = sistema.resolver_ruta(ruta_destino)
        if error:
            return error
        objetivo = carpeta_destino.buscar_carpeta(nombre_actual)
        es_carpeta = True
        if objetivo is None:
            objetivo = carpeta_destino.buscar_archivo(nombre_actual)
            es_carpeta = False
        if objetivo is None:
            return f"Error: No existe un elemento llamado '{nombre_actual}' en este directorio."
        if carpeta_destino.buscar_carpeta(nuevo_nombre) or carpeta_destino.buscar_archivo(nuevo_nombre):
            return f"Error: Ya existe un elemento llamado '{nuevo_nombre}' en este directorio."
        ruta_base = sistema.ruta_absoluta(carpeta_destino)
        ruta_anterior = f"{ruta_base}/{nombre_actual}"
        if es_carpeta:
            objetivo.nombre = nuevo_nombre
            objetivo.actualizar_modificacion()
            # Reindexa la carpeta completa en el B-Tree global
            sistema.indice_global.eliminar_por_prefijo(ruta_anterior)
            self._reinsertar_subarbol(objetivo, f"{ruta_base}/{nuevo_nombre}", sistema)
        else:
            archivo_obj = objetivo
            carpeta_destino.eliminar_archivo(nombre_actual)
            archivo_obj.nombre = nuevo_nombre
            archivo_obj.extension = archivo_obj._obtener_extension(nuevo_nombre)
            carpeta_destino.agregar_archivo(archivo_obj)
            # Actualiza la entrada en el indice B-Tree global
            sistema.indice_global.renombrar_ruta(ruta_anterior, nuevo_nombre, f"{ruta_base}/{nuevo_nombre}")
        sistema.unidad_actual = unidad_destino
        sistema.directorio_actual = carpeta_destino
        sistema.ruta_actual = sistema.ruta_absoluta(carpeta_destino)
        sistema.registrar_operacion(f"rename {ruta_origen} {nuevo_nombre}")
        sistema.respaldar_automatico()
        return f"Elemento '{nombre_actual}' renombrado a '{nuevo_nombre}'."

    def _validar_nombre(self, nombre: str) -> bool:
        caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return nombre.strip() and all(c not in nombre for c in caracteres_invalidos)

    def _reinsertar_subarbol(self, carpeta, ruta_base: str, sistema):
        for archivo in carpeta.archivos_en_orden("inorden"):
            sistema.indice_global.insertar_archivo(archivo, f"{ruta_base}/{archivo.nombre}")
        for sub in carpeta.subcarpetas:
            self._reinsertar_subarbol(sub, f"{ruta_base}/{sub.nombre}", sistema)

    def obtener_nombre(self) -> str:
        return "rename"

    def obtener_uso(self) -> str:
        return "rename <ruta_origen> <nuevo_nombre>"


class ComandoRMDIR(Comando):
    """Eliminar directorios; soporta /s /q."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if not argumentos:
            return self.obtener_uso()
        flags = []
        ruta_objetivo = None
        for arg in argumentos:
            if arg.startswith('/'):
                flags.append(arg.upper())
            else:
                ruta_objetivo = arg
        if ruta_objetivo is None:
            return "Error: Se requiere especificar un directorio"
        unidad_destino, carpeta_destino, error = sistema.resolver_ruta(ruta_objetivo)
        if error:
            return error
        if carpeta_destino.padre is None:
            return "Error: No se puede eliminar la raiz de la unidad."
        if (carpeta_destino.subcarpetas or carpeta_destino.archivos_raiz) and '/S' not in flags:
            return f"Error: La carpeta '{carpeta_destino.nombre}' no esta vacia. Use /s para eliminar recursivamente."
        if '/S' in flags:
            self._eliminar_recursivo(carpeta_destino)
            carpeta_destino.padre.eliminar_carpeta(carpeta_destino)
        else:
            if not carpeta_destino.padre.eliminar_carpeta(carpeta_destino):
                return f"Error interno al intentar eliminar la carpeta '{carpeta_destino.nombre}'."
        sistema.unidad_actual = unidad_destino
        sistema.directorio_actual = carpeta_destino.padre
        sistema.ruta_actual = sistema.ruta_absoluta(carpeta_destino.padre)
        # Elimina todas las rutas de la carpeta en el indice B-Tree global
        sistema.indice_global.eliminar_por_prefijo(sistema.ruta_absoluta(carpeta_destino))
        sistema.registrar_operacion(f"rmdir {ruta_objetivo}")
        sistema.respaldar_automatico()
        return f"Carpeta '{carpeta_destino.nombre}' eliminada exitosamente."

    def _eliminar_recursivo(self, carpeta):
        for sub in list(carpeta.subcarpetas):
            self._eliminar_recursivo(sub)
            carpeta.eliminar_carpeta(sub)
        for archivo in carpeta.archivos_en_orden("inorden"):
            carpeta.eliminar_archivo(archivo.nombre)

    def obtener_nombre(self) -> str:
        return "rmdir"

    def obtener_uso(self) -> str:
        return "rmdir <ruta_carpeta> [/s] [/q]"


class ComandoDIR(Comando):
    """Listar contenido o realizar busquedas avanzadas."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if argumentos and argumentos[0] == "search":
            return self._buscar(sistema, argumentos[1:])
        ruta = argumentos[0] if argumentos else ""
        if ruta:
            return self._listar_ruta(sistema, ruta)
        return self._listar_actual(sistema)

    def _listar_ruta(self, sistema, ruta: str) -> str:
        _, carpeta_destino, error = sistema.resolver_ruta(ruta)
        if error:
            return error
        return self._formatear_listado(sistema, carpeta_destino, sistema.ruta_absoluta(carpeta_destino))

    def _listar_actual(self, sistema) -> str:
        return self._formatear_listado(sistema, sistema.directorio_actual, sistema.ruta_absoluta(sistema.directorio_actual))

    def _formatear_listado(self, sistema, carpeta, ruta_texto):
        sistema.registrar_operacion("dir")
        resultado = [f"Directorio de {ruta_texto}", "-" * 40]
        elementos = carpeta.listar_elementos()
        if not elementos:
            resultado.append("El directorio esta vacio")
        else:
            for elemento in elementos:
                resultado.append(str(elemento))
        resultado.append(f"\nTotal: {len(elementos)} elemento(s)")
        return "\n".join(resultado)

    def _buscar(self, sistema, args: List[str]) -> str:
        if not args:
            return "dir search <nombre_directorio> | dir search -file <texto> [-range min-max]"
        if args[0] != "-file":
            nombre_dir = args[0]
            objetivo = self._buscar_directorio(sistema.directorio_actual, nombre_dir)
            if objetivo is None:
                return f"No se encontro el directorio '{nombre_dir}'."
            rutas = []
            for carpeta in objetivo.recorrer_subcarpetas_postorden():
                rutas.append(sistema.ruta_absoluta(carpeta))
                for arch in carpeta.archivos_en_orden("inorden"):
                    rutas.append(f"{sistema.ruta_absoluta(carpeta)}/{arch.nombre}")
            return "\n".join([f"Postorden de {sistema.ruta_absoluta(objetivo)}:"] + rutas)
        if len(args) < 2:
            return "Error: Falta texto para -file"
        texto = args[1].lower()
        minimo = None
        maximo = None
        if len(args) > 2 and args[2] == "-range" and len(args) > 3:
            rango = args[3]
            if "-" not in rango:
                return "Error: formato de rango invalido. Use min-max"
            partes = rango.split("-")
            try:
                minimo = int(partes[0]) if partes[0] else None
                maximo = int(partes[1]) if len(partes) > 1 and partes[1] else None
            except ValueError:
                return "Error: los limites de rango deben ser enteros."
        resultados = []
        orden = "preorden" if maximo is None and minimo is None else "inorden"
        self._buscar_archivos(sistema, sistema.directorio_actual, texto, minimo, maximo, resultados, orden=orden)
        if not resultados:
            return "No se encontraron archivos que coincidan."
        encabezado = "Busqueda de archivos"
        if minimo is not None or maximo is not None:
            partes = []
            if minimo is not None:
                partes.append(f">= {minimo} KB")
            if maximo is not None:
                partes.append(f"<= {maximo} KB")
            encabezado += " (" + " y ".join(partes) + ")"
        lineas = [encabezado]
        for idx, (ruta, tam) in enumerate(resultados, start=1):
            lineas.append(f"{idx}. {ruta} ({tam} KB)")
        return "\n".join(lineas)

    def _buscar_directorio(self, carpeta, nombre: str):
        if carpeta.nombre.lower() == nombre.lower():
            return carpeta
        for sub in carpeta.subcarpetas:
            encontrado = self._buscar_directorio(sub, nombre)
            if encontrado:
                return encontrado
        return None

    def _buscar_archivos(self, sistema, carpeta, texto, minimo, maximo, salida, orden="preorden"):
        if orden == "preorden":
            self._procesar_archivos_carpeta(sistema, carpeta, texto, minimo, maximo, salida)
        for sub in carpeta.subcarpetas:
            self._buscar_archivos(sistema, sub, texto, minimo, maximo, salida, orden)
        if orden == "postorden":
            self._procesar_archivos_carpeta(sistema, carpeta, texto, minimo, maximo, salida)
        if orden == "inorden":
            if carpeta.subcarpetas:
                mid = len(carpeta.subcarpetas) // 2
                for sub in carpeta.subcarpetas[:mid]:
                    self._buscar_archivos(sistema, sub, texto, minimo, maximo, salida, orden)
                self._procesar_archivos_carpeta(sistema, carpeta, texto, minimo, maximo, salida)
                for sub in carpeta.subcarpetas[mid:]:
                    self._buscar_archivos(sistema, sub, texto, minimo, maximo, salida, orden)
            else:
                self._procesar_archivos_carpeta(sistema, carpeta, texto, minimo, maximo, salida)

    def _procesar_archivos_carpeta(self, sistema, carpeta, texto, minimo, maximo, salida):
        for archivo in carpeta.archivos_en_orden("inorden"):
            if texto in archivo.nombre.lower():
                tam_kb = sistema.indice_global.calcular_tamano_kb(archivo.contenido)
                if minimo is not None and tam_kb < minimo:
                    continue
                if maximo is not None and tam_kb > maximo:
                    continue
                salida.append((f"{sistema.ruta_absoluta(carpeta)}/{archivo.nombre}", tam_kb))

    def obtener_nombre(self) -> str:
        return "dir"

    def obtener_uso(self) -> str:
        return "dir [ruta] | dir search ..."


class ComandoLOG(Comando):
    """Mostrar historial de operaciones."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        sistema.registrar_operacion("log")
        resultado = ["--- Historial de Operaciones (LIFO) ---"]
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
            resultado.append(operacion)
        return "\n".join(resultado)

    def obtener_nombre(self) -> str:
        return "log"

    def obtener_uso(self) -> str:
        return "log (muestra el historial de operaciones)"


class ComandoClearLog(Comando):
    """Limpiar historial de operaciones y errores."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        sistema.registrar_operacion("clear log")
        sistema.limpiar_historial()
        sistema.limpiar_errores()
        return "El historial de errores y operaciones ha sido limpiado."

    def obtener_nombre(self) -> str:
        return "clear log"

    def obtener_uso(self) -> str:
        return "clear log (limpia el historial de operaciones y errores)"


class ComandoIndexSearch(Comando):
    """Consulta el indice global basado en Arbol B."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        if not argumentos or argumentos[0].lower() != "search":
            return self.obtener_uso()
        sistema.registrar_operacion("index search")
        nombre_filtro = None
        minimo = None
        maximo = None
        i = 1
        while i < len(argumentos):
            arg = argumentos[i]
            if arg == "-range" and i + 1 < len(argumentos):
                rango = argumentos[i + 1]
                if "-" not in rango:
                    return "Error: formato de rango invalido. Use -range <min-max>"
                partes = rango.split("-")
                try:
                    minimo = int(partes[0]) if partes[0] else None
                    maximo = int(partes[1]) if len(partes) > 1 and partes[1] else None
                except ValueError:
                    return "Error: los limites de rango deben ser enteros."
                i += 2
                continue
            if arg == "-file" and i + 1 < len(argumentos):
                nombre_filtro = argumentos[i + 1]
                i += 2
                continue
            if nombre_filtro is None:
                nombre_filtro = arg
            i += 1
        if nombre_filtro is None and minimo is None and maximo is None:
            return "Error: proporcione un texto o un rango para buscar."
        # Consulta al indice B-Tree global con filtros combinados
        resultados = sistema.indice_global.buscar_combinado(nombre_filtro, minimo, maximo)
        if not resultados:
            return "No se encontraron coincidencias en el indice global."
        salida = []
        encabezado = "Resultados encontrados en indice global:" if minimo is None and maximo is None else "Archivos encontrados en el indice global"
        if minimo is not None or maximo is not None:
            rango_txt = []
            if minimo is not None:
                rango_txt.append(f"desde {minimo} KB")
            if maximo is not None:
                rango_txt.append(f"hasta {maximo} KB")
            encabezado += f" ({' y '.join(rango_txt)})"
        salida.append(encabezado)
        for idx, entrada in enumerate(resultados, start=1):
            salida.append(f"{idx}. {entrada.ruta_completa} ({entrada.tamano_kb} KB)")
        salida.append("Operacion completada.")
        return "\n".join(salida)

    def obtener_nombre(self) -> str:
        return "index"

    def obtener_uso(self) -> str:
        return "index search [-file <texto>] [-range <min-max>]"


class ComandoBackup(Comando):
    """Genera un respaldo inmediato."""

    def ejecutar(self, sistema, argumentos: List[str]) -> str:
        sistema.registrar_operacion("backup")
        resultado = sistema.respaldar_automatico()
        return resultado

    def obtener_nombre(self) -> str:
        return "backup"

    def obtener_uso(self) -> str:
        return "backup | respaldar"
