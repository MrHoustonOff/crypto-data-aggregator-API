from base import BaseAdapter
import json


class BinanceAdapter(BaseAdapter):

    @property
    def mapping(self) -> dict[str, str]:
        return {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}

    def prepare_request_url(self, tickers: list[str]) -> str:
        mapping_gen = (
            res for ticker in tickers if (res := self.mapping.get(ticker)) is not None
        )
        tickers_param = json.dumps(list(mapping_gen))

        if tickers_param != "[]":
            return (
                f"https://api.binance.com/api/v3/ticker/price?symbols={tickers_param}"
            )
        return ""

    def normalize_response(self, response: dict | list) -> dict:
        normalize_output = dict()

        for response_dict in response:
            response_ticker = response_dict.get("symbol")
            response_value = response_dict.get("price")

            normalize_output[self.reverse_mapping[response_ticker]] = response_value

        return normalize_output
