from django.urls import path

from quiz.views import HomeView, topic_detail

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("topics/<slug:slug>/", topic_detail, name="topic-detail"),
]
