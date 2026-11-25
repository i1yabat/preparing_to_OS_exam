from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView

from .forms import QuizForm
from .models import Choice, Topic


class HomeView(ListView):
    template_name = "home.html"
    context_object_name = "topics"
    queryset = Topic.objects.annotate(question_count=Count("questions"))
    ordering = ("name", "pk")


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
