# Daily Brief - {{ date }}

## 📅 Today's Schedule
{% for event in calendar_events %}

**{{ event.start_time }}**: {{ event.summary }}
  - Location: {{ event.location }}
      - Travel: {{ event.transportation }}
----------------------------------
{% endfor %}
## Todays Weather Forcast.

{% for hour_data in weather %}
- **{{ hour_data.hour }}**: {{ hour_data.temperature }}°C, precipitation {{ hour_data.precipitation }}mm
{% endfor %}

## 📧 Unread Emails.
{% for email in new_email %}
- [{{ email.subject }}]({{ email.summary }}) - {{ email.sender }}
{% endfor %}

