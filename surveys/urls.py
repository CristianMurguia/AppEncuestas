from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Panel de control
    path('', views.dashboard, name='dashboard'),
    path('encuesta/nueva/', views.survey_create, name='survey_create'),
    path('encuesta/<int:pk>/editar/', views.survey_edit, name='survey_edit'),
    path('encuesta/<int:pk>/eliminar/', views.survey_delete, name='survey_delete'),
    path('encuesta/<int:pk>/resultados/', views.survey_results, name='survey_results'),
    path('encuesta/<int:pk>/exportar/', views.export_responses, name='export_responses'),

    # Preguntas
    path('encuesta/<int:survey_pk>/pregunta/nueva/', views.question_add, name='question_add'),
    path('pregunta/<int:pk>/editar/', views.question_edit, name='question_edit'),
    path('pregunta/<int:pk>/eliminar/', views.question_delete, name='question_delete'),

    # Frontend encuestado
    path('s/<uuid:token>/', views.survey_take, name='survey_take'),
    path('s/<uuid:token>/gracias/', views.survey_thank_you, name='survey_thank_you'),
]