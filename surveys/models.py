from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Survey(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('active', 'Activa'),
        ('closed', 'Cerrada'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveys')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    requires_login = models.BooleanField(default=False)
    allow_multiple_responses = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_open(self):
        now = timezone.now()
        if self.status != 'active':
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def total_responses(self):
        return self.responses.count()


class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Texto libre'),
        ('radio', 'Opción única'),
        ('checkbox', 'Opción múltiple'),
        ('select', 'Lista desplegable'),
        ('rating', 'Calificación (1-5)'),
        ('scale', 'Escala (1-10)'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='text')
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    help_text = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.survey.title} - {self.text[:50]}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    respondent_ip = models.GenericIPAddressField(null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Respuesta #{self.pk} - {self.survey.title}"


class Answer(models.Model):
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text_answer = models.TextField(blank=True)
    selected_choices = models.ManyToManyField(Choice, blank=True)

    def __str__(self):
        return f"Respuesta a: {self.question.text[:40]}"