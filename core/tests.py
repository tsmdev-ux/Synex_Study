from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .forms import SignupForm
from .models import Tarefa, Perfil


class SignupFormTests(TestCase):
    def test_terms_required(self):
        form = SignupForm(data={
            "username": "tiago",
            "email": "tiago@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("terms_accepted", form.errors)

    def test_email_unique(self):
        User.objects.create_user(username="u1", email="dup@example.com", password="StrongPass123!")
        form = SignupForm(data={
            "username": "u2",
            "email": "dup@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "terms_accepted": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class KanbanLimitsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", email="user@example.com", password="StrongPass123!")
        Perfil.objects.get_or_create(usuario=self.user)

    def test_free_plan_limit(self):
        self.client.login(username="user", password="StrongPass123!")
        url = reverse("kanban")
        for i in range(3):
            resp = self.client.post(url, data={"titulo": f"Tarefa {i}", "prioridade": "M"})
            self.assertEqual(resp.status_code, 302)
        self.assertEqual(Tarefa.objects.filter(usuario=self.user).count(), 3)

        resp = self.client.post(url, data={"titulo": "Tarefa extra", "prioridade": "M"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Tarefa.objects.filter(usuario=self.user).count(), 3)
