from django import forms


def answer_field_name(question):
    return f"question_{question.pk}"


class QuizForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = questions
        for question in questions:
            self.fields[answer_field_name(question)] = forms.TypedChoiceField(
                label=question.text,
                choices=[(choice.pk, choice.text) for choice in question.choices.all()],
                coerce=int,
                widget=forms.RadioSelect,
                error_messages={
                    "required": "Выберите ответ на этот вопрос.",
                    "invalid_choice": "Этот вариант не относится к данному вопросу.",
                },
            )

    def clean(self):
        cleaned_data = super().clean()
        if any(
            name.startswith("question_") and name not in self.fields for name in self.data
        ):
            self.add_error(None, "В отправленных ответах есть вопрос не из этой темы.")
        if hasattr(self.data, "getlist"):
            for name in self.fields:
                if len(self.data.getlist(name)) > 1:
                    self.add_error(name, "Выберите только один вариант ответа.")
        return cleaned_data

    def grade(self):
        mistakes = []
        for question in self.questions:
            selected_id = self.cleaned_data[answer_field_name(question)]
            choices = question.choices.all()
            correct_choice = next((choice for choice in choices if choice.is_correct), None)
            if correct_choice is None or selected_id != correct_choice.pk:
                mistakes.append({"question": question, "correct_choice": correct_choice})
        return len(self.questions) - len(mistakes), mistakes
