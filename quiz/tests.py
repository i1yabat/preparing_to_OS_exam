from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Choice, Topic


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
