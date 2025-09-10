import urllib.parse

import httpx
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed


class WeatherService:

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def get_weather(city: str) -> tuple[int, str]:

        city_encoded = urllib.parse.quote(city)
        url = f"https://wttr.in/{city_encoded}?format=j1"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                current = data['current_condition'][0]
                temp = current['temp_C']
                description = current['weatherDesc'][0]['value']
                return temp, description

        except RetryError:
            return -999, f"Не получилось получить погоду для города '{city}', попробуйте позже."
        except Exception:
            return -999, f"Произошла ошибка, обратитесь к разработчику."


class CurrencyService:

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def get_rates(base: str, symbols: str) -> list[float]:
        base = base.lower()
        url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base.lower()}.json"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                rates = data.get(base, {})
                lines = []
                for symbol in symbols.split(","):
                    val = rates.get(symbol.lower())
                    lines.append(f"{symbol}: {val if val is not None else 'нет данных'}")
                return lines

        except RetryError:
            return [-1]
        except Exception:
            return [-1]
