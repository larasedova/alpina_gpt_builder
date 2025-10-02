from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Bot, Scenario, Step, BotExecution
from .serializers import (
    BotSerializer, ScenarioSerializer, StepSerializer,
    BotExecutionSerializer, StepCreateSerializer, GPTRequestSerializer
)
from .services import GPTService


def home(request):
    """Главная страница с информацией о API"""
    return render(request, 'home.html', {
        'title': 'Alpina GPT Bot Builder',
        'api_endpoints': [
            {'url': '/api/bots/', 'methods': 'GET, POST', 'description': 'CRUD для ботов'},
            {'url': '/api/scenarios/', 'methods': 'GET, POST', 'description': 'CRUD для сценариев'},
            {'url': '/api/steps/', 'methods': 'GET, POST', 'description': 'CRUD для шагов'},
            {'url': '/api/executions/', 'methods': 'GET, POST', 'description': 'История выполнений'},
            {'url': '/admin/', 'methods': 'GET', 'description': 'Административная панель'},
        ]
    })


@api_view(['GET'])
def api_root(request):
    """Корневой endpoint API"""
    return Response({
        'message': 'Welcome to Alpina GPT Bot Builder API',
        'endpoints': {
            'bots': '/api/bots/',
            'scenarios': '/api/scenarios/',
            'steps': '/api/steps/',
            'executions': '/api/executions/',
            'admin': '/admin/',
        }
    })


class BotViewSet(viewsets.ModelViewSet):
    queryset = Bot.objects.all()
    serializer_class = BotSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'bot_type']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        bot = self.get_object()
        serializer = GPTRequestSerializer(data=request.data)

        if serializer.is_valid():
            gpt_service = GPTService()
            try:
                response = gpt_service.process_message(
                    bot=bot,
                    message=serializer.validated_data['message'],
                    user_session=serializer.validated_data['user_session']
                )
                return Response(response)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bot', 'is_active']

    @action(detail=True, methods=['get', 'post'])
    def steps(self, request, pk=None):
        """GET/POST для шагов конкретного сценария"""
        scenario = self.get_object()

        if request.method == 'GET':
            steps = scenario.steps.all()
            serializer = StepSerializer(steps, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = StepCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(scenario=scenario)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StepViewSet(viewsets.ModelViewSet):
    queryset = Step.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return StepCreateSerializer
        return StepSerializer

    def get_queryset(self):
        queryset = Step.objects.all()
        scenario_id = self.request.query_params.get('scenario_id')
        if scenario_id:
            queryset = queryset.filter(scenario_id=scenario_id)
        return queryset


class BotExecutionViewSet(viewsets.ModelViewSet):
    queryset = BotExecution.objects.all()
    serializer_class = BotExecutionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bot', 'scenario', 'user_session', 'is_completed']