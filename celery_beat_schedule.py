from celery.schedules import crontab
from reminders.tasks import check_and_notify_low_activity

beat_schedule = {
    'check_low_activity_daily': {
        'task': 'notifications.tasks.check_and_notify_low_activity',
        'schedule': crontab(hour=9, minute=0),  # Ejecutar a las 9:00 AM todos los días
    },
}