# main.py
"""
Modulo Principal - Punto de entrada unico
Muy bajo acoplamiento - solo importa sistema_archivos
"""

from sistema_archivos import SistemaArchivos

def main():
    """Funcion principal del sistema"""
    try:
        sistema = SistemaArchivos()
        sistema.iniciar_consola()
    except Exception as e:
        print(f"Error iniciando el sistema: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())