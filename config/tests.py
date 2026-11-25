from django.test import TestCase
from django.urls import reverse

from quiz.models import Question, Topic


class HomePageTests(TestCase):
    def test_home_page_renders_heading_and_empty_message(self):
        response = self.client.get(reverse("home"))

        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "<h1>Тренажёр по операционным системам</h1>", html=True)
        self.assertContains(response, 'href="/static/quiz/site.css"')
        self.assertContains(response, "Темы пока не добавлены")


class TopicPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        processes = Topic.objects.create(name="Процессы", slug="processes")
        Topic.objects.create(name="Память", slug="memory")
        Question.objects.create(topic=processes, text="Что такое процесс?")

    def test_home_lists_topics_with_links_and_question_counts(self):
        response = self.client.get(reverse("home"))

        for slug, title, count in [("processes", "Процессы", 1), ("memory", "Память", 0)]:
            with self.subTest(slug=slug):
                url = reverse("topic-detail", kwargs={"slug": slug})
                self.assertContains(response, f'href="{url}"')
                self.assertContains(response, f"<h3>{title}</h3>", html=True)
                self.assertContains(response, f"Вопросов: {count}")
        self.assertNotContains(response, "Темы пока не добавлены")

    def test_topic_page_shows_name_and_question_count(self):
        response = self.client.get(reverse("topic-detail", kwargs={"slug": "processes"}))

        self.assertTemplateUsed(response, "topic_detail.html")
        self.assertContains(response, "<h1>Процессы</h1>", html=True)
        self.assertContains(response, "<p>Количество вопросов: 1</p>", html=True)

    def test_unknown_topic_returns_404(self):
        response = self.client.get(reverse("topic-detail", kwargs={"slug": "unknown"}))

        self.assertEqual(response.status_code, 404)
