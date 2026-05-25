from src.escucha import escuchar_usuario
from src.cerebro import pensar_respuesta

# Según el listado anterior:
# ID 2: Mezcla estéreo (Realtek(R) Audi, MME
# ID 14: Mezcla estéreo (Realtek(R) Audio), Windows WASAPI

def test_llamada():
    print("--- TEST ESCUCHA DE SISTEMA (LLAMADAS) ---")
    print("Asegúrate de tener la 'Mezcla estéreo' habilitada en Windows.")
    print("Reproduce algún audio o inicia una llamada para probar.")
    
    # Probamos con el índice 2 (MME) o 14 (WASAPI)
    # Intentaremos con el 2 primero
    idx_mezcla = 2 
    
    texto = escuchar_usuario(device_index=idx_mezcla)
    print(f"Sistema detectó: {texto}")
    
    if texto and not texto.startswith("Error"):
        respuesta = pensar_respuesta(texto)
        print(f"IA: {respuesta}")

if __name__ == "__main__":
    test_llamada()
