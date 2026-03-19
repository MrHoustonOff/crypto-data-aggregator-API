import asyncio
import httpx
from .adapters import BinanceAdapter, CoinGeckoAdapter


class ParserService:
    def __init__(self, adapters: list, tickers: list):
        self.adapters = adapters # [BinanceAdapter(), CoinGeckoAdapter()]
        self.tickers_to_track = tickers # ["BTC", "ETH", "DOGE", "SOL", "BNB"]

    async def fetch_all_prices(self) -> dict[str, float]:
        """
        Собирает цены со всех бирж и сливает их в один словарь.
        """
        all_exchanges = {}
        async with httpx.AsyncClient() as cl:
            get_price_coroutines = [
                ad.get_price(cl, self.tickers_to_track) for ad in self.adapters
            ]

            result = await asyncio.gather(*get_price_coroutines, return_exceptions=True)
        
        for res in result:
            if not isinstance(res, Exception):
                all_exchanges.update(res)
            else:
                #TODO обработка ошибок адаптера.
                print(f"Adapter Error: {res}")
        
        return all_exchanges

if __name__ == "__main__":
    tmp = ParserService(
        adapters=[BinanceAdapter(), CoinGeckoAdapter()],
        tickers=["BTC", "ETH", "DOGE", "SOL", "BNB"]
        )
    print(asyncio.run(tmp.fetch_all_prices()))
