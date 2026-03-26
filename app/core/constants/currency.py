from enum import Enum

class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    UAH = "UAH"
    GBP = "GBP"
    PLN = "PLN"

CURRENCY_DATA = {
    CurrencyCode.USD: {"name": "US Dollar", "symbol": "$"},
    CurrencyCode.EUR: {"name": "Euro", "symbol": "€"},
    CurrencyCode.UAH: {"name": "Ukrainian Hryvnia", "symbol": "₴"},
    CurrencyCode.GBP: {"name": "British Pound", "symbol": "£"},
    CurrencyCode.PLN: {"name": "Polish Zloty", "symbol": "zł"},
}