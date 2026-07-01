"""Shared Fal queue-API transport.

Every Fal-hosted provider (Hunyuan3D, Pixal3D, Tripo, Rodin) submits one job to
``https://queue.fal.run/{endpoint}`` with ``Key`` auth, polls the returned
``status_url`` until ``COMPLETED``, then reads the GLB url from the result. That
mechanic lives here once; a concrete provider is just an ``endpoint`` + ``params``
+ ``_payload`` in its own module. All Fal providers share the ``fal_api_key``
preference.
"""

import time

from ... import api
from ..base import Asset, GenerateRequest, Provider
from ..common import _POLL_INTERVAL, _POLL_TIMEOUT, ProviderError


def _fal_glb_url(result: dict) -> str | None:
    """Pull the GLB download url from a Fal result across known output shapes.

    Different Fal 3D models nest the url differently: ``model_urls.glb.url``
    (Hunyuan3D), ``model_glb.url`` (Hunyuan3D, Pixal3D), or ``model_mesh.url``
    (Tripo, Rodin). ``model_urls.glb`` wins because ``model_glb`` is polymorphic -
    on some Hunyuan tiers it points at an OBJ, whereas ``model_urls.glb`` is
    always GLB.
    """
    url = ((result.get("model_urls") or {}).get("glb") or {}).get("url")
    if url:
        return url
    url = (result.get("model_glb") or {}).get("url")
    if url:
        return url
    return (result.get("model_mesh") or {}).get("url")


class FalQueueProvider(Provider):
    """Base for a Fal queue-API image-to-3D provider.

    Subclasses declare ``endpoint`` and ``params`` and implement ``_payload``.
    Override ``_endpoint`` when the model id depends on params (e.g. a tier).
    """

    api_key_pref_field = "fal_api_key"
    endpoint: str = ""

    def _endpoint(self, params: dict) -> str:
        """The Fal model id to submit to (may depend on params, e.g. a tier)."""
        return self.endpoint

    def _payload(self, req: GenerateRequest) -> dict:
        raise NotImplementedError

    def generate(self, req: GenerateRequest) -> Asset:
        headers = {"Authorization": f"Key {req.api_key}"}

        submit = api.http_post_json(
            f"https://queue.fal.run/{self._endpoint(req.params)}",
            self._payload(req),
            headers,
        )
        status_url = submit.get("status_url")
        response_url = submit.get("response_url")
        if not status_url or not response_url:
            raise ProviderError(f"Fal submit returned no queue URLs: {submit}")

        result = self._poll(status_url, response_url, headers)

        url = _fal_glb_url(result)
        if not url:
            raise ProviderError(f"Fal response had no GLB URL: {result}")

        return Asset(
            url=url,
            format="glb",
            metadata={"provider": self.id, "seed": result.get("seed")},
        )

    def _poll(self, status_url, response_url, headers):
        deadline = time.monotonic() + _POLL_TIMEOUT
        while time.monotonic() < deadline:
            status = api.http_get_json(status_url, headers, timeout=90)
            state = status.get("status")
            if state == "COMPLETED":
                return api.http_get_json(response_url, headers, timeout=_POLL_TIMEOUT)
            if state in ("IN_QUEUE", "IN_PROGRESS"):
                time.sleep(_POLL_INTERVAL)
                continue
            raise ProviderError(f"Fal job in unexpected state: {status}")
        raise ProviderError(f"Fal job timed out after {_POLL_TIMEOUT}s")
