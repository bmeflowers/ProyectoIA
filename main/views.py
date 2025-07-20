import os
from django.http import FileResponse, Http404
from django.conf import settings

def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'main', 'serviceworkers', 'service-worker.js')
    if not os.path.exists(sw_path):
        raise Http404("Service worker not found.")
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript', headers={
        'Service-Worker-Allowed': '/',
    })
