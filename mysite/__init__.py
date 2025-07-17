try:
    from .celery import app as celery_app
except ImportError:
    # Manejar casos en el cual celery no está listo aún o para entorno específicos
    celery_app = None

__all__ = ('celery_app',)