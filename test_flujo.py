from src.escucha import escuchar_usuario
from src.cerebro import pensar_respuesta

def test_flujo():
    print("--- INICIO TEST ---")
    
    # 1. Escuchar
    texto = escuchar_usuario()
    print(f"Usuario: {texto}")
    
    if texto and not texto.startswith("Error"):
        # 2. Pensar
        respuesta = pensar_respuesta(texto)
        print(f"IA: {respuesta}")
    else:
        print("No se pudo procesar la voz.")

if __name__ == "__main__":
    test_flujo()
