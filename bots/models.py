from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Bot(models.Model):
    BOT_TYPES = [
        ('completion', 'Completion'),
        ('chat', 'Chat'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название бота')
    description = models.TextField(blank=True, verbose_name='Описание')
    bot_type = models.CharField(max_length=20, choices=BOT_TYPES, default='chat', verbose_name='Тип бота')
    gpt_model = models.CharField(max_length=50, default='gpt-3.5-turbo', verbose_name='Модель GPT')
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        verbose_name='Температура'
    )
    max_tokens = models.IntegerField(default=1000, verbose_name='Максимальное количество токенов')
    system_prompt = models.TextField(blank=True, verbose_name='Системный промпт')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Создатель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Бот'
        verbose_name_plural = 'Боты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Scenario(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название сценария')
    description = models.TextField(blank=True, verbose_name='Описание')
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='scenarios', verbose_name='Бот')
    initial_step = models.ForeignKey(
        'Step',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initial_scenarios',
        verbose_name='Начальный шаг'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Сценарий'
        verbose_name_plural = 'Сценарии'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.bot.name})"


class Step(models.Model):
    STEP_TYPES = [
        ('message', 'Сообщение'),
        ('question', 'Вопрос'),
        ('condition', 'Условие'),
        ('api_call', 'API вызов'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название шага')
    step_type = models.CharField(max_length=20, choices=STEP_TYPES, default='message', verbose_name='Тип шага')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='steps', verbose_name='Сценарий')
    content = models.JSONField(verbose_name='Содержание шага')
    order = models.IntegerField(default=0, verbose_name='Порядок')
    next_step = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_steps',
        verbose_name='Следующий шаг'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Шаг'
        verbose_name_plural = 'Шаги'
        ordering = ['scenario', 'order']

    def __str__(self):
        return f"{self.name} (Сценарий: {self.scenario.name})"


class BotExecution(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, verbose_name='Бот')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, verbose_name='Сценарий')
    user_session = models.CharField(max_length=100, verbose_name='Сессия пользователя')
    current_step = models.ForeignKey(Step, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Текущий шаг')
    conversation_history = models.JSONField(default=list, verbose_name='История разговора')
    is_completed = models.BooleanField(default=False, verbose_name='Завершено')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Выполнение бота'
        verbose_name_plural = 'Выполнения ботов'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bot.name} - {self.user_session}"