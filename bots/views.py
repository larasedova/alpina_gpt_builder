# bots/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Bot, Scenario, Step, BotExecution
from .serializers import (
    BotSerializer, ScenarioSerializer, StepSerializer,
    BotExecutionSerializer, ChatSerializer
)
from .services import generate_gpt_response, validate_gpt_config, test_gpt_connection


class BotViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления ботами
    """
    queryset = Bot.objects.all().order_by('-created_at')
    serializer_class = BotSerializer

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Тестирование подключения бота (заглушка)
        """
        bot = self.get_object()

        # В демо-режиме всегда возвращаем успех
        result = test_gpt_connection()

        return Response(result)

    @action(detail=True, methods=['post'])
    def validate_config(self, request, pk=None):
        """
        Валидация конфигурации бота (заглушка)
        """
        bot = self.get_object()

        bot_config = {
            "gpt_model": bot.gpt_model,
            "temperature": bot.temperature,
            "max_tokens": bot.max_tokens,
            "system_prompt": bot.system_prompt,
            "bot_type": bot.bot_type
        }

        result = validate_gpt_config(bot_config)
        return Response(result)

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """
        Чат с ботом (использует заглушку вместо реального GPT)
        """
        bot = self.get_object()

        # Валидируем входные данные
        serializer = ChatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data['message']
        user_session = serializer.validated_data.get('user_session', 'default_session')
        scenario_id = serializer.validated_data.get('scenario_id')

        # Подготавливаем конфигурацию бота
        bot_config = {
            "gpt_model": bot.gpt_model,
            "temperature": bot.temperature,
            "max_tokens": bot.max_tokens,
            "system_prompt": bot.system_prompt,
            "bot_type": bot.bot_type
        }

        # Подготавливаем историю сообщений
        messages = [{"role": "user", "content": message}]

        # Получаем ответ от ЗАГЛУШКИ
        try:
            bot_response = generate_gpt_response(messages, bot_config)

            # Сохраняем выполнение
            execution = BotExecution.objects.create(
                bot=bot,
                user_session=user_session,
                current_step=None,
                conversation_history=f"Пользователь: {message}\nБот: {bot_response}",
                is_completed=False
            )

            # Если указан сценарий, связываем с выполнением
            if scenario_id:
                try:
                    scenario = Scenario.objects.get(id=scenario_id, bot=bot)
                    execution.scenario = scenario
                    execution.save()
                except Scenario.DoesNotExist:
                    pass

            return Response({
                'success': True,
                'response': bot_response,
                'execution_id': execution.id,
                'bot_name': bot.name,
                'demo_mode': True  # Указываем, что работает в демо-режиме
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': f'Ошибка при генерации ответа: {str(e)}',
                'demo_mode': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScenarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления сценариями
    """
    queryset = Scenario.objects.all().order_by('-created_at')
    serializer_class = ScenarioSerializer

    def get_queryset(self):
        """
        Опционально фильтруем сценарии по bot_id
        """
        queryset = Scenario.objects.all()
        bot_id = self.request.query_params.get('bot_id')
        if bot_id is not None:
            queryset = queryset.filter(bot_id=bot_id)
        return queryset

    @action(detail=True, methods=['get'])
    def steps(self, request, pk=None):
        """
        Получение шагов сценария
        """
        scenario = self.get_object()
        steps = scenario.steps.all().order_by('order')
        serializer = StepSerializer(steps, many=True)
        return Response(serializer.data)


class StepViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления шагами сценариев
    """
    queryset = Step.objects.all().order_by('scenario', 'order')
    serializer_class = StepSerializer

    def get_queryset(self):
        """
        Опционально фильтруем шаги по scenario_id
        """
        queryset = Step.objects.all()
        scenario_id = self.request.query_params.get('scenario_id')
        if scenario_id is not None:
            queryset = queryset.filter(scenario_id=scenario_id)
        return queryset


class BotExecutionViewSet(viewsets.ModelViewSet):
    """
    API endpoint для просмотра истории выполнений
    """
    queryset = BotExecution.objects.all().order_by('-started_at')
    serializer_class = BotExecutionSerializer

    def get_queryset(self):
        """
        Фильтрация по боту или сессии пользователя
        """
        queryset = BotExecution.objects.all()
        bot_id = self.request.query_params.get('bot_id')
        user_session = self.request.query_params.get('user_session')

        if bot_id:
            queryset = queryset.filter(bot_id=bot_id)
        if user_session:
            queryset = queryset.filter(user_session=user_session)

        return queryset


@api_view(['GET'])
def api_root(request):
    """
    Корневой endpoint API
    """
    return Response({
        'message': 'Добро пожаловать в Alpina GPT Bot Builder API!',
        'endpoints': {
            'bots': '/api/bots/',
            'scenarios': '/api/scenarios/',
            'steps': '/api/steps/',
            'executions': '/api/executions/',
            'admin': '/admin/'
        },
        'demo_mode': True,
        'status': 'active'
    })


@api_view(['POST'])
def test_bot_creation(request):
    """
    Тестовый endpoint для создания демо-бота
    """
    from django.contrib.auth.models import User

    # Создаем тестового пользователя если нет
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={'email': 'demo@alpina.digital', 'is_staff': True}
    )

    # Создаем демо-бота
    demo_bot, created = Bot.objects.get_or_create(
        name='Демо-бот Alpina Digital',
        defaults={
            'description': 'Тестовый бот для демонстрации возможностей платформы',
            'bot_type': 'chat',
            'gpt_model': 'alpina-demo',
            'temperature': 0.7,
            'max_tokens': 1000,
            'system_prompt': 'Ты полезный помощник для демонстрации возможностей Alpina Digital',
            'is_active': True,
            'created_by': user
        }
    )

    return Response({
        'success': True,
        'message': 'Демо-бот создан/найден',
        'bot_id': demo_bot.id,
        'bot_name': demo_bot.name,
        'demo_mode': True
    })
