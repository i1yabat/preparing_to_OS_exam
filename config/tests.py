from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from redis import Redis

from quiz.models import Question, Topic
from quiz.views import TOPIC_LIST_CACHE_KEY


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-topic-pages",
        }
    }
)
class TopicViewTestCase(TestCase):
    def setUp(self):
        super().setUp()
        cache.delete(TOPIC_LIST_CACHE_KEY)


class HomePageTests(TopicViewTestCase):
    def test_home_page_renders_heading_and_empty_message(self):
        response = self.client.get(reverse("home"))

        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "<h1>Тренажёр по операционным системам</h1>", html=True)
        self.assertContains(response, 'href="/static/quiz/site.css"')
        self.assertContains(response, "Темы пока не добавлены")


class TopicPageTests(TopicViewTestCase):
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


class TopicCacheTests(TestCase):
    def setUp(self):
        super().setUp()
        # Keep the test database's catalogue out of the running site's cache.
        backend = {**settings.CACHES["default"], "KEY_PREFIX": f"test:{uuid4().hex}"}
        self.enterContext(self.settings(CACHES={"default": backend}))
        self.addCleanup(cache.delete, TOPIC_LIST_CACHE_KEY)
        self.valkey = Redis.from_url(backend["LOCATION"])
        self.addCleanup(self.valkey.close)
        self.key = cache.make_key(TOPIC_LIST_CACHE_KEY)

    def test_cold_and_warm_catalogue_on_valkey(self):
        topic = Topic.objects.create(name="Процессы", slug="processes")
        Question.objects.create(topic=topic, text="Что такое процесс?")
        url = reverse("home")

        self.assertEqual(self.valkey.ttl(self.key), -2)
        with self.assertNumQueries(1):
            cold = self.client.get(url)
        self.assertContains(cold, "Вопросов: 1")
        self.assertEqual(
            cache.get(TOPIC_LIST_CACHE_KEY),
            [{"name": "Процессы", "slug": "processes", "question_count": 1}],
        )
        self.assertIn(self.valkey.ttl(self.key), range(55, 61))

        self.valkey.expire(self.key, 30)
        with self.assertNumQueries(0):
            warm = self.client.get(url)
        self.assertEqual(warm.content, cold.content)
        self.assertIn(self.valkey.ttl(self.key), range(1, 31))

        self.valkey.expire(self.key, 0)
        self.assertEqual(self.valkey.ttl(self.key), -2)
        with self.assertNumQueries(1):
            self.client.get(url)

    def test_empty_catalogue_is_cached(self):
        url = reverse("home")
        with self.assertNumQueries(1):
            cold = self.client.get(url)
        self.assertEqual(cache.get(TOPIC_LIST_CACHE_KEY), [])

        with self.assertNumQueries(0):
            warm = self.client.get(url)
        self.assertContains(warm, "Темы пока не добавлены")
        self.assertEqual(warm.content, cold.content)
