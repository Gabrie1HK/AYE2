# estructuras_datos.py
"""
Modulo de Estructuras de Datos
Implementa TDA Cola y Pila usando listas enlazadas
Bajo acoplamiento - solo exporta clases Cola y Pila
"""

class Nodo:
    """
    Nodo basico para listas enlazadas
    
    Unidad fundamental de almacenamiento dinámico.
    Permite crear estructuras de datos que crecen dinámicamente en memoria,
    enlazando cada elemento con el siguiente mediante referencias (punteros).
    """
    def __init__(self, valor=None):
        self.valor = valor
        self.siguiente = None

class Pila:
    """
    Implementacion de Pila (LIFO) usando lista enlazada
    
    Estructura de datos LIFO (Last In, First Out).
    Se utiliza en el proyecto para gestionar el historial de operaciones y errores.
    Es ideal para historiales porque lo último que hiciste es lo primero que querrías ver o deshacer.
    """
    
    def __init__(self):
        self.cabeza = None
        self.longitud = 0
    
    def apilar(self, valor):
        nuevo_nodo = Nodo(valor)
        nuevo_nodo.siguiente = self.cabeza
        self.cabeza = nuevo_nodo
        self.longitud += 1
    
    def desapilar(self):
        if self.cabeza is None:
            return None
        valor = self.cabeza.valor
        self.cabeza = self.cabeza.siguiente
        self.longitud -= 1
        return valor
    
    def esta_vacia(self):
        return self.cabeza is None
    
    def ver_tope(self):
        return self.cabeza.valor if self.cabeza else None
    
    def __len__(self):
        return self.longitud
    
    def __iter__(self):
        actual = self.cabeza
        while actual:
            yield actual.valor
            actual = actual.siguiente

class Cola:
    """
    Implementacion de Cola (FIFO) usando lista enlazada
    
    Estructura de datos FIFO (First In, First Out).
    Se utiliza para almacenar el contenido de las carpetas.
    Garantiza que los elementos se mantengan en el orden en que fueron agregados,
    simulando una lista de archivos ordenada temporalmente.
    """
    
    def __init__(self):
        self.frente = None
        self.final = None
        self.longitud = 0
    
    def encolar(self, valor):
        nuevo_nodo = Nodo(valor)
        if self.final is None:
            self.frente = self.final = nuevo_nodo
        else:
            self.final.siguiente = nuevo_nodo
            self.final = nuevo_nodo
        self.longitud += 1
    
    def desencolar(self):
        if self.frente is None:
            return None
        valor = self.frente.valor
        self.frente = self.frente.siguiente
        if self.frente is None:
            self.final = None
        self.longitud -= 1
        return valor
    
    def esta_vacia(self):
        return self.frente is None
    
    def ver_frente(self):
        return self.frente.valor if self.frente else None
    
    def __len__(self):
        return self.longitud
    
    def __iter__(self):
        actual = self.frente
        while actual:
            yield actual.valor
            actual = actual.siguiente