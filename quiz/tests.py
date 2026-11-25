from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Choice, Question, Topic


class DemoFixtureTests(TestCase):
    fixtures = ["demo.json"]

    def test_demo_contains_two_topics_with_five_questions_each(self):
        self.assertCountEqual(
            Topic.objects.values_list("slug", "name"),
            [("processes", "Процессы"), ("memory", "Память")],
        )
        for topic in Topic.objects.all():
            with self.subTest(topic=topic.slug):
                self.assertEqual(topic.questions.count(), 5)

    def test_each_question_has_an_explanation_and_one_correct_choice(self):
        for topic in Topic.objects.prefetch_related("questions__choices"):
            for question in topic.questions.all():
                with self.subTest(question=question.pk):
                    choices = list(question.choices.all())
                    self.assertTrue(question.text.strip())
                    self.assertTrue(question.explanation.strip())
                    self.assertEqual(len(choices), 4)
                    self.assertEqual(sum(choice.is_correct for choice in choices), 1)
                    self.assertEqual(len({choice.text.strip() for choice in choices}), 4)
                    self.assertTrue(all(choice.text.strip() for choice in choices))

    def test_database_rejects_a_second_correct_choice(self):
        question = Topic.objects.get(slug="processes").questions.first()

        with self.assertRaises(IntegrityError), transaction.atomic():
            Choice.objects.create(
                question=question, text="Второй правильный вариант", is_correct=True
            )


class QuizPageTests(TestCase):
    fixtures = ["demo.json"]

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("topic-detail", kwargs={"slug": "processes"})
        cls.answers = {
            "question_1": 2,
            "question_2": 5,
            "question_3": 9,
            "question_4": 13,
            "question_5": 18,
        }

    def test_topic_shows_all_questions_and_choices(self):
        response = self.client.get(self.url)

        self.assertContains(response, "<fieldset", count=5)
        self.assertContains(response, 'type="radio"', count=20)
        for question in Question.objects.filter(topic__slug="processes"):
            self.assertContains(response, question.text)
            self.assertNotContains(response, question.explanation)
        self.assertNotContains(response, 'name="question_6"')

    def test_grades_answers_and_explains_only_mistakes(self):
        response = self.client.post(self.url, self.answers)

        self.assertTemplateUsed(response, "topic_result.html")
        self.assertContains(response, "<strong>3/5</strong>", html=True)
        self.assertContains(response, "Правильный ответ:", count=2)
        for question in Question.objects.filter(pk__in=[2, 4]):
            self.assertContains(response, question.text)
            self.assertContains(response, question.choices.get(is_correct=True).text)
            self.assertContains(response, question.explanation)
        self.assertNotContains(response, Question.objects.get(pk=1).explanation)
        self.assertContains(response, '<a href="/">Вернуться к списку тем</a>', html=True)

    def test_score_boundaries(self):
        for choice_ids, score in [([2, 8, 9, 15, 18], 5), ([1, 5, 10, 13, 17], 0)]:
            with self.subTest(score=score):
                answers = dict(zip(self.answers, choice_ids))
                response = self.client.post(self.url, answers)

                self.assertContains(response, f"<strong>{score}/5</strong>", html=True)
                if score == 5:
                    self.assertContains(response, "Все ответы верны.")
                    self.assertNotContains(response, "Разбор ошибок")

    def test_missing_answer_keeps_other_selections_and_does_not_grade(self):
        answers = self.answers.copy()
        missing_answer = answers.pop("question_3")
        response = self.client.post(self.url, answers)

        self.assertTemplateUsed(response, "topic_detail.html")
        self.assertTemplateNotUsed(response, "topic_result.html")
        self.assertContains(response, "Выберите ответ на этот вопрос.", count=1)
        self.assertContains(response, " checked", count=4)
        form = response.context["form"]
        self.assertEqual(form.errors.as_data()["question_3"][0].code, "required")
        for field, choice in answers.items():
            self.assertEqual(form[field].value(), str(choice))

        answers["question_3"] = missing_answer
        response = self.client.post(self.url, answers)
        self.assertContains(response, "<strong>3/5</strong>", html=True)

    def test_rejects_choice_that_does_not_belong_to_the_question(self):
        for choice in [8, 23, 9999, "not-a-choice"]:
            with self.subTest(choice=choice):
                response = self.client.post(self.url, self.answers | {"question_1": choice})

                self.assertTemplateNotUsed(response, "topic_result.html")
                self.assertContains(response, "Этот вариант не относится к данному вопросу.")
                error = response.context["form"].errors.as_data()["question_1"][0]
                self.assertEqual(error.code, "invalid_choice")

    def test_rejects_extra_question_from_another_topic(self):
        response = self.client.post(self.url, self.answers | {"question_6": 23})

        self.assertTemplateNotUsed(response, "topic_result.html")
        self.assertContains(response, "В отправленных ответах есть вопрос не из этой темы.")

    def test_rejects_multiple_choices_for_the_same_question(self):
        response = self.client.post(self.url, self.answers | {"question_1": [1, 2]})

        self.assertTemplateNotUsed(response, "topic_result.html")
        self.assertContains(response, "Выберите только один вариант ответа.")

    def test_unknown_topic_post_returns_404(self):
        url = reverse("topic-detail", kwargs={"slug": "unknown"})

        self.assertEqual(self.client.post(url, self.answers).status_code, 404)

    def test_empty_topic_shows_message_without_quiz(self):
        Topic.objects.create(name="Без вопросов", slug="empty")
        url = reverse("topic-detail", kwargs={"slug": "empty"})
        for response in (self.client.get(url), self.client.post(url)):
            self.assertContains(response, "В этой теме пока нет вопросов.")
            self.assertNotContains(response, "<form")
            self.assertTemplateNotUsed(response, "topic_result.html")
