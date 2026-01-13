from django.test import TestCase

from apps.usuarios.models import Usuario

from .models import Consulta, SignosVitales, CategoriaPadecimiento


class ConsultaTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.paciente = Usuario.objects.create_user(
            clave="ISC221733",
            email="isc221733@itsatlixco.edu.mx",
            nombres="JOHN",
            apellido_paterno="DOE",
            fecha_nacimiento="1990-01-01",
            carrera_o_puesto="ING. SISTEMAS COMP.",
            password="P@ssword123",
            role="paciente",
        )
        cls.medico = Usuario.objects.create_user(
            clave="ISC221734",
            email="isc221734@itsatlixco.edu.mx",
            nombres="JOHN",
            apellido_paterno="DOE",
            fecha_nacimiento="1990-01-01",
            carrera_o_puesto="Médico",
            password="P@ssword123",
            role="medico",
        )
        cls.categoria = CategoriaPadecimiento.objects.get_or_create(
            padecimiento="IRAS"
        )[0]
        cls.consulta = Consulta.objects.create(
            fecha="2023-01-01",
            padecimiento_actual="Padecimiento actual",
            tratamiento_no_farmacologico="Tratamiento no farmacológico",
            tratamiento_farmacologico_recetado="Tratamiento farmacológico recetado",
            categoria_de_padecimiento=cls.categoria,
            clave_paciente=cls.paciente,
            clave_medico=cls.medico,
        )
        cls.signos_vitales = SignosVitales.objects.create(
            consulta=cls.consulta,
            peso=80,
            talla=1.80,
            temperatura=37.5,
            frecuencia_cardiaca=60,
            frecuencia_respiratoria=12,
            presion_arterial="120/80",
        )

    def test_consulta_exists(self):
        consulta = Consulta.objects.get(id_consulta=self.consulta.id_consulta)
        self.assertEqual(consulta, self.consulta)

    def test_signos_vitales_exists(self):
        signos_vitales = SignosVitales.objects.get(
            id_signos=self.signos_vitales.id_signos
        )
        self.assertEqual(signos_vitales, self.signos_vitales)

