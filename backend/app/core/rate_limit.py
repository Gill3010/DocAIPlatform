"""Rate limiting in-memory para forgot-password (5 solicitudes / 15 min por IP)."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import MutableMapping

# IP -> lista de timestamps de solicitudes
_forgot_password_requests: MutableMapping[str, list[float]] = defaultdict(list)
WINDOW_SECONDS = 15 * 60  # 15 minutos
MAX_REQUESTS = 5


def check_forgot_password_rate_limit(ip: str) -> bool:
    """Retorna True si el IP está dentro del límite, False si excedió."""
    now = time.time()
    cutoff = now - WINDOW_SECONDS
    requests = _forgot_password_requests[ip]
    # Limpiar entradas antiguas
    requests[:] = [t for t in requests if t > cutoff]
    if len(requests) >= MAX_REQUESTS:
        return False
    requests.append(now)
    return True
