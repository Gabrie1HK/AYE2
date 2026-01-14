"""
Modulo de Configuracion
Centraliza parametros ajustables del sistema.
"""

import json
import os
from typing import Dict


class Configuracion:
    """
    Maneja la configuracion del sistema.

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
            "comandos_activados": [
                "cd",
                "mkdir",
                "type",
                "rmdir",
                "rm",
                "rename",
                "dir",
                "log",
                "clear log",
                "index",
                "backup",
                "respaldar",
            ],
            "habilitar_chatbot": True,
            "unidades": ["C:", "D:", "F:"],
            "log_operaciones": True,
            "modelo_ia": "gemini-2.5-flash",
        }

        try:
            if os.path.exists(self.archivo_config):
                with open(self.archivo_config, "r", encoding="utf-8") as f:
                    config_cargada = json.load(f)
                    config_merged = {**config_por_defecto, **config_cargada}
                    if "comandos_activados" in config_merged:
                        requeridos = {"index", "rm", "rename", "backup", "respaldar"}
                        for cmd in requeridos:
                            if cmd not in config_merged["comandos_activados"]:
                                config_merged["comandos_activados"].append(cmd)
                    return config_merged
        except Exception as e:
            print(f"Error cargando configuracion: {e}")

        return config_por_defecto

    def guardar_configuracion(self) -> bool:
        """Guarda la configuracion en archivo JSON"""
        try:
            with open(self.archivo_config, "w", encoding="utf-8") as f:
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
