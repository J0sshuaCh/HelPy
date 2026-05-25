import os
import sys
import ctypes

def diagnose_dll(dll_path):
    print(f"Diagnosing {dll_path}...")
    if not os.path.exists(dll_path):
        print("ERROR: File does not exist.")
        return

    # Try to load with WinDLL
    try:
        # Set DLL search path to the DLL's directory
        dll_dir = os.path.dirname(dll_path)
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(dll_dir)
        os.environ["PATH"] = dll_dir + os.pathsep + os.environ["PATH"]
        
        ctypes.WinDLL(dll_path)
        print("SUCCESS: DLL loaded successfully with ctypes.")
    except Exception as e:
        print(f"FAILURE: Could not load DLL. Error: {e}")
        
        # Check for common dependencies in System32
        common_deps = ["vcruntime140.dll", "msvcp140.dll", "concrt140.dll", "vccorlib140.dll"]
        for dep in common_deps:
            dep_path = os.path.join("C:\\Windows\\System32", dep)
            if os.path.exists(dep_path):
                print(f"Found {dep} in System32.")
            else:
                print(f"MISSING {dep} in System32!")

if __name__ == "__main__":
    # Path to c10.dll in venv
    base_path = r"C:\Users\I5\Documents\Proyectos\AYUDIN"
    c10_path = os.path.join(base_path, "venv", "Lib", "site-packages", "torch", "lib", "c10.dll")
    diagnose_dll(c10_path)
