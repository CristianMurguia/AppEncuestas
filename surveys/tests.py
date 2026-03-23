# surveys/tests.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Survey


class AuthTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_login_page_carga(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_carga(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_login_correcto(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_dashboard_requiere_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_con_login(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)


class SurveyTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_crear_encuesta(self):
        response = self.client.post(reverse('survey_create'), {
            'title': 'Encuesta de prueba',
            'description': 'Descripcion de prueba',
            'status': 'draft',
            'requires_login': False,
            'allow_multiple_responses': False,
        })
        self.assertEqual(Survey.objects.count(), 1)

    def test_encuesta_aparece_en_dashboard(self):
        Survey.objects.create(
            owner=self.user,
            title='Encuesta test',
            status='active'
        )
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Encuesta test')

    def test_encuesta_cerrada_no_accesible(self):
        survey = Survey.objects.create(
            owner=self.user,
            title='Encuesta cerrada',
            status='closed'
        )
        self.client.logout()
        response = self.client.get(reverse('survey_take', args=[survey.access_token]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no disponible')