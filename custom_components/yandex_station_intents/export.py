from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import EXPORT_FILENAME
from .entry_data import ConfigEntryData


def _build_export_url(ip_or_url: str, request_path: str) -> str:
    value = ip_or_url.strip()
    if not value:
        raise HomeAssistantError("Не указан IP адрес для экспорта")

    if "://" in value:
        parsed = urlsplit(value)
        if not parsed.scheme or not parsed.netloc:
            raise HomeAssistantError("Некорректный URL для экспорта")
        return value

    path = request_path if request_path.startswith("/") else f"/{request_path}"
    return f"http://{value}{path}"


def _write_export_file(hass: HomeAssistant, data: list[str] | str) -> str:
    out_path = Path(hass.config.path(EXPORT_FILENAME))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, str):
        content = data
    else:
        if not all(isinstance(item, str) for item in data):
            raise HomeAssistantError("Ответ должен содержать строку или список строк")
        content = "\n".join(data)

    out_path.write_text(content, encoding="utf-8")
    return str(out_path)


async def async_export_intents(hass: HomeAssistant, entry_data: ConfigEntryData) -> str:
    url = _build_export_url(entry_data.export_ip, entry_data.export_path)
    session = async_get_clientsession(hass)

    try:
        async with session.get(url) as response:
            response.raise_for_status()
            payload = await response.json()
    except ClientError as err:
        raise HomeAssistantError(f"Не удалось получить данные по адресу {url}: {err}") from err
    except ValueError as err:
        raise HomeAssistantError("Сервис экспорта вернул невалидный JSON") from err

    if isinstance(payload, dict) and "data" in payload:
        payload = payload["data"]

    if not isinstance(payload, (list, str)):
        raise HomeAssistantError("Сервис экспорта должен вернуть JSON строку или список строк")

    return await hass.async_add_executor_job(_write_export_file, hass, payload)
