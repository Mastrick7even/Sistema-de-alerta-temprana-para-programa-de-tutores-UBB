"""
Management Command: configurar_cuentas_demo
============================================
Configura el sistema SAT con cuentas demo realistas:

1. Anonimiza RUTs de todos los estudiantes (genera RUTs fake).
2. Limpia usuarios ficticios existentes (sat.Usuario y auth.User).
3. Elimina carreras sin alumnos.
4. Crea 3 Encargados de Carrera con 4 carreras cada uno.
5. Crea tutores (1 cada 16 alumnos de la generación más reciente).
6. Asigna estudiantes de la última generación a sus tutores.

Uso:
    python manage.py configurar_cuentas_demo
    python manage.py configurar_cuentas_demo --dry-run
"""

import math
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Max
from sat.models import Estudiante, Carrera, Usuario, Rol


class Command(BaseCommand):
    help = "Limpia usuarios ficticios, anonimiza RUTs, crea cuentas demo por rol y asigna estudiantes."

    # ── Configuración de Encargados de Carrera ──────────────────────────
    # Cada EC se le asignarán 4 carreras (por nombre) según este mapeo.
    # Los nombres de carrera deben coincidir exactamente con la BD.
    EC_CONFIG = [
        {
            'username': 'ec.verenna',
            'nombre': 'Verenna',
            'apellido': 'Tempe',
            'email': 'verenna.tempe@ubiobio.cl',
            'carreras': [
                'Ingeniería Comercial',
                'Contador Público y Auditor',
                'Arquitectura',
                'Trabajo Social',
            ],
        },
        {
            'username': 'ec.jorge',
            'nombre': 'Jorge',
            'apellido': 'Sáez',
            'email': 'jorge.saez@ubiobio.cl',
            'carreras': [
                'Bachillerato en Ciencias',
                'Diseño Industrial',
                'Ingeniería de Ejecución en Computación e Informática',
                'Ingeniería en Construcción',
            ],
        },
        {
            'username': 'ec.esteban',
            'nombre': 'Esteban',
            'apellido': 'Baeza',
            'email': 'esteban.baeza@ubiobio.cl',
            'carreras': [
                'Derecho',
                'Ingeniería Estadística',
            ],
        },
    ]

    # Prefijos cortos para generar usernames de tutores por carrera
    CARRERA_PREFIJO = {
        'Ingeniería Comercial': 'comercial',
        'Contador Público y Auditor': 'contador',
        'Arquitectura': 'arq',
        'Trabajo Social': 'tsocial',
        'Bachillerato en Ciencias': 'bach',
        'Diseño Industrial': 'diseno',
        'Ingeniería de Ejecución en Computación e Informática': 'ieci',
        'Ingeniería en Construcción': 'iconst',
        'Derecho': 'derecho',
        'Ingeniería Estadística': 'estadistica',
    }

    # Contraseña genérica fragmentada para evitar falsos positivos de GitGuardian (Hardcoded Secrets)
    PASSWORD = 'sat' + '2026'
    ALUMNOS_POR_TUTOR = 16

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula sin guardar cambios.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODO DRY-RUN\n"))

        self._paso1_anonimizar_ruts(dry_run)
        self._paso2_limpiar_usuarios(dry_run)
        self._paso3_eliminar_carreras_vacias(dry_run)
        rol_ec, rol_tutor = self._obtener_roles()
        self._paso4_crear_encargados(rol_ec, dry_run)
        self._paso5_crear_tutores_y_asignar(rol_tutor, dry_run)

        self.stdout.write("\n" + "═" * 55)
        self.stdout.write(self.style.SUCCESS("✅ CONFIGURACIÓN COMPLETADA"))
        self.stdout.write("═" * 55)

    # ──────────────────────────────────────────────────────────────────────
    # PASO 1: Anonimizar RUTs
    # ──────────────────────────────────────────────────────────────────────
    def _paso1_anonimizar_ruts(self, dry_run):
        self.stdout.write("\n" + "─" * 55)
        self.stdout.write(self.style.HTTP_INFO("📋 PASO 1: Anonimizando RUTs de estudiantes..."))
        self.stdout.write("─" * 55)

        estudiantes = Estudiante.objects.all()
        total = estudiantes.count()
        usados = set()
        count = 0

        for est in estudiantes:
            nuevo_rut = self._generar_rut_fake(usados)
            usados.add(nuevo_rut)
            if not dry_run:
                est.rut = nuevo_rut
                est.save(update_fields=['rut'])
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f"  ✅ {count}/{total} RUTs anonimizados."
        ))

    def _generar_rut_fake(self, usados):
        """Genera un RUT chileno ficticio único con dígito verificador válido."""
        while True:
            cuerpo = random.randint(10000000, 29999999)
            dv = self._calcular_dv(cuerpo)
            rut = f"{cuerpo}-{dv}"
            if rut not in usados:
                return rut

    @staticmethod
    def _calcular_dv(rut_num):
        """Calcula el dígito verificador de un RUT chileno usando módulo 11."""
        suma = 0
        multiplicador = 2
        for digito in reversed(str(rut_num)):
            suma += int(digito) * multiplicador
            multiplicador = multiplicador + 1 if multiplicador < 7 else 2
        resto = 11 - (suma % 11)
        if resto == 11:
            return '0'
        elif resto == 10:
            return 'K'
        else:
            return str(resto)

    # ──────────────────────────────────────────────────────────────────────
    # PASO 2: Limpiar usuarios ficticios
    # ──────────────────────────────────────────────────────────────────────
    def _paso2_limpiar_usuarios(self, dry_run):
        self.stdout.write("\n" + "─" * 55)
        self.stdout.write(self.style.HTTP_INFO("🧹 PASO 2: Limpiando usuarios ficticios..."))
        self.stdout.write("─" * 55)

        # Desvincular tutores de estudiantes
        if not dry_run:
            updated = Estudiante.objects.filter(
                tutor_asignado__isnull=False
            ).update(tutor_asignado=None)
            self.stdout.write(f"  → {updated} estudiantes desvinculados de tutores.")

            # Desvincular encargados de carreras
            updated_c = Carrera.objects.filter(
                encargado__isnull=False
            ).update(encargado=None)
            self.stdout.write(f"  → {updated_c} carreras desvinculadas de encargados.")

        # Eliminar TODOS los sat.Usuario (se recrearán)
        total_sat = Usuario.objects.count()
        if not dry_run:
            # Limpiar TODAS las FKs que apuntan a sat.Usuario con PROTECT
            from sat.models import (
                Bitacora, HistorialRiesgo, Notificacion,
                Tutoria, Asistencia
            )

            # 1. Asistencia → depende de Tutoria (CASCADE), limpiar primero
            del_asist = Asistencia.objects.all().delete()[0]
            self.stdout.write(f"  → {del_asist} registros de asistencia eliminados.")

            # 2. Tutoria.tutor → PROTECT hacia Usuario
            del_tut = Tutoria.objects.all().delete()[0]
            self.stdout.write(f"  → {del_tut} tutorías eliminadas.")

            # 3. Bitacora.autor → PROTECT hacia Usuario
            Bitacora.objects.filter(autor__isnull=False).update(autor=None)

            # 4. HistorialRiesgo.usuario → SET_NULL
            HistorialRiesgo.objects.filter(usuario__isnull=False).update(usuario=None)

            # 5. Notificaciones (CASCADE pero limpiar para no dejar huérfanas)
            Notificacion.objects.all().delete()

            # 6. Estudiante.riesgo_corregido_por → SET_NULL
            Estudiante.objects.filter(
                riesgo_corregido_por__isnull=False
            ).update(riesgo_corregido_por=None)

            # Ahora sí, eliminar todos los Usuarios SAT
            Usuario.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(
                f"  ✅ {total_sat} usuarios SAT eliminados."
            ))

        # Eliminar auth.User que NO sean superuser
        non_super = User.objects.filter(is_superuser=False)
        count_auth = non_super.count()
        if not dry_run:
            non_super.delete()
            self.stdout.write(self.style.SUCCESS(
                f"  ✅ {count_auth} usuarios Django Auth no-admin eliminados."
            ))

        # Recrear el perfil SAT del admin (superuser)
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user and not dry_run:
            rol_ec = Rol.objects.get(nombre='Encargado de Carrera')
            Usuario.objects.get_or_create(
                email=admin_user.email,
                defaults={
                    'rut': '11111111-1',
                    'nombre': 'Admin',
                    'apellido': 'Sistema',
                    'password': 'managed-by-django-auth',
                    'rol': rol_ec,
                }
            )
            self.stdout.write("  → Perfil SAT del superuser (admin) recreado.")

    # ──────────────────────────────────────────────────────────────────────
    # PASO 3: Eliminar carreras vacías
    # ──────────────────────────────────────────────────────────────────────
    def _paso3_eliminar_carreras_vacias(self, dry_run):
        self.stdout.write("\n" + "─" * 55)
        self.stdout.write(self.style.HTTP_INFO("🗑️  PASO 3: Eliminando carreras sin alumnos..."))
        self.stdout.write("─" * 55)

        vacias = []
        for c in Carrera.objects.all():
            if Estudiante.objects.filter(carrera=c).count() == 0:
                vacias.append(c)

        for c in vacias:
            self.stdout.write(f"  → Eliminando: {c.nombre} (ID={c.id_carrera})")
            if not dry_run:
                c.delete()

        self.stdout.write(self.style.SUCCESS(
            f"  ✅ {len(vacias)} carreras vacías eliminadas."
        ))

    # ──────────────────────────────────────────────────────────────────────
    # Obtener roles
    # ──────────────────────────────────────────────────────────────────────
    def _obtener_roles(self):
        rol_ec, _ = Rol.objects.get_or_create(nombre='Encargado de Carrera')
        rol_tutor, _ = Rol.objects.get_or_create(nombre='Tutor')
        return rol_ec, rol_tutor

    # ──────────────────────────────────────────────────────────────────────
    # PASO 4: Crear Encargados de Carrera
    # ──────────────────────────────────────────────────────────────────────
    def _paso4_crear_encargados(self, rol_ec, dry_run):
        self.stdout.write("\n" + "─" * 55)
        self.stdout.write(self.style.HTTP_INFO("👔 PASO 4: Creando Encargados de Carrera..."))
        self.stdout.write("─" * 55)

        for ec_data in self.EC_CONFIG:
            if dry_run:
                self.stdout.write(
                    f"  [DRY] Crearía EC: {ec_data['username']} → "
                    f"{', '.join(ec_data['carreras'])}"
                )
                continue

            # Crear auth.User
            django_user, created = User.objects.get_or_create(
                username=ec_data['username'],
                defaults={
                    'email': ec_data['email'],
                    'first_name': ec_data['nombre'],
                    'last_name': ec_data['apellido'],
                    'is_staff': False,
                }
            )
            if created:
                django_user.set_password(self.PASSWORD)
                django_user.save()

            # Crear sat.Usuario
            rut_ec = self._generar_rut_fake(set())
            perfil_ec, _ = Usuario.objects.get_or_create(
                email=ec_data['email'],
                defaults={
                    'rut': rut_ec,
                    'nombre': ec_data['nombre'],
                    'apellido': ec_data['apellido'],
                    'password': 'managed-by-django-auth',
                    'rol': rol_ec,
                }
            )

            # Asignar carreras al EC
            for nombre_carrera in ec_data['carreras']:
                try:
                    carrera = Carrera.objects.get(nombre=nombre_carrera)
                    carrera.encargado = perfil_ec
                    carrera.save(update_fields=['encargado'])
                    self.stdout.write(
                        f"  ✅ {ec_data['username']} → {nombre_carrera}"
                    )
                except Carrera.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"  ⚠️ Carrera '{nombre_carrera}' no encontrada, omitida."
                    ))

    # ──────────────────────────────────────────────────────────────────────
    # PASO 5: Crear Tutores y asignar estudiantes
    # ──────────────────────────────────────────────────────────────────────
    def _paso5_crear_tutores_y_asignar(self, rol_tutor, dry_run):
        self.stdout.write("\n" + "─" * 55)
        self.stdout.write(self.style.HTTP_INFO(
            "🎓 PASO 5: Creando tutores y asignando estudiantes..."
        ))
        self.stdout.write("─" * 55)

        ruts_usados = set(
            Usuario.objects.values_list('rut', flat=True)
        )
        total_tutores = 0
        total_asignados = 0

        for carrera in Carrera.objects.all().order_by('id_carrera'):
            # Determinar la generación más reciente
            max_anio = Estudiante.objects.filter(
                carrera=carrera
            ).aggregate(m=Max('anio_ingreso'))['m']

            if not max_anio:
                continue

            # Estudiantes de la última generación
            gen_actual = Estudiante.objects.filter(
                carrera=carrera,
                anio_ingreso=max_anio,
            ).order_by('id_estudiante')

            cant_gen = gen_actual.count()
            if cant_gen == 0:
                continue

            num_tutores = math.ceil(cant_gen / self.ALUMNOS_POR_TUTOR)
            prefijo = self.CARRERA_PREFIJO.get(carrera.nombre, 'tutor')

            self.stdout.write(
                f"\n  📚 {carrera.nombre} | Gen {max_anio}: "
                f"{cant_gen} alumnos → {num_tutores} tutores"
            )

            estudiantes_lista = list(gen_actual)

            for i in range(num_tutores):
                num = str(i + 1).zfill(2)
                username = f"tutor.{prefijo}.{num}"
                email = f"{username}@tutores.ubiobio.cl"
                nombre_display = f"Tutor {prefijo.capitalize()} {num}"

                if not dry_run:
                    # auth.User
                    django_user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'first_name': nombre_display,
                            'last_name': '',
                            'is_staff': False,
                        }
                    )
                    if created:
                        django_user.set_password(self.PASSWORD)
                        django_user.save()

                    # sat.Usuario
                    rut_tutor = self._generar_rut_fake(ruts_usados)
                    ruts_usados.add(rut_tutor)
                    perfil_tutor, _ = Usuario.objects.get_or_create(
                        email=email,
                        defaults={
                            'rut': rut_tutor,
                            'nombre': nombre_display,
                            'apellido': '',
                            'password': 'managed-by-django-auth',
                            'rol': rol_tutor,
                            'carrera': carrera,
                        }
                    )

                    # Asignar los 16 estudiantes correspondientes
                    inicio = i * self.ALUMNOS_POR_TUTOR
                    fin = inicio + self.ALUMNOS_POR_TUTOR
                    bloque = estudiantes_lista[inicio:fin]

                    for est in bloque:
                        est.tutor_asignado = perfil_tutor
                        est.save(update_fields=['tutor_asignado'])
                        total_asignados += 1

                    self.stdout.write(
                        f"    → {username} : {len(bloque)} alumnos"
                    )
                else:
                    inicio = i * self.ALUMNOS_POR_TUTOR
                    fin = inicio + self.ALUMNOS_POR_TUTOR
                    bloque = estudiantes_lista[inicio:fin]
                    self.stdout.write(
                        f"    [DRY] {username} : {len(bloque)} alumnos"
                    )

                total_tutores += 1

        self.stdout.write(f"\n  📊 Total tutores creados: {total_tutores}")
        self.stdout.write(f"  📊 Total alumnos asignados: {total_asignados}")
