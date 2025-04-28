import requests
import json

from web3 import Web3
from termcolor import colored

from config import account_file, proxy_file, MIN_BALANCE, FIND_ZERO_BALANCE_KEY
from utils import get_pexchanges_price


# Читаємо файли
def load_accounts_from_file():
    with open(account_file, 'r') as file:
        return file.readlines()


try:
    accounts = load_accounts_from_file()
except FileNotFoundError:
    print(colored(f"Файл '{account_file}' не знайдено.", 'red'))
    exit()


def load_rpc_from_file():
    with open('rpcs.json', 'r') as file:
        return json.load(file)


try:
    rpcs = load_rpc_from_file()
except FileNotFoundError:
    print(colored("Файл 'rpcs.json' не знайдено.", 'red'))
    exit()


def load_proxies_from_file():
    with open(proxy_file, 'r') as file:
        return [line.strip() for line in file.readlines()]


try:
    proxies = load_proxies_from_file()
except FileNotFoundError:
    print(colored(f"Файл '{proxy_file}' не знайдено.", 'red'))
    exit()


def main_menu():
    if len(proxies) != len(accounts):
        print(colored("Немає достатньо проксі для всіх гаманців.", 'red'))
        print(f"Аккаунти: {len(accounts)}")
        print(f"Проксі:   {len(proxies)}")
        user_choice = input("Ви хочете продовжити? (y/n): ").strip().lower()
        if user_choice == 'n':
            print("Вихід з програми.")
            exit()

    print("Доступні RPC:")
    print("____________________________")
    for index, network in enumerate(rpcs.keys(), start=1):
        print(f"{index:>2}. {network.capitalize()}")

    while True:
        try:
            choice = int(input("Введіть номер пункту меню: "))
            print()
            if 1 <= choice <= len(rpcs):
                # Повертаємо список RPC для вибраної мережі
                return rpcs[list(rpcs.keys())[choice - 1]]
            elif choice == 0:
                print("Вихід з програми.")
                exit()
            else:
                print(colored("Неправильний вибір, спробуйте ще раз.", 'red'))
        except ValueError:
            print("Будь ласка, введіть номер пункту.")


selected_rpc_list = main_menu()
selected_rpc_index = 0
# Використовуємо перше посилання з списку
selected_rpc = selected_rpc_list[selected_rpc_index]
print(f"Ви вибрали RPC: {selected_rpc}")

web3 = Web3(Web3.HTTPProvider(selected_rpc))

chain_id = web3.eth.chain_id
network_names = {
    1: "Ethereum Mainnet (ETH)",
    10: "Optimism (ETH)",
    56: "Binance Smart Chain (BSC)",
    42161: "Arbitrum (ETH)",
    137: "Polygon (POL)",
    8453: "Base (ETH)",
    10143: "Monad Testnet (MON)",
    59144: "Linea (ETH)",
    534352: "Scroll (ETH)"
}

network_name = network_names.get(
    chain_id, "Unknown Network")  # Отримуємо назву мережі
print(f"\nCurrent Network {chain_id}: {network_name}\nФайл: {account_file}")

# Отримуємо актуальну ціну газу в wei
gas_price_gwei = web3.from_wei(web3.eth.gas_price, 'gwei')
print(f"Gas price: {gas_price_gwei}")

# ================♢================

token_map = {
    'binance': 'BNB',
    'gravity': 'G',
    'neon': 'NEON',
    'polygon': 'POL',
    'monad': 'MON',
    'ape': 'APE',
}
ticker = next((token for key, token in token_map.items()
               if key in selected_rpc), 'ETH')


def get_token_price(ticker):
    print(f"Ticker = {ticker}")
    try:
        price = get_pexchanges_price.ExchangeRequest()
        ticker = ticker.upper() + "USDT"
        binance_price = price.get_binance_ticker_price(ticker)
        bybit_price = price.get_bybit_ticker_price(ticker)

        if binance_price is not None:
            print(f"Price {ticker} on Binance: {binance_price}")
            price = float(binance_price)
            return price
        elif bybit_price is not None:
            print(f"Price {ticker} on Bybit: {bybit_price}")
            price = float(bybit_price)
            return price
    except requests.exceptions.RequestException as e:
        print(f"Помилка запиту: {e}")


price = get_token_price(ticker)

print(colored(f"Ціна {ticker} в USD: ${price}\n", 'cyan'))

# ==============

usd_summ = []  # весь баланс ETH
eth_summ = []  # весь баланс USDT
zero_wallet = []


def check_balance(wallet_address, price, proxy):
    wallet_address = Web3.to_checksum_address(wallet_address)
    session = requests.Session()
    session.proxies = {'http': proxy, 'https': proxy}

    balance_eth = round(web3.from_wei(
        web3.eth.get_balance(wallet_address), 'ether'), 4)

    eth_to_usd = round(float(balance_eth) * price, 2)
    usd_summ.append(eth_to_usd)
    eth_summ.append(balance_eth)
    if balance_eth < MIN_BALANCE:
        zero_wallet.append(wallet_address)
        print((f"{wallet_address} | " + colored(f"{balance_eth:>7.4f}", 'red') +
              f" {ticker.upper():<1} | $ {eth_to_usd:>6.2f} | TX: {web3.eth.get_transaction_count(wallet_address):<2}"))
    else:
        print(f"{wallet_address} | {balance_eth:>7.4f} {ticker.upper():<1} | $ {eth_to_usd:>6.2f} | TX: {web3.eth.get_transaction_count(wallet_address):<2}")


# Перевірка кожного аккаунта
try:
    for i, line in enumerate(accounts, start=0):
        account_info = line.strip().split(':')
        if len(account_info) != 2:
            print(f"❌ Неправильний формат рядка: {line.strip()}")
            continue

        wallet_address, _ = account_info
        print(f"{i + 1:>3}) ", end="")
        if i < len(proxies):
            try:
                check_balance(wallet_address, price, proxies[i])
            except Exception as e:
                print(f"Помилка при перевірці з {selected_rpc}: {e}")
                selected_rpc_index += 1
                if selected_rpc_index < len(selected_rpc_list):
                    selected_rpc = selected_rpc_list[selected_rpc_index]
                    print(f"Спробуємо наступний RPC: {selected_rpc}")
                    web3 = Web3(Web3.HTTPProvider(selected_rpc))
                else:
                    print(colored("Всі RPC не працюють. Завершення програми.", 'red'))
                    exit()
        else:
            print(colored("Немає достатньо проксі", 'red'))
except KeyboardInterrupt:
    print("\n❌ Відмінено користувачем.")
    exit()

# Виводимо результати
print(f"\nСумма: {sum(eth_summ)} ETH | $ {sum(usd_summ):.2f}")
print(f"Zero balance wallets(<{MIN_BALANCE}): {len(zero_wallet)}")

if FIND_ZERO_BALANCE_KEY:
    print("\n🔎 Пошук приватних ключів з нульовим балансом")
    # шукаємо приватні ключі для адрес, які мають нульовий баланс
    data = {line.split(":")[0]: line.split(":")[1] for line in accounts}

    found_keys = [
        f"{address}:{data[address]}" for address in zero_wallet if address in data]
    missing_addresses = [
        address for address in zero_wallet if address not in data]

    # Виводимо результати
    print("🔎 Знайдені приватні ключі:")
    print("".join(found_keys))

    print("\n🚫 Адреси без знайдених ключів:")
    print("\n".join(missing_addresses)
          if missing_addresses else "Всі адреси знайдені")

if __name__ == "__main__":
    exit()  # Закриваємо скрипт
