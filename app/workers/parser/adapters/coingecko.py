from .base import BaseAdapter

class CoinGeckoAdapter(BaseAdapter):
    
    @property
    def mapping(self) -> dict[str, str]:
        return {"BTC": "bitcoin", "ETH": "ethereum"}

    def prepare_request_url(self, tickers: list[str]) -> str:
        mapping_gen = (res for ticker in tickers if (res := self.mapping.get(ticker)) is not None)
        tickers_param = ",".join(mapping_gen)

        if tickers_param:
            return f"https://api.coingecko.com/api/v3/simple/price?ids={tickers_param}&vs_currencies=usd"
        return ""

    def normalize_response(self, response: dict) -> dict:
        normalize_output = dict()
        for response_key, response_value in response.items():
            normalize_output[self.reverse_mapping[response_key]] = float(response_value["usd"])
        return normalize_output