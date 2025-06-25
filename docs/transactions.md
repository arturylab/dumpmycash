# Transactions

Record and manage financial transactions.

## Transaction Types

- **Income**: Money received (adds to account balance)
- **Expense**: Money spent (subtracts from account balance)

## Transaction Properties

- **Amount**: Transaction value (required)
- **Date**: Transaction date (defaults to current date)
- **Description**: Optional transaction details
- **Account**: Associated account (required)
- **Category**: Transaction category (required)

## Features

### Add Transaction
- Quick add via floating button
- Full form with all transaction details
- Real-time balance updates

### View Transactions
- Chronological transaction list
- Filter by date, category, or account
- Search by description

### Edit Transaction
- Modify existing transaction details
- Update amount, date, description, category
- Automatic balance recalculation

### Delete Transaction
- Remove unwanted transactions
- Automatic balance adjustment
- Confirmation required

## Quick Add
Fast transaction entry with:
- Amount input
- Category selection
- Account selection
- Optional description

## Transfers

Move money between accounts:
- **From Account**: Source account
- **To Account**: Destination account
- **Amount**: Transfer amount
- **Description**: Optional transfer notes

Transfer creates two linked transactions:
- Expense from source account
- Income to destination account
