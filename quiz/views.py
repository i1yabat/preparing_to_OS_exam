from django.db.models import Count
from django.views.generic import DetailView, ListView

from .models import Topic


class HomeView(ListView):
    template_name = "home.html"
    context_object_name = "topics"
    queryset = Topic.objects.annotate(question_count=Count("questions"))
    ordering = ("name", "pk")


class TopicDetailView(DetailView):
    template_name = "topic_detail.html"
    context_object_name = "topic"
    queryset = Topic.objects.annotate(question_count=Count("questions"))
