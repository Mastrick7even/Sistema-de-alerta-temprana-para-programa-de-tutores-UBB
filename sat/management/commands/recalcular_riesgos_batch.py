"""
Management Command: recalcular_riesgos_batch
============================================
Diseñado para ejecutarse en las madrugadas vía crontab.

Ejemplo de crontab (3 AM todos los días):
    0 3 * * * /ruta/venv/bin/python /ruta/manage.py recalcular_riesgos_batch

Lógica:
  1. Filtra estudiantes donde riesgo_sobrescrito=False (respeta decisiones manuales).
  2. Instancia PredictorRiesgo() UNA SOLA VEZ fuera del loop (eficiente).
  3. Calcula el nuevo riesgo y actualiza si cambió.
  4. La señal pre_save de Estudiante registra automáticamente el HistorialRiesgo.
"""

from django.core.management.base import BaseCommand
from sat.models import Estudiante
from sat.services import PredictorRiesgo


class Command(BaseCommand):
    help = (
        "Recalcula el riesgo_ia de todos los estudiantes activos que "
        "no tienen riesgo_sobrescrito=True. Pensado para correr en crontab nocturno."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la ejecución sin guardar cambios en la base de datos.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODO DRY-RUN: no se guardarán cambios.\n"))

        # ── Contadores para el resumen final ──────────────────────────────
        total = 0
        actualizados = 0
        sin_cambio = 0
        errores = 0
        omitidos_sobrescritos = 0

        # ── Cargar el predictor UNA SOLA VEZ (evita recargar el modelo en cada iter) ──
        try:
            predictor = PredictorRiesgo()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ No se pudo cargar el modelo IA: {e}"))
            return

        if not predictor.cerebro:
            self.stderr.write(self.style.ERROR(
                "❌ El modelo IA no está disponible. Verifica la ruta del archivo .pkl."
            ))
            return

        # ── Contar estudiantes omitidos (para el resumen) ─────────────────
        omitidos_sobrescritos = Estudiante.objects.filter(riesgo_sobrescrito=True).count()

        # ── Filtrar solo estudiantes sin sobrescritura manual ─────────────
        estudiantes_qs = Estudiante.objects.filter(
            riesgo_sobrescrito=False
        ).select_related('carrera')  # Optimiza queries si el predictor consulta carrera

        total = estudiantes_qs.count()
        self.stdout.write(
            f"🚀 Iniciando recálculo para {total} estudiantes "
            f"({omitidos_sobrescritos} omitidos por sobrescritura manual)...\n"
        )

        # ── Loop principal ────────────────────────────────────────────────
        for estudiante in estudiantes_qs.iterator():
            try:
                nuevo_riesgo = predictor.predecir_estudiante(estudiante)

                if nuevo_riesgo != estudiante.nivel_riesgo_ia:
                    if not dry_run:
                        estudiante.nivel_riesgo_ia = nuevo_riesgo
                        # update_fields dispara la señal pre_save → crea HistorialRiesgo automáticamente
                        estudiante.save(update_fields=['nivel_riesgo_ia'])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✅ {estudiante.rut} | "
                            f"{estudiante.nivel_riesgo_ia} → {nuevo_riesgo}"
                            + (" [DRY-RUN]" if dry_run else "")
                        )
                    )
                    actualizados += 1
                else:
                    sin_cambio += 1

            except Exception as e:
                errores += 1
                self.stderr.write(
                    self.style.ERROR(f"  ❌ Error en {getattr(estudiante, 'rut', '?')}: {e}")
                )

        # ── Resumen final ─────────────────────────────────────────────────
        self.stdout.write("\n" + "─" * 50)
        self.stdout.write(self.style.SUCCESS("📊 RESUMEN DEL BATCH:"))
        self.stdout.write(f"   Total procesados       : {total}")
        self.stdout.write(self.style.SUCCESS(f"   Actualizados           : {actualizados}"))
        self.stdout.write(f"   Sin cambio             : {sin_cambio}")
        self.stdout.write(self.style.WARNING(f"   Omitidos (manual)      : {omitidos_sobrescritos}"))
        if errores:
            self.stdout.write(self.style.ERROR(f"   Errores                : {errores}"))
        self.stdout.write("─" * 50 + "\n")

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY-RUN completado. No se modificó la BD."))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Batch completado exitosamente."))
