from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Count, Avg, Q
from django.utils import timezone
from collections import Counter
import json

from .models import Survey, Question, Choice, SurveyResponse, Answer
from .forms import SurveyForm, QuestionForm, ChoiceFormSet, TakeSurveyForm


# ──────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'surveys/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'surveys/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ──────────────────────────────────────────────
# DASHBOARD / PANEL DE CONTROL
# ──────────────────────────────────────────────

@login_required
def dashboard(request):
    surveys = Survey.objects.filter(owner=request.user).annotate(
        response_count=Count('responses')
    )
    stats = {
        'total': surveys.count(),
        'active': surveys.filter(status='active').count(),
        'draft': surveys.filter(status='draft').count(),
        'total_responses': SurveyResponse.objects.filter(survey__owner=request.user).count(),
    }
    return render(request, 'surveys/dashboard.html', {'surveys': surveys, 'stats': stats})


# ──────────────────────────────────────────────
# CONSTRUCTOR DE ENCUESTAS
# ──────────────────────────────────────────────

@login_required
def survey_create(request):
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.owner = request.user
            survey.save()
            messages.success(request, 'Encuesta creada. Ahora agrega preguntas.')
            return redirect('survey_edit', pk=survey.pk)
    else:
        form = SurveyForm()
    return render(request, 'surveys/survey_create.html', {'form': form})


@login_required
def survey_edit(request, pk):
    survey = get_object_or_404(Survey, pk=pk, owner=request.user)
    questions = survey.questions.prefetch_related('choices').all()
    form = SurveyForm(instance=survey)

    if request.method == 'POST':
        form = SurveyForm(request.POST, instance=survey)
        if form.is_valid():
            form.save()
            messages.success(request, 'Encuesta actualizada.')
            return redirect('survey_edit', pk=pk)

    return render(request, 'surveys/survey_edit.html', {
        'survey': survey, 'questions': questions, 'form': form
    })


@login_required
def question_add(request, survey_pk):
    survey = get_object_or_404(Survey, pk=survey_pk, owner=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.survey = survey
            question.save()
            formset = ChoiceFormSet(request.POST, instance=question)
            if formset.is_valid():
                formset.save()
            messages.success(request, 'Pregunta agregada.')
            return redirect('survey_edit', pk=survey_pk)
    else:
        form = QuestionForm()
        formset = ChoiceFormSet()
    return render(request, 'surveys/question_form.html', {
        'form': form, 'formset': formset, 'survey': survey, 'action': 'Agregar'
    })


@login_required
def question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk, survey__owner=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Pregunta actualizada.')
            return redirect('survey_edit', pk=question.survey.pk)
    else:
        form = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)
    return render(request, 'surveys/question_form.html', {
        'form': form, 'formset': formset, 'survey': question.survey, 'action': 'Editar'
    })


@login_required
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk, survey__owner=request.user)
    survey_pk = question.survey.pk
    question.delete()
    messages.success(request, 'Pregunta eliminada.')
    return redirect('survey_edit', pk=survey_pk)


@login_required
def survey_delete(request, pk):
    survey = get_object_or_404(Survey, pk=pk, owner=request.user)
    if request.method == 'POST':
        survey.delete()
        messages.success(request, 'Encuesta eliminada.')
        return redirect('dashboard')
    return render(request, 'surveys/survey_confirm_delete.html', {'survey': survey})


# ──────────────────────────────────────────────
# EXPERIENCIA DEL ENCUESTADO
# ──────────────────────────────────────────────

def survey_take(request, token):
    survey = get_object_or_404(Survey, access_token=token)

    if not survey.is_open():
        return render(request, 'surveys/survey_closed.html', {'survey': survey})

    if survey.requires_login and not request.user.is_authenticated:
        messages.warning(request, 'Esta encuesta requiere que inicies sesión.')
        return redirect('login')

    # Control de respuestas múltiples
    if not survey.allow_multiple_responses:
        if request.user.is_authenticated:
            already = SurveyResponse.objects.filter(
                survey=survey, respondent=request.user, is_complete=True
            ).exists()
        else:
            already = SurveyResponse.objects.filter(
                survey=survey, session_key=request.session.session_key or '', is_complete=True
            ).exists()
        if already:
            return render(request, 'surveys/already_responded.html', {'survey': survey})

    questions = survey.questions.prefetch_related('choices').all()

    if request.method == 'POST':
        form = TakeSurveyForm(request.POST, questions=questions)
        if form.is_valid():
            if not request.session.session_key:
                request.session.create()

            ip = request.META.get('REMOTE_ADDR')
            survey_response = SurveyResponse.objects.create(
                survey=survey,
                respondent=request.user if request.user.is_authenticated else None,
                respondent_ip=ip,
                session_key=request.session.session_key,
                is_complete=True
            )

            for question in questions:
                field_name = f'question_{question.pk}'
                value = form.cleaned_data.get(field_name)
                answer = Answer.objects.create(
                    response=survey_response,
                    question=question
                )
                if question.question_type in ('radio', 'select', 'rating'):
                    try:
                        choice = Choice.objects.get(pk=int(value))
                        answer.selected_choices.add(choice)
                    except (Choice.DoesNotExist, ValueError, TypeError):
                        answer.text_answer = str(value) if value else ''
                        answer.save()
                elif question.question_type == 'checkbox':
                    if value:
                        for cid in value:
                            try:
                                choice = Choice.objects.get(pk=int(cid))
                                answer.selected_choices.add(choice)
                            except (Choice.DoesNotExist, ValueError):
                                pass
                else:
                    answer.text_answer = str(value) if value else ''
                    answer.save()

            messages.success(request, '¡Gracias por completar la encuesta!')
            return redirect('survey_thank_you', token=token)
    else:
        form = TakeSurveyForm(questions=questions)

    return render(request, 'surveys/survey_take.html', {
        'survey': survey, 'form': form, 'questions': questions
    })


def survey_thank_you(request, token):
    survey = get_object_or_404(Survey, access_token=token)
    return render(request, 'surveys/thank_you.html', {'survey': survey})


# ──────────────────────────────────────────────
# ANÁLISIS Y REPORTES
# ──────────────────────────────────────────────

@login_required
def survey_results(request, pk):
    survey = get_object_or_404(Survey, pk=pk, owner=request.user)
    questions = survey.questions.prefetch_related('choices', 'answers__selected_choices').all()
    total_responses = survey.responses.filter(is_complete=True).count()

    analysis = []
    for question in questions:
        q_data = {
            'question': question,
            'total_answers': question.answers.count(),
            'chart_data': None,
            'text_answers': [],
        }
        if question.question_type in ('radio', 'checkbox', 'select', 'rating'):
            choice_counts = {}
            for choice in question.choices.all():
                count = choice.answer_set.filter(response__survey=survey).count()
                choice_counts[choice.text] = count
            q_data['chart_data'] = json.dumps({
                'labels': list(choice_counts.keys()),
                'data': list(choice_counts.values()),
            })
        elif question.question_type == 'scale':
            text_vals = [
                a.text_answer for a in question.answers.all() if a.text_answer.isdigit()
            ]
            if text_vals:
                avg = sum(int(v) for v in text_vals) / len(text_vals)
                q_data['average'] = round(avg, 2)
                counter = Counter(text_vals)
                q_data['chart_data'] = json.dumps({
                    'labels': [str(i) for i in range(1, 11)],
                    'data': [counter.get(str(i), 0) for i in range(1, 11)],
                })
        else:
            q_data['text_answers'] = [
                a.text_answer for a in question.answers.all() if a.text_answer
            ]
        analysis.append(q_data)

    responses_by_day = (
        survey.responses.filter(is_complete=True)
        .extra(select={'day': 'date(submitted_at)'})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    return render(request, 'surveys/survey_results.html', {
        'survey': survey,
        'total_responses': total_responses,
        'analysis': analysis,
        'responses_by_day': json.dumps(list(responses_by_day), default=str),
    })


@login_required
def export_responses(request, pk):
    import csv
    from django.http import HttpResponse

    survey = get_object_or_404(Survey, pk=pk, owner=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="encuesta_{survey.pk}.csv"'

    writer = csv.writer(response)
    questions = list(survey.questions.all())
    header = ['ID Respuesta', 'Fecha', 'IP'] + [q.text for q in questions]
    writer.writerow(header)

    for resp in survey.responses.filter(is_complete=True).prefetch_related('answers__selected_choices'):
        row = [resp.pk, resp.submitted_at.strftime('%Y-%m-%d %H:%M'), resp.respondent_ip or '']
        answers_map = {a.question_id: a for a in resp.answers.all()}
        for q in questions:
            answer = answers_map.get(q.pk)
            if answer:
                if answer.selected_choices.exists():
                    row.append(', '.join(c.text for c in answer.selected_choices.all()))
                else:
                    row.append(answer.text_answer)
            else:
                row.append('')
        writer.writerow(row)

    return response