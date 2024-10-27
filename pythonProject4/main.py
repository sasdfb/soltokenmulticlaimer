import asyncio
import base58
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Processed
from solana.rpc.types import TxOpts
from spl.token.instructions import get_associated_token_address, create_associated_token_account
from colorama import Fore, Style

# Константы программ
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPu1xSph7v3fGaUthoxC7rsZGTmQPey5YRcWL")
SYS_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")


def load_private_keys(file_path):
    """Загружает приватные ключи из файла."""
    with open(file_path, "r") as f:
        private_keys = [line.strip() for line in f if line.strip()]
    print(f"{Fore.GREEN}🔑 Загружено {len(private_keys)} приватных ключей из файла {file_path}{Style.RESET_ALL}")
    return private_keys


async def get_or_create_associated_token_account(client, payer, owner, mint):
    """Получает или создаёт ассоциированный токеновый аккаунт."""
    associated_token_address = get_associated_token_address(owner, mint)
    print(f"{Fore.CYAN}🔍 Проверка существования ассоциированного токенового аккаунта для {owner} и mint {mint}{Style.RESET_ALL}")

    # Проверяем, существует ли токеновый аккаунт
    account_info = await client.get_account_info(associated_token_address, commitment=Confirmed)
    if account_info.value is None:
        print(f"{Fore.YELLOW}⚠️ Ассоциированный токеновый аккаунт для {owner} не найден. Создаётся новый аккаунт.{Style.RESET_ALL}")
        create_instruction = create_associated_token_account(payer=payer, owner=owner, mint=mint)
        return associated_token_address, [create_instruction]

    print(f"{Fore.GREEN}✅ Ассоциированный токеновый аккаунт для {owner} найден: {associated_token_address}{Style.RESET_ALL}")
    return associated_token_address, []


async def send_tokens(file_path, token_mint_str, to_address_str):
    """Отправляет токены с нескольких кошельков на указанный адрес."""
    async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
        print(f"{Fore.BLUE}🌐 Подключение к клиенту Solana...{Style.RESET_ALL}")
        private_keys = load_private_keys(file_path)
        to_pubkey = Pubkey.from_string(to_address_str)
        token_mint = Pubkey.from_string(token_mint_str)

        # Получаем количество десятичных знаков токена
        print(f"{Fore.CYAN}ℹ️ Получение информации о токене mint: {token_mint}{Style.RESET_ALL}")
        token_info = await client.get_token_supply(token_mint, commitment=Confirmed)
        decimals = int(token_info.value.decimals)
        print(f"{Fore.MAGENTA}🔢 Decimals for token: {decimals}{Style.RESET_ALL}")

        for pk in private_keys:
            print(f"{Fore.YELLOW}🔒 Обработка приватного ключа: {pk[:5]}... (скрыто для безопасности){Style.RESET_ALL}")
            # Создаём Keypair из приватного ключа
            secret_key = base58.b58decode(pk)
            from_account = Keypair.from_bytes(secret_key)
            wallet_pubkey = from_account.pubkey()
            print(f"{Fore.GREEN}👛 Обрабатывается кошелёк: {wallet_pubkey}{Style.RESET_ALL}")

            # Получаем или создаём ассоциированный токеновый аккаунт отправителя
            associated_token_address, create_account_instructions = await get_or_create_associated_token_account(
                client, wallet_pubkey, wallet_pubkey, token_mint
            )

            # Получаем или создаём ассоциированный токеновый аккаунт получателя
            destination_associated_address, create_dest_instructions = await get_or_create_associated_token_account(
                client, wallet_pubkey, to_pubkey, token_mint
            )

            # Получаем баланс токенов
            print(f"{Fore.BLUE}💰 Получение баланса токенов для аккаунта: {associated_token_address}{Style.RESET_ALL}")
            balance_resp = await client.get_token_account_balance(associated_token_address, commitment=Confirmed)
            if balance_resp.value is None:
                print(f"{Fore.RED}⚠️ Баланс токенов на {wallet_pubkey} равен 0.{Style.RESET_ALL}")
                continue

            amount = float(balance_resp.value.amount) / (10 ** balance_resp.value.decimals)
            print(f"{Fore.MAGENTA}💸 Баланс токенов на кошельке {wallet_pubkey}: {amount}{Style.RESET_ALL}")

            if amount > 0:
                print(f"{Fore.YELLOW}✉️ Отправка {amount} токенов с {wallet_pubkey} на {to_pubkey}...{Style.RESET_ALL}")
                # Создаём инструкцию перевода токенов
                transfer_amount = int(amount * (10 ** decimals))
                print(f"{Fore.CYAN}📝 Создание инструкции для перевода {transfer_amount} токенов (в минимальных единицах){Style.RESET_ALL}")
                # Проверка типов аккаунтов перед созданием инструкции
                print(f"{Fore.BLUE}🔍 Тип аккаунта отправителя: {type(associated_token_address)}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}🔍 Тип аккаунта получателя: {type(destination_associated_address)}{Style.RESET_ALL}")
                transfer_instruction = Instruction(
                    program_id=TOKEN_PROGRAM_ID,
                    accounts=[
                        AccountMeta(pubkey=associated_token_address, is_signer=False, is_writable=True),
                        AccountMeta(pubkey=token_mint, is_signer=False, is_writable=False),
                        AccountMeta(pubkey=destination_associated_address, is_signer=False, is_writable=True),
                        AccountMeta(pubkey=wallet_pubkey, is_signer=True, is_writable=True),
                    ],
                    data=bytes([12]) + transfer_amount.to_bytes(8, byteorder="little") + decimals.to_bytes(1, byteorder="little")
                )

                # Собираем все инструкции
                instructions = create_account_instructions + create_dest_instructions + [transfer_instruction]
                print(f"{Fore.GREEN}📜 Всего инструкций для выполнения: {len(instructions)}{Style.RESET_ALL}")

                # Получаем recent_blockhash
                print(f"{Fore.CYAN}🔄 Получение последнего блока...{Style.RESET_ALL}")
                latest_blockhash_resp = await client.get_latest_blockhash(commitment=Confirmed)
                recent_blockhash_value = latest_blockhash_resp.value.blockhash
                print(f"{Fore.MAGENTA}🆔 Получен recent_blockhash: {str(recent_blockhash_value)}{Style.RESET_ALL}")

                # Создаём объект Message с инструкциями
                print(f"{Fore.YELLOW}✉️ Создание сообщения с инструкциями...{Style.RESET_ALL}")
                message = Message(instructions)
                print(f"{Fore.BLUE}📋 Message Header: {message.header}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}📋 Account Keys: {message.account_keys}{Style.RESET_ALL}")

                # Создаём объект Transaction
                print(f"{Fore.CYAN}🛠️ Создание транзакции...{Style.RESET_ALL}")
                transaction = Transaction([from_account], message, recent_blockhash_value)

                # Подписываем транзакцию
                print(f"{Fore.YELLOW}✍️ Подписание транзакции...{Style.RESET_ALL}")
                transaction.sign([from_account], recent_blockhash_value)

                # Сериализуем транзакцию
                serialized_tx = bytes(transaction)
                print(f"{Fore.GREEN}🔏 Сериализованная транзакция: {serialized_tx.hex()[:10]}... (скрыто для безопасности){Style.RESET_ALL}")

                # Отправляем транзакцию
                try:
                    print(f"{Fore.CYAN}🚀 Отправка транзакции...{Style.RESET_ALL}")
                    response = await client.send_raw_transaction(serialized_tx, opts=TxOpts(skip_preflight=True, preflight_commitment=Processed))
                    print(f"{Fore.GREEN}✅ Транзакция завершена: {response}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}❌ Ошибка при отправке транзакции: {e}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}⚠️ Баланс токенов на {wallet_pubkey} равен 0.{Style.RESET_ALL}")

            # Добавляем задержку между транзакциями
            print(f"{Fore.YELLOW}⏳ Ожидание 5 секунд перед выполнением следующей транзакции...{Style.RESET_ALL}")
            await asyncio.sleep(5)


# Пример использования
if __name__ == "__main__":
    file_path = "private_keys.txt"  # Путь к файлу с приватными ключами
    token_mint = input("Введите адрес контракта токена: ")
    to_address = input("Введите адрес получателя: ")

    # Запуск асинхронной функции
    asyncio.run(send_tokens(file_path, token_mint, to_address))
