from django.contrib import admin
from .models import Bot, Scenario, Step, BotExecution


class StepInline(admin.TabularInline):
    model = Step
    extra = 1
    fields = ['name', 'step_type', 'order', 'next_step']


class ScenarioInline(admin.TabularInline):
    model = Scenario
    extra = 1
    fields = ['name', 'is_active', 'initial_step']


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ['name', 'bot_type', 'gpt_model', 'is_active', 'created_by', 'created_at']
    list_filter = ['bot_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ScenarioInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Настройки GPT', {
            'fields': ('bot_type', 'gpt_model', 'temperature', 'max_tokens', 'system_prompt')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'bot', 'is_active', 'created_at']
    list_filter = ['is_active', 'bot', 'created_at']
    search_fields = ['name', 'description']
    inlines = [StepInline]
    filter_horizontal = []
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ['name', 'step_type', 'scenario', 'order', 'created_at']
    list_filter = ['step_type', 'scenario', 'created_at']
    search_fields = ['name', 'content']
    readonly_fields = ['created_at']


@admin.register(BotExecution)
class BotExecutionAdmin(admin.ModelAdmin):
    list_display = ['bot', 'user_session', 'current_step', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'bot', 'created_at']
    search_fields = ['user_session', 'bot__name']
    readonly_fields = ['created_at', 'updated_at']