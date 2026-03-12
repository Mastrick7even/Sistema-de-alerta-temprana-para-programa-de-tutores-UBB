import pandas as pd
import re

# 1. Función de Normalización (Limpieza Previa)
def normalizar_rut(val):
    """
    Transforma '12.345.678-k' en '12345678-K'.
    Quita puntos, espacios y hace mayúsculas.
    """
    if pd.isna(val): return ""
    return str(val).replace('.', '').strip().upper()

# 2. Función de Validación (Sobre el dato ya limpio)
def es_rut_real(val_limpio):
    """
    Valida que sea DIGITOS + GUION + DIGITO/K
    Ej: 12345678-K (Acepta de 1 a 9 millones, o 10-20 millones)
    """
    # Regex: Inicio ^, 1 a 9 digitos, guion, 1 digito o K, Fin $
    patron = r'^\d{1,9}-[\dK]$'
    return bool(re.match(patron, val_limpio))

# --- EJECUCIÓN ---
print("Cargando CSV...")
df = pd.read_csv("bitacora_estructurada_final_v2.csv")
print(f"Total inicial: {len(df)}")

# Paso A: Normalizar TODOS los RUTs primero
# Creamos una columna temporal para no perder el original si algo falla, 
# pero el objetivo es reemplazarlo.
df['rut_limpio'] = df['rut'].apply(normalizar_rut)

# Paso B: Filtrar Basura (Fechas, nombres, vacíos)
# Nos quedamos solo con los que cumplen el patrón XXXXXXXX-X
df_valido = df[df['rut_limpio'].apply(es_rut_real)].copy()
basura = df[~df['rut_limpio'].apply(es_rut_real)]

# Paso C: Reemplazar la columna 'rut' original con la versión limpia
df_valido['rut'] = df_valido['rut_limpio']
df_valido.drop(columns=['rut_limpio'], inplace=True)

# Reporte Brutal
print(f"\n🗑️ BASURA REAL ELIMINADA: {len(basura)} registros")
if not basura.empty:
    print("Ejemplos de lo eliminado (deberían ser fechas o textos raros):")
    print(basura[['Origen', 'rut']].head(5))

print(f"\n✅ REGISTROS VÁLIDOS RECUPERADOS: {len(df_valido)}")
print("Ejemplo de RUTs normalizados:")
print(df_valido['rut'].head(3))

# Guardar
df_valido.to_csv("bitacora_final_ready_for_django.csv", index=False, encoding='utf-8-sig')
print("\n💾 Archivo 'bitacora_final_ready_for_django.csv' generado correctamente.")