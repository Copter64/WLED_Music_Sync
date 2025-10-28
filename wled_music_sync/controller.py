"""WLED Controller interface module."""
import json
import logging
from typing import Any, Dict

import aiohttp

LOGGER = logging.getLogger(__name__)

class WLEDController:
    """
    Talks to a single WLED instance via its JSON API.

    Supports both state scenes and preset recall.
    """
    # Timeouts in seconds
    WLED_HTTP_TIMEOUT = 0.5  # Total timeout for any HTTP request
    WLED_CONNECT_TIMEOUT = 0.2  # Timeout for establishing connection
    WLED_READ_TIMEOUT = 0.3  # Timeout for reading response
    
    def __init__(self, controller_id: str, base_url: str):
        self.id = controller_id
        self.base_url = base_url.rstrip("/")
        self._internal_session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._internal_session is None:
            # Use more specific timeouts to prevent hanging
            timeout = aiohttp.ClientTimeout(
                total=self.WLED_HTTP_TIMEOUT,
                connect=self.WLED_CONNECT_TIMEOUT,
                sock_read=self.WLED_READ_TIMEOUT
            )
            connector = aiohttp.TCPConnector(
                force_close=True,  # Don't keep connections alive
                enable_cleanup_closed=True  # Clean up closed connections
            )
            self._internal_session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
        return self._internal_session

    async def apply_scene(self, scene: Dict[str, Any], dry_run: bool = False) -> bool:
        """
        Apply a scene or preset to this WLED controller via /json endpoint.
        
        Args:
            scene: Scene definition dictionary:
                - {"preset": <num>} for preset recall by number
                - {"preset_name": "<n>"} for preset recall by name
                - Any other keys will be sent directly as state
            dry_run: If True, log but don't send commands
            
        Returns:
            bool: True if successful, False on error
        """
        # Determine endpoint and payload
        if "preset" in scene:
            # Match the working approach from wled_preset_uploader.py
            url = f"{self.base_url}/json"
            payload = {"ps": scene["preset"], "on": True}  # ensure lights are on when recalling preset
        elif "preset_name" in scene:
            # preset_name requires lookup from WLED's /presets (optional)
            return await self._apply_preset_by_name(scene["preset_name"], dry_run)
        else:
            url = f"{self.base_url}/json"
            payload = scene

        if dry_run:
            LOGGER.info("[DRY RUN] %s would POST %s -> %s", self.id, json.dumps(payload), url)
            return True

        session = await self._get_session()
        try:
            async with session.post(url, json=payload) as resp:
                text = await resp.text()
                if 200 <= resp.status < 300:
                    LOGGER.debug("WLED %s response: %s", self.id, text)
                    return True
                LOGGER.warning("WLED %s HTTP %s: %s", self.id, resp.status, text)
                return False
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("Error posting to %s: %s", self.id, exc)
            return False

    async def _apply_preset_by_name(self, name: str, dry_run: bool) -> bool:
        """Lookup preset by name and apply if found."""
        if dry_run:
            LOGGER.info("[DRY RUN] %s would recall preset_name=%s", self.id, name)
            return True
        session = await self._get_session()
        try:
            async with session.get(f"{self.base_url}/presets") as resp:
                data = await resp.json(content_type=None)
                match = next((pid for pid, val in data.items() if val.get("n") == name), None)
                if not match:
                    LOGGER.warning("Preset '%s' not found on %s", name, self.id)
                    return False
            # recall by id using the same approach as wled_preset_uploader.py
            url = f"{self.base_url}/json"
            payload = {"ps": int(match), "on": True}
            if dry_run:
                LOGGER.info("[DRY RUN] %s would POST %s -> %s", self.id, json.dumps(payload), url)
                return True
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                text = await resp.text()
                if 200 <= resp.status < 300:
                    LOGGER.debug("WLED %s response: %s", self.id, text)
                    return True
                LOGGER.warning("WLED %s HTTP %s: %s", self.id, resp.status, text)
                return False
        except Exception as exc:
            LOGGER.warning("Error looking up preset_name '%s' on %s: %s", name, self.id, exc)
            return False

    async def close(self) -> None:
        if self._internal_session:
            await self._internal_session.close()
            self._internal_session = None
