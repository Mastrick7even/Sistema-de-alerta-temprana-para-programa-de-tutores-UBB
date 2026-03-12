import pandas as pd

# Cargar
df = pd.read_csv("bitacora_estructurada_final.csv")
print(f"Total registros: {len(df)}")

# 1. Chequeo de Integridad Crítica
print("\n--- 1. Integridad Crítica ---")
sin_rut = df[df['rut'].isna() | (df['rut'] == "")]
print(f"Filas sin RUT (Basura): {len(sin_rut)}")

sin_tutor = df[df['Tutor'].isna() | (df['Tutor'] == "")]
print(f"Filas sin Tutor: {len(sin_tutor)}")

# 2. Chequeo de Anomalías en Alertas
print("\n--- 2. Anomalías en Alertas ---")
# Columnas de alerta
cols_alerta = [c for c in df.columns if "Alerta" in c]
# Filas que tienen texto en alertas pero NO tienen etiqueta de color (Posible pérdida de info)
for col in cols_alerta:
    # Busca celdas con texto pero sin [ROJO] ni [AMARILLO]
    problemas = df[
        df[col].notna() & 
        (df[col] != "") & 
        (~df[col].str.contains(r'\[ROJO\]|\[AMARILLO\]', na=False))
    ]
    if len(problemas) > 0:
        print(f"⚠️ {col}: {len(problemas)} registros tienen texto sin color (¿Es normal o se perdió el color?)")

# 3. Chequeo de Duplicados Lógicos
print("\n--- 3. Duplicados Lógicos ---")
# Un mismo RUT no debería aparecer 2 veces en el mismo archivo origen + misma hoja
duplicados = df[df.duplicated(subset=['Origen', 'Tutor', 'rut'], keep=False)]
print(f"Duplicados exactos (mismo alumno en misma hoja): {len(duplicados)}")

print("\n--- FIN DE AUDITORÍA ---")