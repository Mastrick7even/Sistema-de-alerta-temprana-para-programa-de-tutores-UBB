import pandas as pd

# Cargar
df = pd.read_csv("bitacora_estructurada_final.csv")

# 1. VER quiénes son (Para tu tranquilidad mental)
duplicados = df[df.duplicated(subset=['Origen', 'Tutor', 'rut'], keep=False)]
if not duplicados.empty:
    print("\n🕵️‍♂️ DETECTIVE DE DUPLICADOS:")
    print(duplicados[['Origen', 'Tutor', 'rut', 'nombre']].sort_values(by='rut'))
    
    # 2. ELIMINARLOS (Quedarse con la primera aparición)
    # drop_duplicates mantiene la primera ocurrencia y borra las siguientes
    df_limpio = df.drop_duplicates(subset=['Origen', 'Tutor', 'rut'], keep='first')
    
    print(f"\n🔪 Se eliminaron {len(df) - len(df_limpio)} registros duplicados.")
    print(f"📉 Total final: {len(df_limpio)} registros únicos.")
    
    # Sobrescribir el archivo
    df_limpio.to_csv("bitacora_estructurada_final_v2.csv", index=False, encoding='utf-8-sig')
    print("✅ Archivo 'bitacora_estructurada_final_v2.csv' listo para inyección.")
else:
    print("✅ No hay duplicados que eliminar.")