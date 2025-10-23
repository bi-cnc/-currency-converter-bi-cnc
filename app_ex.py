import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import flag

class Converter:
    def __init__(self, date_str, max_attempts=10):
        # Nastavíme původní datum zadané uživatelem
        self.original_date = date_str
        self.max_attempts = max_attempts
        self.rates = self.get_rates()

    def get_rates(self):
        # Převod stringu data zpět na objekt datetime
        current_date = datetime.strptime(self.original_date, "%d.%m.%Y")
        
        # Logika pro opakované pokusy, dokud nejsou nalezena data
        for attempt in range(self.max_attempts):
            # Formátování URL pro aktuální pokusné datum
            date_to_fetch = current_date.strftime("%d.%m.%Y")
            self.url = f'https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/index.html?date={date_to_fetch}'
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            
            try:
                response = requests.get(self.url, headers=headers, timeout=5)
                # Použijeme stavy 4xx/5xx jako chybu
                response.raise_for_status() 
                soup = BeautifulSoup(response.text, 'html.parser')
                
                tables = soup.find_all('table')

                if tables:
                    # ✅ ÚSPĚCH: Tabulka nalezena. Kurzy stáhneme a rovnou vrátíme.
                    # POZNÁMKA: Původní st.info zpráva byla ZDE a byla odstraněna.
                    
                    table = tables[0]
                    rows = table.find_all('tr')
                    rates = {'CZK': (1, 1)}  # Přidání kurzu CZK k sobě
                    
                    for row in rows[1:]:
                        data = row.find_all('td')
                        if len(data) >= 5:
                            country = data[0].text
                            currency = data[1].text
                            
                            try:
                                # Odstranění neměnných mezer a převod na číslo
                                quantity = float(data[2].text.replace('\xa0', '').strip())
                            except ValueError:
                                quantity = 1.0

                            code = data[3].text
                            
                            try:
                                # Ošetření čárky jako oddělovače desetinných míst
                                rate = float(data[4].text.replace('\xa0', '').replace(',', '.').strip())
                            except ValueError:
                                continue
                            
                            rates[code] = (rate, quantity)
                    
                    return rates # Úspěšné vrácení kurzů
                
            except requests.exceptions.RequestException as e:
                # Chyba při připojení nebo HTTP chyba
                # Tuto varovnou zprávu (st.warning) pro interní debug můžete také odstranit, 
                # pokud nechcete, aby se objevovala při každé chybě připojení.
                st.warning(f"Chyba při stahování dat pro {date_to_fetch}. Zkouším předchozí den.") 
            except IndexError:
                # Tabulka nebyla nalezena (o víkendu/svátku nebo budoucí datum)
                pass # Pokračujeme na další den
            
            # Posuneme datum o jeden den zpět
            current_date -= timedelta(days=1)
            
        # Pokud se po X pokusech data nenajdou
        st.error(f"Nepodařilo se stáhnout žádné kurzy po {self.max_attempts} pokusech, počínaje {self.original_date}.")
        return {'CZK': (1, 1)}

    def convert(self, amount, from_currency, to_currency):
        to_czk_rate, to_czk_quantity = self.rates.get(from_currency, (0, 1))
        to_currency_rate, to_currency_quantity = self.rates.get(to_currency, (0, 1))

        if to_czk_rate == 0 or to_currency_rate == 0:
             return 0.0

        czk_amount = (amount / to_czk_quantity) * to_czk_rate
        converted_amount = (czk_amount / to_currency_rate) * to_currency_quantity
        return round(converted_amount, 2)

# Zobrazení názvu aplikace
st.title('Převodník měn – měnová kalkulačka')

# Dictionary mapping currency codes to country codes.
currency_to_country = {
    "CZK": "CZ", "USD": "US", "EUR": "EU", "AUD": "AU", "BRL": "BR", "BGN": "BG",
    "CNY": "CN", "DKK": "DK", "PHP": "PH", "HKD": "HK", "INR": "IN", "IDR": "ID",
    "ISK": "IS", "ILS": "IL", "JPY": "JP", "ZAR": "ZA", "CAD": "CA", "KRW": "KR",
    "HUF": "HU", "MYR": "MY", "MXN": "MX", "NOK": "NO", "NZD": "NZ", "PLN": "PL",
    "RON": "RO", "SGD": "SG", "SEK": "SE", "CHF": "CH", "THB": "TH", "TRY": "TR", "GBP": "GB",
}

def format_option(opt):
    country_code = currency_to_country.get(opt, "")
    flag_emoji = flag.flag(country_code) if country_code else ""
    return f"{flag_emoji} {opt}"

# Vytvoření vstupu pro datum
dnes = datetime.now()
date = st.date_input('**Vyber datum pro převod měn:**', value=dnes.date())

# Zde se inicializuje Converter s logikou pro opakované pokusy o stažení
converter = Converter(date.strftime("%d.%m.%Y"))

# Získání seznamu měn z právě stažených kurzů
currencies = list(converter.rates.keys())

# Vytvoření vstupů pro měny a množství
default_base = 'EUR' if 'EUR' in currencies else 'CZK'
default_target = 'CZK' if 'CZK' in currencies else list(currencies)[0]

base_currency = st.selectbox('**Vyberte základní měnu:**', currencies, index=currencies.index(default_base), format_func=format_option)
target_currency = st.selectbox('**Vyberte cílovou měnu:**', currencies, index=currencies.index(default_target), format_func=format_option)
amount = st.number_input('**Zadejte množství:**', value=1.0, min_value=0.01)


# Tlačítko pro přepočet
if st.button('Spočítat'):
    if base_currency != target_currency and len(converter.rates) > 1:
        # Výpočet převedeného množství
        converted_amount_float = converter.convert(amount, base_currency, target_currency)
        converted_amount = "{:,.2f}".format(converted_amount_float).replace(",", " ").replace(".", ",")

        # Zobrazení výsledku
        st.markdown(f'<div style="font-size: 15px; text-align: center;"><div style="background-color: #0078D4; padding: 10px; color: white; border-radius: 5px; display: inline-block;font-weight: bold;">{amount:.2f} {base_currency} = {converted_amount} {target_currency}</div></div>', unsafe_allow_html=True)
    elif len(converter.rates) <= 1:
        st.error('Nelze provést převod, protože se nepodařilo stáhnout kurzy jiných měn než CZK.')
    else:
        st.warning('Základní a cílová měna nemohou být stejné.')
