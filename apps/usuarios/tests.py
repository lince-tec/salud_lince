from django.test import TestCase
from apps.usuarios.models import Usuario, HistorialMedico, Role


class UsuarioTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = Usuario.objects.create_user(
            clave="ISC221733",
            email="isc221733@itsatlixco.edu.mx",
            nombres="JOHN",
            apellido_paterno="DOE",
            fecha_nacimiento="1990-01-01",
            carrera_o_puesto="ING. SISTEMAS COMP.",
            password="P@ssword123",
            role="paciente",
        )

        cls.user2 = Usuario.objects.create_user(
            clave="ISC221734",
            email="isc221734@itsatlixco.edu.mx",
            nombres="JOHN",
            apellido_paterno="DOE",
            fecha_nacimiento="1990-01-01",
            carrera_o_puesto="ING. SISTEMAS COMP.",
            password="P@ssword123",
            role="medico",
        )

    def test_user_exists(self):
        usuario = Usuario.objects.get(email="isc221733@itsatlixco.edu.mx")
        self.assertEqual(self.user, usuario)

    def test_user_role(self):
        usuario = Usuario.objects.get(email="isc221733@itsatlixco.edu.mx")
        self.assertEqual("paciente", usuario.role.nombre_rol)

    def test_user2_exists(self):
        usuario = Usuario.objects.get(email="isc221734@itsatlixco.edu.mx")
        self.assertEqual(self.user2, usuario)

    def test_user2_role(self):
        usuario2 = Usuario.objects.get(email="isc221734@itsatlixco.edu.mx")
        self.assertEqual("medico", usuario2.role.nombre_rol)


class HistorialMedicoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.paciente_role = Role.objects.get_or_create(nombre_rol="paciente")
        cls.user = Usuario.objects.create_user(
            clave="ISC221744",
            email="isc221744@itsatlixco.edu.mx",
            nombres="JOHN",
            apellido_paterno="DOE",
            fecha_nacimiento="1990-01-01",
            carrera_o_puesto="ING. SISTEMAS COMP.",
            password="P@ssword123",
        )
        # Primero verificamos si ya existe un historial para ese paciente.
        cls.historial_medico, created = HistorialMedico.objects.get_or_create(
            paciente=cls.user,
            defaults={
                "id_historial": cls.user.clave,
                "enfermedades_cronicas": "prueba",
                "alergias": "prueba",
                "medicamento_usado": "prueba",
                "es_embarazada": True,
                "usa_drogas": True,
                "usa_cigarro": True,
                "ingiere_alcohol": True,
                "usa_lentes": True,
                "vida_sexual_activa": True,
                "usa_metodos_anticonceptivos": True,
            },
        )

    def test_historial_medico_exists(self):
        # Verificamos que el historial médico existe
        historial_medico = HistorialMedico.objects.get(paciente=self.user)
        self.assertEqual(self.historial_medico, historial_medico)
        self.assertEqual(self.historial_medico.id_historial, self.user.clave)

    def test_user_role(self):
        usuario = Usuario.objects.get(email="isc221744@itsatlixco.edu.mx")
        self.assertEqual("paciente", usuario.role.nombre_rol)
