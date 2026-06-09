
import hashlib
import json
import random
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
DEFAULT_ACCOUNTS = {
    "1001": {
        "owner": "Demo User",
        "pin_hash": "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4",
        "balance": 500.0,
        "locked": False,
        "transactions": ["Initial balance: 500.00 GEL"],
    }
}

def ensure_storage():
    DATA_DIR.mkdir(exist_ok=True)
    if not ACCOUNTS_FILE.exists():
        save_accounts(DEFAULT_ACCOUNTS)


def load_accounts():
    try:
        accounts = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        accounts = DEFAULT_ACCOUNTS.copy()

    if migrate_plain_pins(accounts):
        save_accounts(accounts)
    return accounts


def save_accounts(accounts):
    try:
        ACCOUNTS_FILE.write_text(json.dumps(accounts, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, IOError, PermissionError) as e:
        print(f"Error: Could not save accounts. {e}")


def hash_pin(pin):
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def verify_pin(account, pin):
    return account.get("pin_hash") == hash_pin(pin)


def migrate_plain_pins(accounts):
    changed = False
    for account in accounts.values():
        if "pin" in account and "pin_hash" not in account:
            account["pin_hash"] = hash_pin(account["pin"])
            del account["pin"]
            changed = True

        if "locked" not in account:
            account["locked"] = False
            changed = True
    return changed


def generate_account_number(accounts):
    while True:
        number = str(random.randint(100000, 999999))
        if number not in accounts:
            return number


def read_money(prompt):
    while True:
        value = input(prompt).strip()
        if "." in value and len(value.split(".", 1)[1]) > 2:
            print("Amount can have at most 2 decimal places.")
            continue

        try:
            amount = round(float(value), 2)
        except ValueError:
            print("Error: enter a valid amount.")
            continue
        if amount <= 0:
            print("Amount must be at least 0.01.")
            continue
        return amount


def add_transaction(account, text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    account.setdefault("transactions", []).append(f"{timestamp} | {text}")


def login(accounts):
    print("\n=== Login ===")
    
    account_number = input("Account number: ").strip()
    
    if not account_number.isdigit():
        print("Error: account number must contain only digits.")
        return None

    account = accounts.get(account_number)
    if not account:
        print("Account not found.")
        return None

    if account.get("locked"):
        print("This account is locked. Please contact support.")
        return None

    for attempt in range(3):
        pin = input("PIN: ").strip()

        if len(pin) != 4 or not pin.isdigit():
            print("Error: PIN must be exactly 4 digits.")
            remaining = 2 - attempt
            if remaining > 0:
                print(f"Attempts left: {remaining}")
            else:
                print("This was your last attempt.")
            continue

        if verify_pin(account, pin):
            print(f"Welcome, {account['owner']}!")
            return account_number

        print("Wrong PIN.")
        remaining = 2 - attempt
        if remaining > 0:
            print(f"Attempts left: {remaining}")
        else:
            print("This was your last attempt.")

    account["locked"] = True
    save_accounts(accounts)
    print("Too many failed attempts. Account is now locked.")
    return None


def create_account(accounts):
    print("\n=== Create New Account ===")

    owner = input("Full name: ").strip()
    if not owner:
        print("Name cannot be empty.")
        return None

    while True:
        pin = input("Create PIN (4 digits): ").strip()
        if len(pin) == 4 and pin.isdigit():
            confirm = input("Confirm PIN: ").strip()
            if pin == confirm:
                break
            print("PINs do not match.")
        else:
            print("PIN must be exactly 4 digits.")

    initial = read_money("Initial deposit amount: ")
    account_number = generate_account_number(accounts)

    accounts[account_number] = {
        "owner": owner,
        "pin_hash": hash_pin(pin),
        "balance": initial,
        "locked": False,
        "transactions": [f"Initial balance: {initial:.2f} GEL"],
    }

    save_accounts(accounts)
    print(f"\nAccount created successfully!")
    print(f"Your account number: {account_number}")
    return account_number


def change_pin(account, accounts):
    print("\n=== Change PIN ===")

    old_pin = input("Enter current PIN: ").strip()
    if not verify_pin(account, old_pin):
        print("Incorrect PIN.")
        return

    while True:
        new_pin = input("New PIN (4 digits): ").strip()
        if len(new_pin) == 4 and new_pin.isdigit():
            confirm = input("Confirm new PIN: ").strip()
            if new_pin == confirm:
                account["pin_hash"] = hash_pin(new_pin)
                add_transaction(account, "PIN changed")
                save_accounts(accounts)
                print("PIN changed successfully!")
                return
            print("PINs do not match.")
        else:
            print("PIN must be exactly 4 digits.")


def show_balance(account):
    print(f"Your balance is: {account['balance']:.2f} GEL")


def deposit(account):
    amount = read_money("Deposit amount: ")
    account["balance"] = round(account["balance"] + amount, 2)
    add_transaction(account, f"Deposit: +{amount:.2f} GEL")
    print("Money was deposited successfully.")


def withdraw(account):
    amount = read_money("Withdrawal amount: ")
    if amount > account["balance"]:
        print("Not enough balance.")
        return

    confirm = input(f"Are you sure you want to withdraw {amount:.2f} GEL? (y/n): ").strip().lower()
    if confirm != "y":
        print("Withdrawal cancelled.")
        return

    account["balance"] = round(account["balance"] - amount, 2)
    add_transaction(account, f"Withdrawal: -{amount:.2f} GEL")
    print("Money was withdrawn successfully.")


def transfer_money(account, accounts, from_number):
    print("\n=== Transfer Money ===")

    to_number = input("Enter recipient account number: ").strip()

    if not to_number.isdigit():
        print("Error: account number must contain only digits.")
        return

    if to_number == from_number:
        print("Error: cannot transfer to your own account.")
        return

    recipient = accounts.get(to_number)
    if not recipient:
        print("Recipient account not found.")
        return

    amount = read_money("Transfer amount: ")
    if amount > account["balance"]:
        print("Not enough balance.")
        return

    confirm = input(f"Transfer {amount:.2f} GEL to {recipient['owner']}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Transfer cancelled.")
        return

    account["balance"] = round(account["balance"] - amount, 2)
    recipient["balance"] = round(recipient["balance"] + amount, 2)

    add_transaction(account, f"Transfer to {to_number}: -{amount:.2f} GEL")
    add_transaction(recipient, f"Transfer from {from_number}: +{amount:.2f} GEL")

    save_accounts(accounts)
    print(f"Successfully transferred {amount:.2f} GEL to {recipient['owner']}.")


def show_transactions(account):
    print("\n--- Transaction History ---")
    for transaction in account.get("transactions", []):
        print(transaction)


def atm_menu(accounts, account_number):
    try:
        account = accounts[account_number]
    except KeyError:
        print("Error: Account not found.")
        return

    while True:
        print("\n=== ATM ===")
        print("1. Show balance")
        print("2. Deposit money")
        print("3. Withdraw money")
        print("4. Transfer money")
        print("5. Show history")
        print("6. Change PIN")
        print("7. Exit")

        choice = input("Choose: ").strip()
        if choice == "1":
            show_balance(account)
        elif choice == "2":
            deposit(account)
            save_accounts(accounts)
        elif choice == "3":
            withdraw(account)
            save_accounts(accounts)
        elif choice == "4":
            transfer_money(account, accounts, account_number)
        elif choice == "5":
            show_transactions(account)
        elif choice == "6":
            change_pin(account, accounts)
        elif choice == "7":
            print("Session ended.")
            break
        else:
            print("Error: choose 1-7.")


def main():
    ensure_storage()
    accounts = load_accounts()

    while True:
        print("\n=== Welcome to ATM ===")
        print("1. Login")
        print("2. Create New Account")
        print("3. Exit")

        choice = input("Choose: ").strip()
        if choice == "1":
            account_number = login(accounts)
            if account_number:
                atm_menu(accounts, account_number)
        elif choice == "2":
            create_account(accounts)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Error: choose 1-3.")


if __name__ == "__main__":
    main()
