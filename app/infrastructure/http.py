# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Cliente HTTP para descargar datos públicos (Wikipedia y APIs deportivas)."""
from __future__ import annotations

import requests
import urllib3

from ..core.config import PUBLIC_MODE, USER_AGENT


def get(url: str, *, headers: dict | None = None, timeout: int = 25) -> requests.Response:
    base_headers = {"User-Agent": USER_AGENT}
    if headers:
        base_headers.update(headers)
    try:
        return requests.get(url, headers=base_headers, timeout=timeout)
    except requests.exceptions.SSLError:
        # En despliegue público se mantiene siempre la verificación del
        # certificado. El reintento sin verificar queda reservado a un uso
        # local de desarrollo, nunca expuesto a internet.
        if PUBLIC_MODE:
            raise
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return requests.get(url, headers=base_headers, timeout=timeout, verify=False)
