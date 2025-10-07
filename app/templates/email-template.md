# Daily Brief - {{ date }}

## 📅 Today's Schedule
{% for event in calendar_events %}
- **{{ event.start_time }}**: {{ event.title }}
  - Location: {{ event.location }}
  - Travel: {{ event.travel_instructions }}
{% endfor %}

## 🌤️ Weather & Clothing
- **Forecast**: {{ weather.summary }}
- **Suggested outfit**: {{ clothing_suggestion }}

## 📧 Yesterday's New Emails
{% for email in emails %}
- [{{ email.subject }}]({{ email.link }}) - {{ email.sender }}
{% endfor %}

## ✅ Reminders Created
{% for task in tasks %}
- {{ task.title }} (Due: {{ task.due_time }})
{% endfor %}