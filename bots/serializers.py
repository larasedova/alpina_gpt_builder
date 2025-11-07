# bots/serializers.py
from rest_framework import serializers
from .models import Bot, Scenario, Step, BotExecution


class BotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bot
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class BotExecutionSerializer(serializers.ModelSerializer):
    bot_name = serializers.CharField(source='bot.name', read_only=True)

    class Meta:
        model = BotExecution
        fields = '__all__'
        read_only_fields = ('started_at', 'updated_at')


class ChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    user_session = serializers.CharField(max_length=100, required=False)
    scenario_id = serializers.IntegerField(required=False)
    