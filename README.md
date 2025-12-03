# Proyecto Sistema de Archivos con IA

Este proyecto simula un sistema de archivos con comandos básicos (cd, mkdir, dir, etc.) y cuenta con un asistente de IA integrado para interpretar comandos en lenguaje natural.

## Requisitos

- Python 3.8 o superior
- Conexión a Internet (para la IA)

## Instalación

1. Clonar el repositorio o descargar el código.
2. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración de la API Key (Importante)

Para que la funcionalidad de IA funcione, se necesita una API Key de Google Gemini.

1. Busca el archivo llamado `.env.example` en la carpeta del proyecto.
2. Renómbralo a `.env` (o crea uno nuevo con ese nombre).
3. Abre el archivo `.env` y pega tu API Key:
   ```
   GEMINI_API_KEY=AIzaSy... (tu clave real aquí)
   ```

> **Nota para el evaluador:** La API Key no se incluye en el repositorio por seguridad. Por favor, utilice la clave proporcionada en la entrega de la tarea o genere una propia en Google AI Studio.

## Ejecución

Ejecuta el archivo principal:
```bash
python main.py
```
