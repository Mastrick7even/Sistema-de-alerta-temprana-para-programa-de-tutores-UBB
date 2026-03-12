import pandas as pd
import numpy as np
import joblib
import re
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. Cargar Datos
try:
    df = pd.read_csv("bitacora_final_ready_for_django_v2.csv")
    # Limpiar nombres de columnas (quitar espacios extra)
    df.columns = df.columns.str.strip()
    print(f"📊 Cargados {len(df)} registros.")
except FileNotFoundError:
    print("❌ Error: No existe el CSV. Ejecuta procesar_data.py primero.")
    exit()

# --- LIMPIEZA AVANZADA ---
# --- 1.5. Calcular Métricas de Riesgo (Si no vienen en el CSV) ---
# Contamos cuántas veces aparece [ROJO] y [AMARILLO] en TODAS las columnas
def contar_etiquetas(row, etiqueta):
    conteo = 0
    for col in row.index:
        val = str(row[col])
        if etiqueta in val:
            conteo += val.count(etiqueta)
    return conteo

print("🧮 Calculando métricas de riesgo (Rojos/Amarillos)...")
df['cant_rojos'] = df.apply(lambda x: contar_etiquetas(x, '[ROJO]'), axis=1)
df['cant_amarillos'] = df.apply(lambda x: contar_etiquetas(x, '[AMARILLO]'), axis=1)

# --- CONSOLIDACIÓN DE TEXTO (CRÍTICO PARA NLP) ---
# Juntamos TODAS las columnas de Alerta + Observaciones en un solo texto
print("📝 Consolidando texto de TODAS las alertas...")

def consolidar_texto_completo(row):
    """Junta todas las columnas de Alerta + Observaciones en un solo string"""
    textos = []
    for col in row.index:
        if 'Alerta' in col or col == 'Observaciones':
            val = str(row[col])
            if val and val != 'nan' and len(val) > 2:
                textos.append(val)
    return " || ".join(textos)

df['texto_completo'] = df.apply(consolidar_texto_completo, axis=1)

# --- LIMPIEZA AVANZADA ---
def limpiar_obs_avanzado(texto):
    if not isinstance(texto, str): return ""
    txt = str(texto).lower()
    
    # PRIMERO: Quitar las etiquetas de color [ROJO] [AMARILLO] 
    txt = txt.replace('[rojo]', '').replace('[amarillo]', '')
    
    # Quitar acentos básicos para estandarizar
    txt = txt.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    # Quitar números y signos
    txt = re.sub(r'\d+', '', txt)
    txt = re.sub(r'[^\w\s]', '', txt)
    return txt

df['obs_limpia'] = df['texto_completo'].fillna('').apply(limpiar_obs_avanzado)

# Topamos valores extremos para que el gráfico no se rompa
df['rojos_topados'] = df['cant_rojos'].clip(upper=5)
df['amarillos_topados'] = df['cant_amarillos'].clip(upper=5)

# --- CREAR SCORE DE RIESGO UNIFICADO (Más peso a rojos) ---
# Esto ayuda a que el modelo separe mejor los grupos
df['riesgo_score'] = df['rojos_topados'] * 3 + df['amarillos_topados'] * 1

# 2. Ingeniería de Características

# A. Datos Numéricos (AUMENTAMOS PESO)
# Ahora usamos el score unificado + los valores individuales
scaler = StandardScaler()
X_colores = df[['riesgo_score', 'rojos_topados', 'amarillos_topados']]
X_colores_scaled = scaler.fit_transform(X_colores)

# B. Datos de Texto (NLP Mejorado)
# LISTA NEGRA: Palabras que NO nos importan para detectar riesgo
mis_stopwords = [
    # Conectores
    'el', 'la', 'de', 'en', 'y', 'a', 'que', 'los', 'se', 'un', 'del', 'con', 'no', 'si', 'por', 'lo', 'su', 'para', 'al', 'es', 'son', 'como', 'pero', 'mas', 'esta', 'este', 'fue', 'ha', 'le',
    # Contexto irrelevante
    'estudiante', 'alumno', 'alumna', 'tutorado', 'tutor', 'tutoria', 'carrera', 'universidad', 'año', 'semestre',
    # Datos Socioeconómicos/Perfil (que se repiten mucho y ensucian)
    'gratuidad', 'beca', 'fondo', 'solidario', 'cae', 'residencia', 'procedencia', 'beneficio', 'arancel',
    # Familia (Información de contexto, no alerta)
    'mama', 'papa', 'madre', 'padre', 'hermano', 'hermana', 'abuela', 'abuelo', 'tio', 'tia', 'vive', 'familia', 'hogar',
    # Rellenos comunes
    'bien', 'mal', 'regular', 'contacto', 'correo', 'telefono', 'whatsapp', 'celular', 'responde', 'contesta',
    # Administrativo (Fechas, trámites, etc.)
    'llega', 'espera', 'fecha', 'interinstitucional', 'traslado', 'dice', 'va', 'tiene', 'esta',
    # Palabras genéricas encontradas
    'primera', 'ninguna', 'opcion', 'taller', 'casa', 'poco', 'depues', 'fundamentos'
]

print("🧠 Analizando texto (buscando PATOLOGÍAS, no rellenos)...")
# ngram_range=(1,2) permite capturar frases de 2 palabras como "ansiedad severa" o "bajo rendimiento"
# min_df=3 significa que una palabra debe aparecer en al menos 3 documentos para ser considerada
tfidf = TfidfVectorizer(
    max_features=80,  # Reducido para darle menos peso al texto
    stop_words=mis_stopwords,
    ngram_range=(1, 2),
    min_df=3  # Filtrar palabras muy raras
)
X_texto = tfidf.fit_transform(df['obs_limpia']).toarray()

# C. Unir Matrices
# REDUCIMOS peso del texto porque el contenido es muy similar entre todos
# AUMENTAMOS peso de los números porque son más discriminativos
X_final = np.concatenate([X_colores_scaled * 2.5, X_texto * 0.5], axis=1)

# 3. Entrenar Modelo con 4 Clusters
print("🤖 Entrenando IA (4 Clusters)...")
kmeans = KMeans(n_clusters=4, random_state=42, n_init=20, max_iter=500)
kmeans.fit(X_final)

df['cluster_id'] = kmeans.labels_

# 4. Interpretación Humana
print("\n--- 🔍 RADIOGRAFÍA DEL CURSO ---")
# Ordenamos por el score ya calculado (rojos * 3 + amarillos)
promedios = df.groupby('cluster_id')['riesgo_score'].mean().sort_values()
mapa_orden = {old_id: new_id for new_id, old_id in enumerate(promedios.index)}
df['grupo_ordenado'] = df['cluster_id'].map(mapa_orden)

nombres_sugeridos = {
    0: "0: Sin Riesgo (Casos sanos)",
    1: "1: Riesgo Bajo",
    2: "2: Riesgo Medio",
    3: "3: Riesgo Alto"
}

for nivel in range(4):
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