Solana Token Transfer Script

This Python script facilitates transferring SPL tokens from multiple Solana wallets to a specified recipient address. It utilizes the Solana blockchain and SPL Token Program, allowing users to send tokens from a list of wallet addresses efficiently. This script is ideal for users who need to distribute or consolidate tokens across multiple accounts.

Features

Connects to the Solana blockchain using the AsyncClient.

Loads multiple private keys from a specified file and transfers tokens from these wallets.

Automatically creates associated token accounts for both sender and recipient if they do not exist.

Supports SPL tokens and handles token transfers in an automated manner.

Adds a delay between transactions to prevent rate-limiting issues.

Uses color-coded logging for better readability during the transaction process.

Prerequisites

Python 3.8 or above.

Install required dependencies using pip:

pip install solders solana colorama

A Solana account with sufficient SOL to cover transaction fees.

Usage

Clone the repository.

Create a text file (e.g., private_keys.txt) containing the private keys of the wallets you want to use, one key per line.

Run the script:

python script.py

Enter the token mint address and the recipient's address when prompted.

Code Highlights

Uses solders and solana Python libraries for blockchain interaction.

Leverages colorama for color-coded log output, improving readability.

Includes functions to create associated token accounts if they don't already exist.

Implements a delay between each transaction to avoid overwhelming the network.

Example

Provide the path to the file containing private keys (private_keys.txt).

Input the token mint address and recipient wallet address when prompted.

The script will:

Check balances for each wallet.

Transfer tokens if a balance is available.

Log each step with clear, color-coded messages.

License

This project is licensed under the MIT License. See the LICENSE file for more details.
