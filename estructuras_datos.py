# estructuras_datos.py
"""
Modulo de Estructuras de Datos
Implementa TDA Cola y Pila usando listas enlazadas
Bajo acoplamiento - solo exporta clases Cola y Pila
"""

class Nodo:
    """Nodo basico para listas enlazadas"""
    def __init__(self, valor=None):
        self.valor = valor
        self.siguiente = None

class Pila:
    """Implementacion de Pila (LIFO) usando lista enlazada"""
    
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

    def to_list(self) -> list:
        """Devuelve una lista de los elementos de la pila sin modificarla.

        El orden es desde el tope (ultimo apilado) hasta el fondo.
        """
        return list(self)

class Cola:
    """Implementacion de Cola (FIFO) usando lista enlazada"""
    
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