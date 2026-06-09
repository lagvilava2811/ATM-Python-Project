# ATM Simulation

Console ATM simulation with PIN login, balance management, transfers, and transaction history.

## Run

```powershell
python main.py
```

Data is saved in `data/accounts.json`.

Existing accounts with plain-text `pin` values are automatically converted to `pin_hash` on startup.

## Features

- Login with account number and PIN
- Account lock after 3 failed login attempts
- Check balance
- Deposit money
- Withdraw money (with confirmation)
- Transfer money to another account
- View transaction history
- Change PIN
- Create new account

## Test User

| Field          | Value  |
|----------------|--------|
| Account number | 1001   |
| PIN            | 1234   |
| Balance        | 500.00 GEL |

## Data and Security

- Account data is stored locally in `data/accounts.json`.
- PINs are stored as SHA-256 hashes, not as plain text.
- Locked accounts cannot be unlocked from the current version.
- This is an educational console project, not a production banking system.

## Example Session

```
=== Welcome to ATM ===
1. Login
2. Create New Account
3. Exit
Choose: 1

=== Login ===
Account number: 1001
PIN: 1234
Welcome, Demo User!

=== ATM ===
1. Show balance
2. Deposit money
3. Withdraw money
4. Transfer money
5. Show history
6. Change PIN
7. Exit
```
