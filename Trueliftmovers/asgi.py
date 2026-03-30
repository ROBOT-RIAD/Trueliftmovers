# import os
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from django.core.asgi import get_asgi_application
# from Channel import routing
# from Channel.middleware import JWTAuthMiddleware, ProtocolAcceptMiddleware



# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Trueliftmovers.settings')



# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": ProtocolAcceptMiddleware(
#         JWTAuthMiddleware(
#             AuthMiddlewareStack(
#                 URLRouter(routing.websocket_urlpatterns)
#             )
#         )
#     ),
# })





# # Trueliftmovers/asgi.py

import os
from django.core.asgi import get_asgi_application

# VERY IMPORTANT: do this FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Trueliftmovers.settings')

# This initializes Django → loads apps → registers models
django_asgi_app = get_asgi_application()

# ────────────────────────────────────────────────
# ONLY NOW import your Channels stuff
# ────────────────────────────────────────────────

from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack           # if you still use old one
from channels.security.websocket import AllowedHostsOriginValidator

# your custom middleware
from Channel.middleware import JWTAuthMiddleware, ProtocolAcceptMiddleware

from Channel import routing   # or wherever your websocket_urlpatterns lives

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AllowedHostsOriginValidator(         # usually good to keep
        JWTAuthMiddleware(                            # ← your JWT middleware
            ProtocolAcceptMiddleware(                 # if you really need it
                URLRouter(routing.websocket_urlpatterns)
            )
        ),
    ),
})



