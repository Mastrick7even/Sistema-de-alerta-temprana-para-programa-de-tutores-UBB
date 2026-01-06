"""
Script para crear usuarios SAT que correspondan a los usuarios de Django Auth.
Ejecutar con: python manage.py shell < crear_usuarios_sat.py
"""

from sat.models import Usuario, Rol

# 1. Crear o obtener los roles necesarios
rol_tutor, _ = Rol.objects.get_or_create(nombre='Tutor')
rol_encargado, _ = Rol.objects.get_or_create(nombre='Encargado de Carrera')

# 2. Crear usuario SAT para 'admin' (como Encargado)
admin_sat, created = Usuario.objects.get_or_create(
    email='admin@ubb.cl',
    defaults={
        'rut': '11111111-1',
        'nombre': 'Admin',
        'apellido': 'Sistema',
        'password': 'dummy',  # No se usa, la auth es por Django
        'rol': rol_encargado,
        'carrera': None
    }
)
if created:
    print(f"✅ Creado usuario SAT para admin: {admin_sat}")
else:
    print(f"ℹ️  Usuario SAT para admin ya existe: {admin_sat}")

# 3. Crear usuario SAT para 'tutorbastian' (como Tutor)
tutor_sat, created = Usuario.objects.get_or_create(
    email='bastian.arriagada2201@alumnos.ubiobio.cl',
    defaults={
        'rut': '22222222-2',
        'nombre': 'Bastian',
        'apellido': 'Arriagada',
        'password': 'dummy',
        'rol': rol_tutor,
        'carrera': None
    }
)
if created:
    print(f"✅ Creado usuario SAT para tutorbastian: {tutor_sat}")
else:
    print(f"ℹ️  Usuario SAT para tutorbastian ya existe: {tutor_sat}")

print("\n✅ Proceso completado!")
print("Ahora recarga el servidor y vuelve a intentar.")

