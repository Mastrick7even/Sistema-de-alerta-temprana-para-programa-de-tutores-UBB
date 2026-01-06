from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.

class Alarma(models.Model):
    id_alarma = models.AutoField(primary_key=True)
    descripcion = models.TextField(blank=True, null=True)

    tipo_alarma = models.ForeignKey(
        'TipoAlarma', 
        models.PROTECT,  # No borrar un tipo de alarma si tiene alarmas asociadas
        db_column='id_tipo'
    )

    class Meta:
        db_table = 'alarma'

    def __str__(self):
        # Esto le dice a Django: "Cuando tengas que mostrar una alarma en un menú,
        # muestra el nombre de su TIPO".
        #return self.tipo_alarma.nombre 
        
        # O si prefieres que se vea el tipo Y la descripción corta:
        return f"{self.tipo_alarma.nombre} - {self.descripcion}"


class Asistencia(models.Model):
    id_asistencia = models.AutoField(primary_key=True)
    estado_asistencia = models.CharField(max_length=50)

    tutoria = models.ForeignKey(
        'Tutoria', 
        models.CASCADE,  # Si se borra la tutoría, se borran automáticamente sus asistencias
        db_column='id_tutoria'
    )

    estudiante = models.ForeignKey(
        'Estudiante', 
        models.PROTECT,  # No borrar un estudiante si tiene registros de asistencia asociados
        db_column='id_estudiante'
    )

    class Meta:
        db_table = 'asistencia'
        unique_together = (('tutoria', 'estudiante'),) # Asegura que un estudiante solo tenga un registro de asistencia por tutoría


class Bitacora(models.Model):
    id_bitacora = models.AutoField(primary_key=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    observacion = models.TextField(blank=True, null=True)

    estudiante = models.ForeignKey(
        'Estudiante', 
        models.PROTECT,  # No borrar un estudiante si tiene entradas en la bitácora
        db_column='id_estudiante'
    )

    alarma = models.ForeignKey(
        'Alarma', 
        models.SET_NULL,  # Si la alarma se borra, la referencia en la bitácora queda NULL
        db_column='id_alarma',
        blank=True,
        null=True
    )

    autor = models.ForeignKey(
        'Usuario',
        models.PROTECT,
        db_column='id_autor',
        null=True,
        blank=True,
        related_name='bitacoras_creadas'
    )

    class Meta:
        db_table = 'bitacora'


class Carrera(models.Model):
    id_carrera = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)

    encargado = models.ForeignKey(
        'Usuario',
        models.SET_NULL,  
        null=True,        # para que set null funcione
        blank=True,       # para que el admin de Django permita dejarlo en blanco
        db_column='id_encargado',
        related_name='carreras_a_cargo' 
    )

    class Meta:
        db_table = 'carrera'

    def __str__(self):
        return self.nombre


class ClasificacionTutoria(models.Model):
    id_clasificacion = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'clasificacion_tutoria'
        verbose_name = 'Clasificación de tutoría'
        verbose_name_plural = 'Clasificaciones de tutoría'

    def __str__(self):
        return self.nombre


class Estado(models.Model):
    id_estado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'estado'

    def __str__(self):
        return self.nombre


class Estudiante(models.Model):
    id_estudiante = models.AutoField(primary_key=True)
    rut = models.CharField(unique=True, max_length=12)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True, max_length=255)
    anio_ingreso = models.IntegerField(blank=True, null=True)
    lugar_procedencia = models.CharField(max_length=255, blank=True, null=True)
    grupo_familiar = models.TextField(blank=True, null=True)
    beneficios_sociales = models.TextField(blank=True, null=True)
    
    carrera = models.ForeignKey(
        'Carrera', 
        models.PROTECT, # No borrar una carrera si tiene estudiantes
        db_column='id_carrera'
    )
    tutor_asignado = models.ForeignKey(
        'Usuario', 
        models.SET_NULL, # Si el tutor se borra, el estudiante queda NULL (sin tutor)
        db_column='id_tutor_asignado', 
        blank=True, 
        null=True,
        limit_choices_to={'rol__nombre': 'Tutor'}  # Solo mostrar usuarios con rol "Tutor" en formularios
    )
    estado_actual = models.ForeignKey(
        'Estado', 
        models.PROTECT, # No borrar un estado (ej. 'Riesgo Alto') si un estudiante lo tiene
        db_column='id_estado_actual'
    )
    tipo_desercion = models.ForeignKey(
        'TipoDesercion', 
        models.SET_NULL, # Si la causa de deserción se borra, el estudiante solo pierde la referencia
        db_column='id_tipo_desercion', 
        blank=True, 
        null=True
    )

    class Meta:
        db_table = 'estudiante'

    def clean(self):
        # Validación para asegurar que tutor_asignado (si existe) tenga rol "Tutor"
        if self.tutor_asignado and getattr(self.tutor_asignado, 'rol', None):
            rol_nombre = getattr(self.tutor_asignado.rol, 'nombre', None)
            if rol_nombre != 'Tutor':
                raise ValidationError({'tutor_asignado': 'El usuario asignado debe tener rol "Tutor".'})

    def __str__(self):
        return f"{self.nombre} {self.apellido}" 


class HistorialEstado(models.Model):
    id_historial = models.AutoField(primary_key=True)
    #fecha_asignacion = models.DateTimeField(blank=True, null=True)

    estudiante = models.ForeignKey(
        'Estudiante', 
        models.CASCADE,  # Si el estudiante se borra, borrar su historial de estados
        db_column='id_estudiante'
    )

    estado = models.ForeignKey(
        'Estado', 
        models.PROTECT,  # No borres un estado si está en el historial de algún estudiante
        db_column='id_estado'
    )

    # auto_now_add=True es el equivalente de Django para "DEFAULT CURRENT_TIMESTAMP" (solo se ejecuta al crear).
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_estado'


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'  # <-- ¡Aquí está el truco!

    def __str__(self):
        return self.nombre


class TipoAlarma(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'tipo_alarma'
        verbose_name = 'Tipo de alarma'
        verbose_name_plural = 'Tipos de alarma'


class TipoDesercion(models.Model):
    id_tipo_desercion = models.AutoField(primary_key=True)
    causa = models.CharField(max_length=255)

    class Meta:
        db_table = 'tipo_desercion'
        verbose_name = 'Tipo de deserción'
        verbose_name_plural = 'Tipos de deserción'


class TipoTutoria(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        db_table = 'tipo_tutoria'
        verbose_name = 'Tipo de tutoría'
        verbose_name_plural = 'Tipos de tutoría'

    def __str__(self):
        return self.nombre
        


class Tutoria(models.Model):
    id_tutoria = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(default=timezone.now)
    tema_tutoria = models.TextField(blank=True, null=True)
    lugar = models.CharField(max_length=100)

    tutor = models.ForeignKey(
        'Usuario', 
        models.PROTECT,  # No borres un tutor si tiene tutorías asociadas
        db_column='id_tutor'
    )

    tipo_tutoria = models.ForeignKey(
        'TipoTutoria',
        models.PROTECT,  # No borres un tipo de tutoría si tiene tutorías asociadas
        db_column='id_tipo'
    )

    clasificacion_tutoria = models.ForeignKey(
        'ClasificacionTutoria',
        models.PROTECT,  # No borres una clasificación si tiene tutorías asociadas
        db_column='id_clasificacion'
    )
        

    class Meta:
        db_table = 'tutoria'


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    rut = models.CharField(unique=True, max_length=12)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=255)

    rol = models.ForeignKey(
        'Rol', 
        models.PROTECT,  # No borres un rol si un usuario lo tiene
        db_column='id_rol'
    )

    carrera = models.ForeignKey(
        'Carrera',
        models.SET_NULL,  # Si la carrera se borra, el usuario queda NULL
        db_column='id_carrera',
        blank=True,
        null=True,
        related_name='usuarios_de_carrera'
    )

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rut})"

class Notificacion(models.Model):
    destinatario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_recibidas')
    actor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_enviadas', null=True)
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Opcional: Para saber a qué estudiante se refiere y poder hacer click para ir a verlo
    estudiante_relacionado = models.ForeignKey('Estudiante', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Para {self.destinatario}: {self.mensaje}"