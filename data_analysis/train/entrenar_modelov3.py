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

# --- LIMPIEZA AVANZADA ---
def limpiar_obs_avanzado(texto):
    if not isinstance(texto, str): return ""
    txt = str(texto).lower()
    # Quitar acentos básicos para estandarizar
    txt = txt.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    # Quitar números y signos
    txt = re.sub(r'\d+', '', txt)
    txt = re.sub(r'[^\w\s]', '', txt)
    return txt

df['obs_limpia'] = df['observaciones'].fillna('').apply(limpiar_obs_avanzado)

# Topamos valores extremos para que el gráfico no se rompa
df['rojos_topados'] = df['cant_rojos'].clip(upper=5)
df['amarillos_topados'] = df['cant_amarillos'].clip(upper=5)

# 2. Ingeniería de Características

# A. Datos Numéricos
scaler = StandardScaler()
X_colores = df[['rojos_topados', 'amarillos_topados']]
X_colores_scaled = scaler.fit_transform(X_colores)

# B. Datos de Texto (NLP Mejorado)
# LISTA NEGRA: Palabras que NO nos importan para detectar riesgo
mis_stopwords = [
    # Conectores
    'el', 'la', 'de', 'en', 'y', 'a', 'que', 'los', 'se', 'un', 'del', 'con', 'no', 'si', 'por', 'lo', 'su', 'para', 'al', 'es', 'son', 'como', 'pero', 'mas', 'esta', 'este', 'fue', 'ha',
    # Contexto irrelevante
    'estudiante', 'alumno', 'alumna', 'tutorado', 'tutor', 'carrera', 'universidad', 'año', 'semestre',
    # Datos Socioeconómicos/Perfil (que se repiten mucho y ensucian)
    'gratuidad', 'beca', 'fondo', 'solidario', 'cae', 'residencia', 'procedencia', 'beneficio', 'arancel',
    # Familia (Información de contexto, no alerta)
    'mama', 'papa', 'madre', 'padre', 'hermano', 'hermana', 'abuela', 'abuelo', 'tio', 'tia', 'vive', 'familia', 'hogar',
    # Rellenos comunes
    'bien', 'mal', 'regular', 'contacto', 'correo', 'telefono', 'whatsapp', 'celular', 'responde', 'contesta'
]

print("🧠 Analizando texto (buscando PATOLOGÍAS, no rellenos)...")
# ngram_range=(1,2) permite capturar frases de 2 palabras como "ansiedad severa" o "bajo rendimiento"
tfidf = TfidfVectorizer(
    max_features=100, 
    stop_words=mis_stopwords,
    ngram_range=(1, 2) 
)
X_texto = tfidf.fit_transform(df['obs_limpia']).toarray()

# C. Unir Matrices
# Le damos un poco más de peso al texto ahora que está limpio (multiplicamos por 1.5)
X_final = np.concatenate([X_colores_scaled, X_texto * 1.5], axis=1)

# 3. Entrenar Modelo
print("🤖 Entrenando IA (5 Clusters)...")
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
kmeans.fit(X_final)

df['cluster_id'] = kmeans.labels_

# 4. Interpretación Humana
print("\n--- 🔍 RADIOGRAFÍA DEL CURSO ---")
# Ordenamos por riesgo (suma de rojos + amarillos)
df['riesgo_score'] = df['cant_rojos'] * 2 + df['cant_amarillos']
promedios = df.groupby('cluster_id')['riesgo_score'].mean().sort_values()
mapa_orden = {old_id: new_id for new_id, old_id in enumerate(promedios.index)}
df['grupo_ordenado'] = df['cluster_id'].map(mapa_orden)

nombres_sugeridos = {
    0: "Sin Riesgo (Casos sanos)",
    1: "Riesgo Bajo/Latente",
    2: "Riesgo Medio",
    3: "Riesgo Alto (Alerta Académica)",
    4: "Crítico / Deserción Inminente"
}

for nivel in range(5):
    grupo = df[df['grupo_ordenado'] == nivel]
    if len(grupo) == 0: continue
    
    print(f"\n📂 {nombres_sugeridos[nivel]} (Grupo {nivel})")
    print(f"   👥 Cantidad: {len(grupo)} estudiantes")
    print(f"   📊 Promedios -> 🔴 Rojos: {grupo['cant_rojos'].mean():.1f} | 🟡 Amarillos: {grupo['cant_amarillos'].mean():.1f}")
    
    # Palabras clave (Mejoradas)
    if X_texto.shape[1] > 0:
        all_text = " ".join(grupo['obs_limpia'])
        from collections import Counter
        # Filtramos de nuevo por si acaso
        words = [w for w in all_text.split() if w not in mis_stopwords and len(w) > 3]
        # Buscamos bigramas manuales simples para mostrar
        common = Counter(words).most_common(6)
        temas = [w[0] for w in common]
        print(f"   🗣️ Se habla de: {temas}")

# 5. Guardar
joblib.dump({
    'model': kmeans, 
    'scaler': scaler, 
    'tfidf': tfidf,
    'mapa_orden': mapa_orden,
    'nombres_clusters': nombres_sugeridos
}, 'modelo_sat.pkl')
print("\n✅ Modelo actualizado y guardado.")