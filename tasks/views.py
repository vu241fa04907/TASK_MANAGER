from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from .forms import RegisterForm, TaskForm
from .models import Subtask, Tag, Task


def parse_tag_names(raw_tags):
    return [tag.strip() for tag in (raw_tags or '').split(',') if tag.strip()]


def get_or_create_tags(raw_tags):
    tags = []
    for name in parse_tag_names(raw_tags):
        tag = Tag.objects.filter(name__iexact=name).first()
        if not tag:
            tag = Tag.objects.create(name=name)
        tags.append(tag)
    return tags


def parse_subtasks(raw_subtasks):
    return [line.strip() for line in (raw_subtasks or '').splitlines() if line.strip()]


def set_task_subtasks(task, raw_subtasks):
    subtask_titles = parse_subtasks(raw_subtasks)
    task.subtasks.all().delete()
    subtasks = [Subtask(task=task, title=title) for title in subtask_titles]
    Subtask.objects.bulk_create(subtasks)


def home(request):
    if request.user.is_authenticated:
        tasks = Task.objects.filter(owner=request.user)
        overdue = tasks.filter(due_date__lt=date.today(), completed=False)
        due_soon = [task for task in tasks if task.is_due_soon() and not task.completed]
        reminders = tasks.filter(reminder_date__isnull=False, reminder_date__lte=date.today(), completed=False)
        category_counts = tasks.values('category').annotate(count=Count('id')).order_by('-count')
        priority_counts = {
            'High': tasks.filter(priority=Task.PRIORITY_HIGH, completed=False).count(),
            'Medium': tasks.filter(priority=Task.PRIORITY_MEDIUM, completed=False).count(),
            'Low': tasks.filter(priority=Task.PRIORITY_LOW, completed=False).count(),
        }
        context = {
            'tasks': tasks,
            'overdue': overdue,
            'due_soon': due_soon,
            'reminders': reminders,
            'priority_counts': priority_counts,
            'category_counts': category_counts,
        }
        return render(request, 'tasks/home.html', context)
    return render(request, 'tasks/home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. Please log in with your username and password.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'tasks/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'tasks/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    base_tasks = Task.objects.filter(owner=request.user).prefetch_related('tags')
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    category_filter = request.GET.get('category', 'all')
    sort_by = request.GET.get('sort', 'recent')
    search_query = request.GET.get('q', '').strip()
    view_mode = request.GET.get('view', 'standard')

    tasks = base_tasks
    if status_filter == 'open':
        tasks = tasks.filter(completed=False)
    elif status_filter == 'completed':
        tasks = tasks.filter(completed=True)

    if priority_filter in [Task.PRIORITY_HIGH, Task.PRIORITY_MEDIUM, Task.PRIORITY_LOW]:
        tasks = tasks.filter(priority=priority_filter)

    if category_filter != 'all':
        tasks = tasks.filter(category__iexact=category_filter)

    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(tags__name__icontains=search_query)
        ).distinct()

    if sort_by == 'due':
        tasks = tasks.order_by('due_date', '-created_at')
    elif sort_by == 'priority':
        tasks = tasks.annotate(
            priority_rank=Case(
                When(priority=Task.PRIORITY_HIGH, then=Value(0)),
                When(priority=Task.PRIORITY_MEDIUM, then=Value(1)),
                When(priority=Task.PRIORITY_LOW, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('priority_rank', 'due_date', '-created_at')
    else:
        tasks = tasks.order_by('-created_at')

    overdue = base_tasks.filter(due_date__lt=date.today(), completed=False)
    due_soon = [task for task in base_tasks if task.is_due_soon() and not task.completed]
    reminders = base_tasks.filter(reminder_date__isnull=False, reminder_date__lte=date.today(), completed=False)
    category_list = [cat for cat in base_tasks.values_list('category', flat=True).distinct() if cat]
    completed_count = base_tasks.filter(completed=True).count()
    total_count = base_tasks.count()
    completion_rate = int(completed_count * 100 / total_count) if total_count else 0
    priority_counts = {
        'High': base_tasks.filter(priority=Task.PRIORITY_HIGH, completed=False).count(),
        'Medium': base_tasks.filter(priority=Task.PRIORITY_MEDIUM, completed=False).count(),
        'Low': base_tasks.filter(priority=Task.PRIORITY_LOW, completed=False).count(),
    }
    context = {
        'tasks': tasks,
        'overdue': overdue,
        'due_soon': due_soon,
        'reminders': reminders,
        'priority_counts': priority_counts,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'search_query': search_query,
        'view_mode': view_mode,
        'category_list': category_list,
        'completion_rate': completion_rate,
        'completed_count': completed_count,
        'total_count': total_count,
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def calendar_view(request):
    tasks = Task.objects.filter(owner=request.user, due_date__isnull=False).prefetch_related('tags')
    today = date.today()
    current_year = today.year
    selected_year = request.GET.get('year')
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = current_year

    if selected_year < current_year - 1 or selected_year > current_year + 1:
        selected_year = current_year

    start_date = date(selected_year, 1, 1)
    end_date = date(selected_year, 12, 31)
    selected_date_param = request.GET.get('selected_date')
    selected_date = None
    if selected_date_param:
        try:
            selected_date = date.fromisoformat(selected_date_param)
            if selected_date.year != selected_year:
                selected_date = None
        except ValueError:
            selected_date = None

    if not selected_date:
        selected_date = today if today.year == selected_year else start_date

    task_by_date = {}
    for task in tasks:
        task_by_date.setdefault(task.due_date, []).append(task)

    year_days = []
    day_count = (end_date - start_date).days + 1
    for i in range(day_count):
        current_date = start_date + timedelta(days=i)
        year_days.append({
            'date': current_date,
            'label': current_date.strftime('%A'),
            'tasks': task_by_date.get(current_date, []),
        })

    year_months = []
    current_month = None
    for day in year_days:
        month_label = day['date'].strftime('%B')
        if not current_month or current_month['month_label'] != month_label or current_month['year'] != day['date'].year:
            current_month = {
                'month_label': month_label,
                'year': day['date'].year,
                'days': [],
            }
            year_months.append(current_month)
        current_month['days'].append(day)

    day_count = len(year_days)
    overdue = tasks.filter(due_date__lt=start_date)
    due_this_year = tasks.filter(due_date__range=(start_date, end_date)).count()
    year_options = [current_year - 1, current_year, current_year + 1]
    context = {
        'year_months': year_months,
        'overdue': overdue,
        'today': today,
        'selected_year': selected_year,
        'selected_date': selected_date,
        'year_options': year_options,
        'due_this_year': due_this_year,
        'year_end': end_date,
        'day_count': day_count,
    }
    return render(request, 'tasks/calendar.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            tags = get_or_create_tags(form.cleaned_data.get('tags_raw', ''))
            task.tags.set(tags)
            set_task_subtasks(task, form.cleaned_data.get('subtasks_raw', ''))
            messages.success(request, 'Task added successfully.')
            return redirect('dashboard')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Add Task'})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            task.tags.set(get_or_create_tags(form.cleaned_data.get('tags_raw', '')))
            set_task_subtasks(task, form.cleaned_data.get('subtasks_raw', ''))
            messages.success(request, 'Task updated successfully.')
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Edit Task'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('dashboard')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_toggle_status(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    task.completed = not task.completed
    task.save()
    return redirect('dashboard')


@login_required
def subtask_toggle_status(request, pk):
    subtask = get_object_or_404(Subtask, pk=pk, task__owner=request.user)
    subtask.completed = not subtask.completed
    subtask.save()
    return redirect('dashboard')
