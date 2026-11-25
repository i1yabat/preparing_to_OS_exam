from django.db import models


class Topic(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    explanation = models.TextField()

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question"],
                condition=models.Q(is_correct=True),
                name="quiz_one_correct_choice",
            )
        ]

    def __str__(self):
        return self.text
