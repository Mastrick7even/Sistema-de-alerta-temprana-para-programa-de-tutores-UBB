import csv
import os
import re
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models.signals import post_save
from sat.models import Usuario, Estudiante, Bitacora, Carrera, Rol, Estado, Notificacion
from sat.services import PredictorRiesgo
# IMPORTANTE: Importamos tu señal para poder apagarla
from sat.signals import notificar_observacion

class Command(BaseCommand):
    help = 'Carga datos históricos limpiando la base de datos si se requiere'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='BORRA TODOS los estudiantes, bitácoras y notificaciones antes de cargar.',
        )

    def handle(self, *args, **options):
        file_path = 'data_analysis/process_data/bitacora_final_ready_for_django_v2.csv'
        
# 1. PURGA DE DATOS (Jerárquica)
        if options['clear']:
            self.stdout.write(self.style.WARNING("⚠️ ATENCIÓN: Purgando base de datos (Respetando jerarquías)..."))
            
            # Importar los modelos dependientes (asegúrate de que estén en tus imports arriba)
            from sat.models import Asistencia, Tutoria, HistorialEstado
            
            # 1. Borrar Notificaciones
            Notificacion.objects.all().delete()
            
            # 2. Borrar HIJOS (Los que tienen ForeignKey PROTECT hacia Estudiante o Tutoria)
            Asistencia.objects.all().delete()
            HistorialEstado.objects.all().delete()
            Bitacora.objects.all().delete()
            
            # 3. Borrar TUTORIAS (Tienen PROTECT hacia Usuario/Tutor)
            Tutoria.objects.all().delete()
            
            # 4. Borrar PADRES (Ahora que no tienen hijos que los bloqueen)
            Estudiante.objects.all().delete()
            
            # 5. Borrar Usuarios DUMMY creados por el script (Los reales no se tocan)
            Usuario.objects.filter(email__startswith='tutor_').delete()
            
            self.stdout.write(self.style.SUCCESS("✅ Base de datos purgada. Lista para carga limpia."))

        # 2. APAGAR SEÑALES (EVITA EL COLAPSO)
        # Desconectamos la señal para que no cree notificaciones por datos históricos
        post_save.disconnect(notificar_observacion, sender=Bitacora)
        self.stdout.write(self.style.WARNING("🔇 Señal 'notificar_observacion' apagada temporalmente."))

        predictor = PredictorRiesgo()

        rol_estudiante, _ = Rol.objects.get_or_create(nombre='Estudiante')
        rol_tutor, _ = Rol.objects.get_or_create(nombre='Tutor')
        
        estado_activo, _ = Estado.objects.get_or_create(nombre='Activo')

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                count = 0
                bitacoras_creadas = 0
                
                for row in reader:
                    try:
                        # --- TUTOR ---
                        nombre_tutor_raw = row['Tutor'].strip().upper()
                        import hashlib
                        tutor_hash = hashlib.md5(nombre_tutor_raw.encode()).hexdigest()[:6]
                        email_tutor = f"tutor_{tutor_hash}@ubiobio.cl"
                        rut_tutor = f"T{tutor_hash.upper()}".ljust(12, '0')[:12]
                        
                        tutor_obj, _ = Usuario.objects.get_or_create(
                            email=email_tutor,
                            defaults={
                                'rut': rut_tutor,
                                'nombre': nombre_tutor_raw.split()[0] if nombre_tutor_raw else 'Tutor',
                                'apellido': ' '.join(nombre_tutor_raw.split()[1:]) if len(nombre_tutor_raw.split()) > 1 else '',
                                'password': 'temp_password',
                                'rol': rol_tutor
                            }
                        )

                        # --- ESTUDIANTE ---
                        rut_limpio = row['rut'].strip()
                        nombre_completo = row['nombre'].strip()
                        carrera_nombre = row['Carrera'].strip()
                        anio = int(row['Anio'])

                        carrera_obj, _ = Carrera.objects.get_or_create(nombre=carrera_nombre)
                        
                        estudiante_obj, _ = Estudiante.objects.get_or_create(
                            rut=rut_limpio,
                            defaults={
                                'nombre': nombre_completo.split()[0] if nombre_completo else 'Sin nombre',
                                'apellido': " ".join(nombre_completo.split()[1:]) if len(nombre_completo.split()) > 1 else '',
                                'carrera': carrera_obj,
                                'estado_actual': estado_activo,
                                'email': row.get('Correo', '').strip() or f"{rut_limpio}@alumnos.ubiobio.cl",
                                'anio_ingreso': anio
                            }
                        )

                        # --- BITÁCORAS ---
                        for col_name, valor in row.items():
                            if not valor: continue
                            
                            es_alerta = "Alerta" in col_name
                            es_obs = "Observaciones" == col_name
                            
                            if (es_alerta or es_obs) and len(valor) > 2:
                                nivel = 1
                                texto_limpio = valor
                                
                                if "[ROJO]" in valor:
                                    nivel = 3
                                    texto_limpio = valor.replace("[ROJO]", "").strip()
                                elif "[AMARILLO]" in valor:
                                    nivel = 2
                                    texto_limpio = valor.replace("[AMARILLO]", "").strip()
                                
                                # Usamos get_or_create para no duplicar si el script falla a la mitad
                                _, created = Bitacora.objects.get_or_create(
                                    estudiante=estudiante_obj,
                                    origen_dato=f"{col_name} ({anio})",
                                    observacion=texto_limpio,
                                    defaults={
                                        'autor': tutor_obj,
                                        'anio_academico': anio,
                                        'nivel_riesgo': nivel,
                                    }
                                )
                                if created: bitacoras_creadas += 1

                        # --- IA ---
                        nuevo_riesgo = predictor.predecir_estudiante(estudiante_obj)
                        estudiante_obj.nivel_riesgo_ia = nuevo_riesgo
                        estudiante_obj.save()

                        count += 1
                        if count % 100 == 0:
                            self.stdout.write(f"Procesados {count} estudiantes... ({bitacoras_creadas} bitácoras)")

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Error en estudiante {row.get('rut', 'Desconocido')}: {e}"))

            self.stdout.write(self.style.SUCCESS(f"✅ FINALIZADO: {count} estudiantes inyectados. {bitacoras_creadas} bitácoras creadas."))

        finally:
            # 3. RECONECTAR SEÑALES (Práctica Obligatoria)
            # Aseguramos que pase lo que pase, el sistema vuelva a la normalidad
            post_save.connect(notificar_observacion, sender=Bitacora)
            self.stdout.write(self.style.SUCCESS("🔊 Señal 'notificar_observacion' reconectada con éxito."))