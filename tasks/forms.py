from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task


class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
    )
    reminder_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text='Optional reminder date on or before the due date.',
    )
    tags_raw = forms.CharField(
        required=False,
        help_text='Comma-separated tags.',
        widget=forms.TextInput(attrs={'placeholder': 'personal, urgent, work'}),
    )
    subtasks_raw = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter each subtask on a new line'}),
        help_text='Write one subtask per line.',
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'category', 'priority', 'due_date', 'reminder_date', 'completed', 'tags_raw', 'subtasks_raw']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tags_raw'].initial = ', '.join([tag.name for tag in self.instance.tags.all()])
            self.fields['subtasks_raw'].initial = '\n'.join([subtask.title for subtask in self.instance.subtasks.all()])

    def clean_tags_raw(self):
        raw = self.cleaned_data.get('tags_raw', '')
        return ', '.join([tag.strip() for tag in raw.split(',') if tag.strip()])

    def clean_subtasks_raw(self):
        raw = self.cleaned_data.get('subtasks_raw', '')
        return '\n'.join([line.strip() for line in raw.splitlines() if line.strip()])


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
