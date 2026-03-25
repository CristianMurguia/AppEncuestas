from django import forms
from django.forms import inlineformset_factory
from .models import Survey, Question, Choice


class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['title', 'description', 'status', 'requires_login',
                  'allow_multiple_responses', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la encuesta',
                'maxlength': '50'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': '500'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'required', 'order', 'help_text']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escribe tu pregunta'}),
            'question_type': forms.Select(
                choices=[
                    ('text', 'Texto libre'),
                    ('checkbox', 'Opción múltiple'),
                ],
                attrs={'class': 'form-select'}
            ),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'help_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto de ayuda opcional'}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


ChoiceFormSet = inlineformset_factory(
    Question, Choice, form=ChoiceForm,
    extra=0, can_delete=True
)


class TakeSurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions')
        super().__init__(*args, **kwargs)
        for question in questions:
            field_name = f'question_{question.pk}'
            if question.question_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=question.text,
                    required=question.required,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                    help_text=question.help_text
                )
            elif question.question_type == 'radio':
                choices = [(c.pk, c.text) for c in question.choices.all()]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    choices=choices,
                    required=question.required,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    help_text=question.help_text
                )
            elif question.question_type == 'checkbox':
                choices = [(c.pk, c.text) for c in question.choices.all()]
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=question.text,
                    choices=choices,
                    required=question.required,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                    help_text=question.help_text
                )
            elif question.question_type == 'select':
                choices = [('', '-- Selecciona --')] + [(c.pk, c.text) for c in question.choices.all()]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    choices=choices,
                    required=question.required,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    help_text=question.help_text
                )
            elif question.question_type == 'rating':
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    choices=[(i, str(i)) for i in range(1, 6)],
                    required=question.required,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input rating-input'}),
                    help_text=question.help_text
                )
            elif question.question_type == 'scale':
                self.fields[field_name] = forms.IntegerField(
                    label=question.text,
                    required=question.required,
                    min_value=1,
                    max_value=10,
                    widget=forms.NumberInput(attrs={'class': 'form-control', 'type': 'range',
                                                    'min': '1', 'max': '10'}),
                    help_text=question.help_text
                )