import requests
import random
import time


class ExchangeRequest:
    def __init__(self):
        self.total_attempts = 15
        self.binance_api_urls = [
            "https://api.binance.com/",
            "https://api1.binance.com/",
            "https://api2.binance.com/",
            "https://api3.binance.com/",
            "https://api4.binance.com/"
        ]

    def get_binance_ticker_price(self, ticker: str):
        url = f"{random.choice(self.binance_api_urls)}api/v3/ticker/price?symbol={ticker}"
        session = requests.Session()
        headers = {
            "Accept": "application/json",

        }

        try:
            response = session.get(url, headers=headers)
            # response.raise_for_status()
            if 'price' in response.json():
                session.close()
                return response.json()['price']
            else:
                session.close()
                return None
        except requests.exceptions.RequestException as e:
            session.close()
            return None

    def get_bybit_ticker_price(self, ticker: str):
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={ticker}"
        session = requests.Session()
        headers = {
            "Accept": "application/json",

        }

        try:
            response = requests.get(url, headers=headers)
            if 'result' in response.json():
                return response.json()['result']['list'][0]['lastPrice']
            else:
                session.close()
                return None
        except requests.exceptions.RequestException as e:
            session.close()
            return None

    def get_ticker_price(self, ticker: str):
        success = False
        attempts = 0

        while not success and attempts < self.total_attempts:
            attempts += 1
            try:
                price = 0
                if attempts < 8:
                    price = float(self.get_binance_ticker_price(ticker))

                if 8 <= attempts < 16:
                    price = float(self.get_bybit_ticker_price(ticker))

                if price and float(price) > 0:
                    return price

            except Exception as e:
                if attempts >= 16:
                    print(f"Помилка отримання ціни токена: {ticker} - {e}")
                    raise Exception
                pass

            time.sleep(2)
