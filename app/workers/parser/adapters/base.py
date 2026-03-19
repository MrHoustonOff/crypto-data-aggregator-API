from abc import ABC, abstractmethod
from functools import cached_property
import httpx


class BaseAdapter(ABC):

    @property
    @abstractmethod
    def mapping(self) -> dict[str, str]:
        """Словарь-трафарет. Обязателен для переопределения как property."""
        pass

    @cached_property
    def reverse_mapping(self) -> dict[str, str]:
        """Автоматически инвертирует mapping"""
        return {v: k for k, v in self.mapping.items()}

    @abstractmethod
    def prepare_request_url(self, tickers: list[str]) -> str:
        pass

    @abstractmethod
    def normalize_response(self, response: dict | list) -> dict:
        pass

    async def get_price(self, client: httpx.AsyncClient, tickers: list[str]) -> dict:
        price_url = self.prepare_request_url(tickers)

        if price_url == "":
            return dict()

        response = await client.get(price_url)

        # TODO: Интеграция с Tenacity (Exponential Backoff)
        # Сейчас мы глотаем ошибки (включая 429 Too Many Requests).
        # здесь нужно делать response.raise_for_status(),
        # чтобы библиотека tenacity (или код выше) перехватила исключение и ушла в retry.
        if response.status_code != 200:
            return dict()

        # TODO: Защита от кривого ответа (Cloudflare HTML)
        # Если статус 200, но сервер (или балансировщик) вернул HTML вместо JSON,
        # метод .json() выкинет ошибку. Нужно обернуть в try/except и логировать сбой.
        response_json = response.json()

        return self.normalize_response(response_json)
