import pandas as pd
import random
import numpy as np

# Configuración
INPUT_FILE = "bitacora_final_ready_for_django.csv"
OUTPUT_FILE = "bitacora_final_ready_for_django_v2.csv"

# Banco de datos dummy
NOMBRES = ["JUAN", "PEDRO", "DIEGO", "MARIA", "ANA", "JOSE", "LUIS", "CARLOS", "JORGE", "MIGUEL", "JAVIERA", "CONSTANZA", "CAMILA", "VALENTINA"]
APELLIDOS = ["GONZALEZ", "MUNOZ", "ROJAS", "DIAZ", "PEREZ", "SOTO", "CONTRERAS", "SILVA", "MARTINEZ", "SEPULVEDA", "MORALES", "RODRIGUEZ"]

def generar_nombre_falso():
    n1 = random.choice(NOMBRES)
    n2 = random.choice(NOMBRES)
    a1 = random.choice(APELLIDOS)
    a2 = random.choice(APELLIDOS)
    return f"{n1} {n2} {a1} {a2}"

def estandarizar_nombre(val):
    # Si es nulo, vacío o "nan", generamos uno falso
    if pd.isna(val) or str(val).strip().lower() in ["", "nan", "none"]:
        return generar_nombre_falso()
    
    # Si existe, lo pasamos a mayúsculas y quitamos espacios extra
    return str(val).strip().upper()

# Ejecución
print("💅 Maquillando datos...")
df = pd.read_csv(INPUT_FILE)

# Contar vacíos antes
vacios = df['nombre'].isna().sum() + (df['nombre'] == "").sum()
print(f"Nombres vacíos detectados: {vacios}")

# Aplicar transformación
df['nombre'] = df['nombre'].apply(estandarizar_nombre)

# Guardar
df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
print(f"✅ Listo. Archivo '{OUTPUT_FILE}' generado con nombres en MAYÚSCULAS y sin vacíos.")