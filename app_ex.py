import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import flag

class Converter:
    def __init__(self, date):
        self.url = f'https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/index.html?date={date}'
        self.rates = self.get_rates()

    def get_rates(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find_all('table')[0] 
        rows = table.find_all('tr')
        rates = {'CZK': (1, 1)}  # Add a rate for CZK to itself
        for row in rows[1:]:
            data = row.find_all('td')
            country = data[0].text
            currency = data[1].text
            quantity = float(data[2].text)
            code = data[3].text
            rate = float(data[4].text.replace(',', '.'))
            rates[code] = (rate, quantity)
        return rates

    def convert(self, amount, from_currency, to_currency):
        to_czk_rate, to_czk_quantity = self.rates[from_currency]
        to_currency_rate, to_currency_quantity = self.rates[to_currency]
        czk_amount = (amount / to_czk_quantity) * to_czk_rate
        converted_amount = (czk_amount / to_currency_rate) * to_currency_quantity
        # Zaokrouhlení na 2 desetinná místa
        return round(converted_amount, 2)

# Zobrazení názvu aplikace
st.title('Převodník měn – měnová kalkulačka')

# Initiate converter with selected date
converter = Converter("15.06.2023")

# Získání seznamu měn
currencies = list(converter.rates.keys())

# Dictionary mapping currency codes to country codes.
currency_to_country = {
    "CZK": "CZ",
    "USD": "US",
    "EUR": "EU",
    "AUD": "AU",
    "BRL": "BR",
    "BGN": "BG",
    "CNY": "CN",
    "DKK": "DK",
    "PHP": "PH",
    "HKD": "HK",
    "INR": "IN",
    "IDR": "ID",
    "ISK": "IS",
    "ILS": "IL",
    "JPY": "JP",
    "ZAR": "ZA",
    "CAD": "CA",
    "KRW": "KR",
    "HUF": "HU",
    "MYR": "MY",
    "MXN": "MX",
    "NOK": "NO",
    "NZD": "NZ",
    "PLN": "PL",
    "RON": "RO",
    "SGD": "SG",
    "SEK": "SE",
    "CHF": "CH",
    "THB": "TH",
    "TRY": "TR",
    "GBP": "GB",
    # Add more currencies and their corresponding country codes here.
}

def format_option(opt):
    # Convert the country code to a flag emoji using the flag library.
    country_code = currency_to_country.get(opt, "")
    flag_emoji = flag.flag(country_code) if country_code else ""
    # Return the option (currency code) prefixed with the flag emoji.
    return f"{flag_emoji} {opt}"

# Vytvoření vstupu pro základní měnu
base_currency = st.selectbox('**Vyberte základní měnu:**', currencies, index=currencies.index('EUR'), format_func=format_option)

# Vytvoření vstupu pro cílovou měnu
target_currency = st.selectbox('**Vyberte cílovou měnu:**', currencies, index=currencies.index('CZK'), format_func=format_option)

# Vytvoření vstupu pro množství
amount = st.number_input('**Zadejte množství:**', value=1)

# Vytvoření vstupu pro datum
dnes = datetime.now()
max_date = dnes.date()
date = st.date_input('**Vyber datum pro převod měn:**', value=max_date, max_value=max_date)

# Update converter with selected date
converter = Converter(date.strftime("%d.%m.%Y"))


# Tlačítko pro přepočet
if st.button('Spočítat'):
    # Kontrola, zda jsou základní a cílová měna různé
    if base_currency != target_currency:
        # Výpočet převedeného množství
        converted_amount = "{:,.2f}".format(converter.convert(amount, base_currency, target_currency)).replace(",", " ").replace(".", ",")

        # Zobrazení výsledku
        st.markdown(f'<div style="font-size: 15px; text-align: center;"><div style="background-color: #FA3A3C; padding: 10px; color: white; border-radius: 5px; display: inline-block;font-weight: bold;">{amount} {base_currency} = {converted_amount} {target_currency}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size: 15px; text-align: center;"><div style="background-color: #FA3A3C; padding: 10px; color: white; border-radius: 5px; display: inline-block;font-weight: bold;">Základní a cílová měna nemohou být stejné.', unsafe_allow_html=True)
