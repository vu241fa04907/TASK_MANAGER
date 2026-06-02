document.addEventListener('DOMContentLoaded', function () {
    function attachAlertCloseButtons() {
        document.querySelectorAll('.alert').forEach(function (alert) {
            if (!alert.querySelector('.alert-close')) {
                var closeButton = document.createElement('button');
                closeButton.type = 'button';
                closeButton.className = 'alert-close';
                closeButton.innerHTML = '&times;';
                closeButton.addEventListener('click', function () {
                    alert.style.display = 'none';
                });
                alert.appendChild(closeButton);
            }
        });
    }

    function attachDeleteConfirmations() {
        document.querySelectorAll('a.delete').forEach(function (link) {
            link.addEventListener('click', function (event) {
                var confirmed = window.confirm('Are you sure you want to delete this task?');
                if (!confirmed) {
                    event.preventDefault();
                }
            });
        });
    }

    function attachTaskToggle() {
        document.querySelectorAll('.task-card h3').forEach(function (title) {
            title.addEventListener('click', function () {
                var card = title.closest('.task-card');
                if (card) {
                    card.classList.toggle('collapsed');
                }
            });
        });
    }

    function attachPasswordToggles() {
        document.querySelectorAll('input[type="password"]').forEach(function (passwordInput) {
            if (passwordInput.closest('.password-field-wrap')) {
                return;
            }

            var wrapper = document.createElement('div');
            wrapper.className = 'password-field-wrap';
            passwordInput.parentNode.insertBefore(wrapper, passwordInput);
            wrapper.appendChild(passwordInput);

            var toggleButton = document.createElement('button');
            toggleButton.type = 'button';
            toggleButton.className = 'password-toggle';
            toggleButton.setAttribute('aria-label', 'Show password');
            toggleButton.innerText = '👁';
            toggleButton.addEventListener('click', function () {
                var type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
                toggleButton.innerText = type === 'password' ? '👁' : '🙈';
                toggleButton.setAttribute('aria-label', type === 'password' ? 'Show password' : 'Hide password');
            });
            wrapper.appendChild(toggleButton);
        });
    }

    function attachCalendarDayDetails() {
        var selectedDatePanel = document.querySelector('.selected-day-card');
        var selectedDayName = selectedDatePanel && selectedDatePanel.querySelector('.selected-day-name');
        var selectedDayDate = selectedDatePanel && selectedDatePanel.querySelector('.selected-day-date');

        document.querySelectorAll('.calendar-day').forEach(function (dayItem) {
            dayItem.addEventListener('click', function () {
                document.querySelectorAll('.calendar-day').forEach(function (other) {
                    other.classList.remove('selected-day');
                });
                dayItem.classList.add('selected-day');
                var dateValue = dayItem.dataset.date;
                var dayValue = dayItem.dataset.day;
                if (selectedDayName) {
                    selectedDayName.textContent = dayValue;
                }
                if (selectedDayDate) {
                    selectedDayDate.textContent = new Date(dateValue).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
                }
                if (dayItem.classList.contains('has-task')) {
                    dayItem.classList.toggle('open');
                }
            });
            dayItem.addEventListener('keydown', function (event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    dayItem.click();
                }
            });
        });
    }

    function attachDateValidation() {
        var dueDate = document.querySelector('#id_due_date');
        var reminderDate = document.querySelector('#id_reminder_date');
        if (!dueDate || !reminderDate) {
            return;
        }

        var form = reminderDate.closest('form');
        var messageEl = document.createElement('p');
        messageEl.style.color = '#b91c1c';
        messageEl.style.marginTop = '4px';
        reminderDate.parentNode.appendChild(messageEl);

        function validateDates() {
            var dueValue = dueDate.value;
            var reminderValue = reminderDate.value;
            if (!reminderValue || !dueValue) {
                messageEl.textContent = '';
                form.querySelector('button[type="submit"]').disabled = false;
                return;
            }

            if (reminderValue > dueValue) {
                messageEl.textContent = 'Reminder date should be on or before the due date.';
                form.querySelector('button[type="submit"]').disabled = true;
            } else {
                messageEl.textContent = '';
                form.querySelector('button[type="submit"]').disabled = false;
            }
        }

        dueDate.addEventListener('change', validateDates);
        reminderDate.addEventListener('change', validateDates);
        validateDates();
    }

    function animateStats() {
        document.querySelectorAll('.stat-value').forEach(function (el) {
            var target = Number(el.dataset.target) || 0;
            var current = 0;
            var duration = 900;
            var stepTime = Math.max(Math.floor(duration / (target || 1)), 16);

            var counter = setInterval(function () {
                current += 1;
                el.textContent = current;
                if (current >= target) {
                    clearInterval(counter);
                    el.textContent = target;
                }
            }, stepTime);
        });
    }

    function animateProgressBars() {
        document.querySelectorAll('.progress-fill').forEach(function (fill) {
            var targetWidth = fill.style.width || '0%';
            fill.style.width = '0%';
            setTimeout(function () {
                fill.style.width = targetWidth;
            }, 120);
        });
    }

    attachAlertCloseButtons();
    attachDeleteConfirmations();
    attachTaskToggle();
    attachPasswordToggles();
    attachCalendarDayDetails();
    attachDateValidation();
    animateStats();
    animateProgressBars();
});