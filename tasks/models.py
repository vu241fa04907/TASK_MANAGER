from django.conf import settings
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Task(models.Model):
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    reminder_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completed', 'due_date', '-priority', 'created_at']

    def __str__(self):
        return self.title

    def is_due_soon(self):
        from datetime import date, timedelta

        if self.due_date:
            return date.today() <= self.due_date <= date.today() + timedelta(days=3)
        return False

    def is_reminder_due(self):
        from datetime import date

        if self.reminder_date:
            return date.today() >= self.reminder_date and not self.completed
        return False

    @property
    def completed_subtasks_count(self):
        return self.subtasks.filter(completed=True).count()

    @property
    def subtasks_count(self):
        return self.subtasks.count()


class Subtask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completed', 'created_at']

    def __str__(self):
        return f"{self.title} ({'done' if self.completed else 'open'})"
