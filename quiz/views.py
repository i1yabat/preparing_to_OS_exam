from django.core.cache import cache
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .forms import QuizForm
from .models import Choice, Topic

TOPIC_LIST_CACHE_KEY = "quiz:topics"
TOPIC_LIST_CACHE_TTL = 60


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topics = cache.get(TOPIC_LIST_CACHE_KEY)
        if topics is None:
            topics = list(
                Topic.objects.annotate(question_count=Count("questions"))
                .order_by("name", "pk")
                .values("name", "slug", "question_count")
            )
            cache.set(TOPIC_LIST_CACHE_KEY, topics, timeout=TOPIC_LIST_CACHE_TTL)
        context["topics"] = topics
        return context


@require_http_methods(["GET", "HEAD", "POST"])
def topic_detail(request, slug):
    topic = get_object_or_404(Topic, slug=slug)
    questions = list(
        topic.questions.order_by("pk").prefetch_related(
            Prefetch("choices", queryset=Choice.objects.order_by("pk"))
        )
    )
    context = {"topic": topic, "question_count": len(questions)}
    if not questions:
        return render(request, "topic_detail.html", context)

    form = QuizForm(questions, data=request.POST if request.method == "POST" else None)
    if form.is_valid():
        score, mistakes = form.grade()
        context.update(score=score, mistakes=mistakes)
        return render(request, "topic_result.html", context)

    context["form"] = form
    return render(request, "topic_detail.html", context)
