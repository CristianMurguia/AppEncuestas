from django.contrib import admin
from .models import Survey, Question, Choice, SurveyResponse, Answer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'status', 'total_responses', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'owner__username']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'survey', 'question_type', 'required', 'order']
    inlines = [ChoiceInline]


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['pk', 'survey', 'respondent', 'submitted_at', 'is_complete']
    list_filter = ['is_complete', 'submitted_at']