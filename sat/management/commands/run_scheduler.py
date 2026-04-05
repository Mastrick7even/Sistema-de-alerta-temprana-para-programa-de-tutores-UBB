import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.core.management import call_command

logger = logging.getLogger(__name__)

def my_job():
    """Ejecuta el recálculo masivo."""
    try:
        logger.info("⏳ Iniciando tarea programada: recalcular_riesgos_batch...")
        call_command('recalcular_riesgos_batch')
        logger.info("✅ Tarea completada con éxito.")
    except Exception as e:
        logger.error(f"❌ Error al ejecutar tarea programada: {e}")

class Command(BaseCommand):
    help = "Inicia el programador de tareas continuo (APScheduler)."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Programamos para correr todos los días a las 03:00 de la madrugada
        scheduler.add_job(
            my_job,
            trigger=CronTrigger(hour="03", minute="00"),
            id="recalcular_riesgos_diario",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Añadida tarea diaria 'recalcular_riesgos_diario' (03:00 AM).")

        try:
            logger.info("Iniciando el planificador de fondo... [Presiona Ctrl+C para salir]")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Planificador detenido.")
            scheduler.shutdown()
            self.stdout.write(self.style.SUCCESS('Scheduler detenido con éxito.'))
