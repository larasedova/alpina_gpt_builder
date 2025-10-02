from rest_framework import serializers
from .models import Bot, Scenario, Step, BotExecution


class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = [
            'id', 'name', 'step_type', 'scenario', 'content',
            'order', 'next_step', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ScenarioSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True, read_only=True)

    class Meta:
        model = Scenario
        fields = [
            'id', 'name', 'description', 'bot', 'initial_step',
            'is_active', 'created_at', 'updated_at', 'steps'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BotSerializer(serializers.ModelSerializer):
    scenarios = ScenarioSerializer(many=True, read_only=True)

    class Meta:
        model = Bot
        fields = [
            'id', 'name', 'description', 'bot_type', 'gpt_model',
            'temperature', 'max_tokens', 'system_prompt', 'is_active',
            'created_by', 'created_at', 'updated_at', 'scenarios'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class BotExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotExecution
        fields = [
            'id', 'bot', 'scenario', 'user_session', 'current_step',
            'conversation_history', 'is_completed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StepCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = [
            'id', 'name', 'step_type', 'scenario', 'content',
            'order', 'next_step'
        ]


class GPTRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    user_session = serializers.CharField(required=True)
    bot_id = serializers.IntegerField(required=True)