import openai
from django.conf import settings
from .models import Bot, BotExecution, Step


class GPTService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def process_message(self, bot: Bot, message: str, user_session: str) -> dict:
        # Найти или создать выполнение бота
        execution, created = BotExecution.objects.get_or_create(
            bot=bot,
            user_session=user_session,
            defaults={
                'scenario': bot.scenarios.filter(is_active=True).first(),
                'conversation_history': []
            }
        )

        # Обновить историю разговора
        conversation_history = execution.conversation_history
        conversation_history.append({"role": "user", "content": message})

        try:
            # Подготовить сообщения для GPT
            messages = self._prepare_messages(bot, conversation_history)

            # Вызвать GPT API
            response = self.client.chat.completions.create(
                model=bot.gpt_model,
                messages=messages,
                temperature=bot.temperature,
                max_tokens=bot.max_tokens
            )

            # Извлечь ответ
            gpt_response = response.choices[0].message.content

            # Обновить историю разговора
            conversation_history.append({"role": "assistant", "content": gpt_response})
            execution.conversation_history = conversation_history
            execution.save()

            return {
                'response': gpt_response,
                'execution_id': execution.id,
                'tokens_used': response.usage.total_tokens if response.usage else None
            }

        except Exception as e:
            # В случае ошибки вернуть сообщение об ошибке
            conversation_history.append(
                {"role": "assistant", "content": "Извините, произошла ошибка. Пожалуйста, попробуйте позже."})
            execution.conversation_history = conversation_history
            execution.save()

            raise e

    def _prepare_messages(self, bot: Bot, conversation_history: list) -> list:
        messages = []

        # Добавить системный промпт
        if bot.system_prompt:
            messages.append({"role": "system", "content": bot.system_prompt})

        # Добавить историю разговора
        messages.extend(conversation_history)

        return messages

    def execute_scenario_step(self, execution: BotExecution, user_input: str = None) -> dict:
        """Выполнить шаг сценария"""
        current_step = execution.current_step

        if not current_step:
            # Начать с начального шага сценария
            current_step = execution.scenario.initial_step
            if not current_step:
                return {
                    'response': 'Сценарий не имеет начального шага.',
                    'is_completed': True
                }

        # Обработать шаг в зависимости от его типа
        step_result = self._process_step(current_step, user_input, execution)

        # Перейти к следующему шагу или завершить
        if step_result.get('next_step'):
            execution.current_step = step_result['next_step']
        elif not step_result.get('has_next_step', True):
            execution.is_completed = True

        execution.save()

        return step_result

    def _process_step(self, step: Step, user_input: str, execution: BotExecution) -> dict:
        """Обработать конкретный шаг сценария"""
        step_type = step.step_type
        content = step.content

        if step_type == 'message':
            return self._process_message_step(content)
        elif step_type == 'question':
            return self._process_question_step(content, user_input, step)
        elif step_type == 'condition':
            return self._process_condition_step(content, user_input, step)
        elif step_type == 'api_call':
            return self._process_api_call_step(content, execution)
        else:
            return {
                'response': 'Неизвестный тип шага.',
                'is_completed': True
            }

    def _process_message_step(self, content: dict) -> dict:
        """Обработать шаг-сообщение"""
        return {
            'response': content.get('message', ''),
            'next_step': None,  # Будет определено из next_step поля модели
            'has_next_step': True
        }

    def _process_question_step(self, content: dict, user_input: str, step: Step) -> dict:
        """Обработать шаг-вопрос"""
        if user_input is None:
            # Первый вызов - задать вопрос
            return {
                'response': content.get('question', ''),
                'wait_for_input': True,
                'has_next_step': False  # Ждем ответ пользователя
            }
        else:
            # Обработать ответ пользователя
            # Здесь можно добавить логику валидации ответа
            return {
                'response': content.get('response_template', '').format(user_input=user_input),
                'next_step': step.next_step,
                'has_next_step': step.next_step is not None
            }

    def _process_condition_step(self, content: dict, user_input: str, step: Step) -> dict:
        """Обработать шаг-условие"""
        # Простая реализация условий на основе ключевых слов
        conditions = content.get('conditions', {})
        user_input_lower = user_input.lower() if user_input else ''

        for condition, next_step_id in conditions.items():
            if condition.lower() in user_input_lower:
                try:
                    next_step = Step.objects.get(id=next_step_id)
                    return {
                        'response': content.get('responses', {}).get(condition, ''),
                        'next_step': next_step,
                        'has_next_step': True
                    }
                except Step.DoesNotExist:
                    continue

        # Если ни одно условие не выполнено
        default_response = content.get('default_response', 'Не понимаю ваш ответ.')
        return {
            'response': default_response,
            'next_step': step.next_step,  # Повторить текущий шаг или перейти к следующему
            'has_next_step': step.next_step is not None
        }

    def _process_api_call_step(self, content: dict, execution: BotExecution) -> dict:
        """Обработать шаг с API вызовом"""
        # Здесь можно реализовать вызов внешних API
        # Пока возвращаем заглушку
        return {
            'response': content.get('success_message', 'API вызов выполнен.'),
            'next_step': None,
            'has_next_step': True
        }