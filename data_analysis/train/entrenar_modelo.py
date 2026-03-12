import pandas as pd
import numpy as np
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. Cargar Datos
try:
    df = pd.read_csv("dataset_sat_unificado.csv")
    # Limpiar nombres de columnas (quitar espacios extra)
    df.columns = df.columns.str.strip()
    print(f"📊 Cargados {len(df)} registros para entrenamiento.")
except FileNotFoundError:
    print("❌ Error: No se encuentra 'dataset_sat_unificado.csv'. Ejecuta procesar_data.py primero.")
    exit()

# 2. Ingeniería de Características (Feature Engineering)

# A. Datos Numéricos (Colores)
# Escalamos los datos para que 10 rojos no pesen infinitamente más que 1 amarillo
scaler = StandardScaler()
X_colores = df[['cant_rojos', 'cant_amarillos']].fillna(0) # Asegurate que los nombres coincidan con tu CSV
X_colores_scaled = scaler.fit_transform(X_colores)

# B. Datos de Texto (NLP - Observaciones)
# Usamos TF-IDF para convertir texto a números. 
print("🧠 Analizando lenguaje natural de observaciones...")
tfidf = TfidfVectorizer(
    max_features=50, # Nos quedamos con las 50 palabras más importantes (ej: "asistencia", "nota", "enfermedad")
    stop_words=['el', 'la', 'de', 'en', 'y', 'a', 'que', 'los', 'se', 'un', 'del', 'con', 'no', 'si', 'por', 'lo', 'su', 'para'] 
)
# Rellenamos vacíos
textos = df['observaciones'].fillna('')
X_texto = tfidf.fit_transform(textos).toarray()

# C. Unir todo en una sola matriz para el modelo
X_final = np.concatenate([X_colores_scaled, X_texto], axis=1)

# 3. Entrenar Modelo de Clustering
print("🤖 Entrenando K-Means (Buscando 3 grupos de riesgo)...")
# Definimos 3 clusters: Bajo, Medio, Alto
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans.fit(X_final)

# 4. Resultados Preliminares
df['cluster_id'] = kmeans.labels_

print("\n--- 🔍 INTERPRETACIÓN DE LOS CLUSTERS ---")
print("Revisa estos números para decidir cuál cluster es el de Riesgo Alto:")
for i in range(3):
    grupo = df[df['cluster_id'] == i]
    print(f"\n👉 CLUSTER {i}:")
    print(f"   👥 Cantidad de alumnos: {len(grupo)}")
    print(f"   🔴 Promedio Rojos: {grupo['cant_rojos'].mean():.2f}")
    print(f"   🟡 Promedio Amarillos: {grupo['cant_amarillos'].mean():.2f}")
    print(f"   📝 Palabras clave (Top 5):")
    # Truco para ver qué palabras pesan más en este cluster (si hay textos)
    if len(grupo) > 0 and X_texto.shape[1] > 0:
        # Esto es una simplificación visual
        ejemplos = grupo[grupo['observaciones'].str.len() > 5]['observaciones'].head(3).values
        for ej in ejemplos:
            print(f"      - \"{ej[:60]}...\"")

# 5. Guardar el Modelo
print("\n💾 Guardando cerebro en 'modelo_sat.pkl'...")
model_data = {
    'model': kmeans,
    'scaler': scaler,
    'tfidf': tfidf,
    # Este mapa lo actualizaremos manual después de ver tu output
    'descripciones': {0: 'Grupo A', 1: 'Grupo B', 2: 'Grupo C'} 
}
joblib.dump(model_data, 'modelo_sat.pkl')
print("✅ ¡Listo! Copia el output de arriba y pégalo en el chat.")