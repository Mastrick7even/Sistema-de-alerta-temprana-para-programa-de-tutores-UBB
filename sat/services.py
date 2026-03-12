import joblib
import os
import numpy as np
import re
import pandas as pd
from django.conf import settings
from .models import Estudiante, Bitacora

class PredictorRiesgo:
    def __init__(self):
        # Ruta dinámica y a prueba de balas
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.model_path = os.path.join(project_root,'Sistema-de-alerta-temprana-para-programa-de-tutores-UBB', 'sat', 'ml_models', 'modelo_sat.pkl')
        self.cerebro = None
        self.cargar_modelo()

    def cargar_modelo(self):
        try:
            if os.path.exists(self.model_path):
                self.cerebro = joblib.load(self.model_path)
                print("🧠 Modelo IA cargado exitosamente.")
            else:
                print(f"⚠️ ADVERTENCIA: No se encontró el modelo en {self.model_path}")
        except Exception as e:
            print(f"❌ Error cargando modelo IA: {e}")

    def limpiar_texto(self, texto):
        if not isinstance(texto, str): return ""
        txt = str(texto).lower()
        txt = txt.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        txt = re.sub(r'\d+', '', txt)
        txt = re.sub(r'[^\w\s]', '', txt)
        return txt

    def predecir_estudiante(self, estudiante_obj):
        if not self.cerebro: 
            return 0 
        
        bitacoras = estudiante_obj.bitacora_set.all() 
        
        # EL GHOSTING: Si no hay bitácoras, es un fantasma. Riesgo -1 (Alerta de Inactividad)
        if not bitacoras.exists():
            return -1

        cant_rojos = 0
        cant_amarillos = 0
        textos = []

        for b in bitacoras:
            if b.nivel_riesgo == 3: cant_rojos += 1
            elif b.nivel_riesgo == 2: cant_amarillos += 1
            if b.observacion: textos.append(b.observacion)
        
        obs_limpia = self.limpiar_texto(" ".join(textos))

        # CLIPPING
        rojos_input = min(cant_rojos, 5)     
        amarillos_input = min(cant_amarillos, 5) 
        
        # EL TERCER DATO
        riesgo_score = (rojos_input * 3) + (amarillos_input * 1)

        try:
            # 1. Escalar numéricos (EL ORDEN EXACTO EXIGIDO POR LA IA)
            X_colores_df = pd.DataFrame(
                [[riesgo_score, rojos_input, amarillos_input]], 
                columns=['riesgo_score', 'rojos_topados', 'amarillos_topados']
            )
            X_colores = self.cerebro['scaler'].transform(X_colores_df)
            
            # 2. Vectorizar texto
            X_texto = self.cerebro['tfidf'].transform([obs_limpia]).toarray()

            # 3. Concatenar (Asegúrate de usar los pesos correctos de tu entrenamiento)
            X_final = np.concatenate([X_colores * 2.5, X_texto * 0.5], axis=1)

            # 4. Predecir
            cluster_id = self.cerebro['model'].predict(X_final)[0]
            riesgo_real = self.cerebro['mapa_orden'][cluster_id]
            
            return riesgo_real

        except Exception as e:
            print(f"Error en predicción para {estudiante_obj.rut}: {e}")
            return -1 # Fantasma o Error