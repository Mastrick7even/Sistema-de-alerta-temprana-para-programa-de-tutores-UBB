import pandas as pd
import numpy as np
import joblib
import re
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. Cargar Datos
try:
    df = pd.read_csv("dataset_sat_unificado.csv")
    # Limpiar nombres de columnas (quitar espacios extra)
    df.columns = df.columns.str.strip()
    print(f"📊 Cargados {len(df)} registros.")
except FileNotFoundError:
    print("❌ Error: No existe el CSV. Ejecuta procesar_data.py primero.")
    exit()

# --- MEJORA 1: Topar los valores extremos (Winsorizing suave) ---
# Esto evita que el alumno con 18 rojas rompa la escala para los demás.
# Todo lo que sea mayor a 5, lo dejamos en 5.
df['rojos_topados'] = df['cant_rojos'].clip(upper=5)
df['amarillos_topados'] = df['cant_amarillos'].clip(upper=5)

# --- MEJORA 2: Limpieza de Texto para NLP ---
def limpiar_obs(texto):
    if not isinstance(texto, str): return ""
    # Quitar números (teléfonos, ruts en el texto)
    txt = re.sub(r'\d+', '', texto)
    # Quitar caracteres raros
    txt = re.sub(r'[^\w\s]', '', txt)
    return txt.lower()

df['obs_limpia'] = df['observaciones'].fillna('').apply(limpiar_obs)

# 2. Ingeniería de Características

# A. Datos Numéricos (Usamos los topados)
scaler = StandardScaler()
X_colores = df[['rojos_topados', 'amarillos_topados']]
X_colores_scaled = scaler.fit_transform(X_colores)

# B. Datos de Texto (Sin números)
print("🧠 Analizando texto (sin teléfonos ni basura)...")
tfidf = TfidfVectorizer(
    max_features=50, 
    stop_words=['el', 'la', 'de', 'en', 'y', 'a', 'que', 'los', 'se', 'un', 'del', 'con', 'no', 'si', 'por', 'lo', 'su', 'para', 'al'] 
)
X_texto = tfidf.fit_transform(df['obs_limpia']).toarray()

# C. Unir Matrices
X_final = np.concatenate([X_colores_scaled, X_texto], axis=1)

# 3. Entrenar Modelo (Probamos con 5 Clusters para ver más detalle)
print("🤖 Entrenando K-Means con 5 Segmentos...")
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
kmeans.fit(X_final)

df['cluster_id'] = kmeans.labels_

# 4. Interpretación
print("\n--- 🔍 RESULTADOS MEJORADOS ---")
# Ordenamos los clusters por "gravedad" (promedio de rojos) para que sea fácil leer
promedios = df.groupby('cluster_id')['cant_rojos'].mean().sort_values()
mapa_orden = {old_id: new_id for new_id, old_id in enumerate(promedios.index)}

# Reordenamos el dataframe para mostrarlo ordenado
df['cluster_nivel'] = df['cluster_id'].map(mapa_orden)

for nivel in range(5):
    grupo = df[df['cluster_nivel'] == nivel]
    if len(grupo) == 0: continue
    
    print(f"\n👉 GRUPO {nivel} (Riesgo estimado: {nivel}/4):")
    print(f"   👥 Alumnos: {len(grupo)}")
    print(f"   🔴 Rojos Prom: {grupo['cant_rojos'].mean():.2f}")
    print(f"   🟡 Amarillos Prom: {grupo['cant_amarillos'].mean():.2f}")
    
    # Palabras clave
    if X_texto.shape[1] > 0:
        # Buscamos las palabras más frecuentes en este cluster
        indices_obs = grupo.index
        if len(indices_obs) > 0:
            # Truco simple: concatenar texto y ver palabras frecuentes
            all_text = " ".join(grupo['obs_limpia'])
            # Contar palabras (muy básico pero efectivo para print)
            from collections import Counter
            words = [w for w in all_text.split() if len(w) > 3 and w not in tfidf.stop_words]
            common = Counter(words).most_common(5)
            print(f"   📝 Temas: {[w[0] for w in common]}")

# 5. Guardar
print("\n💾 Guardando modelo mejorado...")
model_data = {
    'model': kmeans,
    'scaler': scaler,
    'tfidf': tfidf,
    'mapa_orden': mapa_orden # Guardamos el orden para saber cuál es el peor
}
joblib.dump(model_data, 'modelo_sat.pkl')
print("✅ Listo.")