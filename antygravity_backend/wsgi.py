"""
WSGI config for antygravity_backend project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'antygravity_backend.settings')
application = get_wsgi_application()

# Self-Ping to keep Render Free Tier active (prevents spin-down)
import threading
import time
import requests
import os

def keep_alive():
    """Pings the server every 13 minutes to prevent sleep."""
    url = "https://backend-network-b9qb.onrender.com/admin/login/" # Lightweight page
    
    # Wait initially to let server start
    time.sleep(10)
    
    while True:
        try:
            print(f"Keeping alive: Pinging {url}...")
            response = requests.get(url)
            print(f"Ping status: {response.status_code}")
        except Exception as e:
            print(f"Ping failed: {e}")
        
        # Sleep for 13 minutes (Render sleeps after 15)
        time.sleep(13 * 60)

# Only start if on Render
if 'RENDER_EXTERNAL_HOSTNAME' in os.environ:
    t = threading.Thread(target=keep_alive, daemon=True)
    t.start()
