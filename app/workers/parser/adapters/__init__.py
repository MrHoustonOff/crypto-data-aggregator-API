from .base import BaseAdapter
from .coingecko import CoinGeckoAdapter
from .binance import BinanceAdapter

# Явно указываем, что доступно при импорте из пакета adapters
__all__ = [
    "BaseAdapter",
    "CoinGeckoAdapter",
    "BinanceAdapter",
]