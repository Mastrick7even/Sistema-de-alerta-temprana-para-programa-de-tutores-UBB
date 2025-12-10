import random
from django.core.management.base import BaseCommand
from faker import Faker
from sat.models import (
    Carrera, Usuario, Rol, Estudiante, Estado, 
    TipoAlarma, TipoDesercion
)

# Configurar Faker para datos chilenos
fake = Faker(['es_CL'])

class Command(BaseCommand):
    help = 'Puebla la base de datos con datos sintéticos coherentes'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando poblado de datos...'))

        # 1. Asegurar Roles y Estados Básicos
        rol_tutor, _ = Rol.objects.get_or_create(nombre='Tutor')
        rol_encargado, _ = Rol.objects.get_or_create(nombre='Encargado de Carrera')
        
        estados = ['Fuera de Riesgo', 'Riesgo Bajo', 'Riesgo Medio', 'Riesgo Alto']
        objs_estados = [Estado.objects.get_or_create(nombre=e)[0] for e in estados]

        # 2. Crear Carreras Ficticias
        nombres_carreras = [
            'Ingeniería Civil Informática', 'Ingeniería Comercial', 
            'Contador Público y Auditor', 'Arquitectura', 'Trabajo Social'
        ]

        for nombre_carrera in nombres_carreras:
            carrera, created = Carrera.objects.get_or_create(nombre=nombre_carrera)
            self.stdout.write(f'--- Procesando carrera: {carrera.nombre}')

            # 3. Crear Encargado de Carrera (1 por carrera)
            encargado = Usuario.objects.create(
                rut=fake.rut(),
                nombre=fake.first_name(),
                apellido=fake.last_name(),
                email=fake.unique.email(),
                password='123', # Password dummy
                rol=rol_encargado,
                carrera=carrera # Asignamos la carrera al encargado
            )
            # Actualizamos la relación inversa
            carrera.encargado = encargado
            carrera.save()

            # 4. Crear Tutores (3 por carrera)
            for _ in range(3):
                tutor = Usuario.objects.create(
                    rut=fake.rut(),
                    nombre=fake.first_name(),
                    apellido=fake.last_name(),
                    email=fake.unique.email(),
                    password='123',
                    rol=rol_tutor,
                    carrera=carrera # El tutor pertenece a esta carrera
                )

                # 5. Crear Estudiantes para este Tutor (5 a 10 por tutor)
                for _ in range(random.randint(5, 10)):
                    estado_random = random.choices(objs_estados, weights=[50, 30, 15, 5], k=1)[0]
                    
                    Estudiante.objects.create(
                        rut=fake.unique.rut(),
                        nombre=fake.first_name(),
                        apellido=fake.last_name(),
                        email=fake.unique.email(),
                        anio_ingreso=random.choice([2023, 2024, 2025]),
                        lugar_procedencia=fake.city(),
                        carrera=carrera,          # Misma carrera del tutor
                        tutor_asignado=tutor,     # Asignado a este tutor
                        estado_actual=estado_random
                    )

        self.stdout.write(self.style.SUCCESS('¡Base de datos poblada exitosamente!'))