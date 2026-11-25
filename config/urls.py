from django.urls import path

from quiz.views import HomeView, TopicDetailView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("topics/<slug:slug>/", TopicDetailView.as_view(), name="topic-detail"),
]
