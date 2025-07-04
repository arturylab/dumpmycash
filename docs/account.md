# Account Management

Manage financial accounts and track balances.

## Features

- **Create Accounts**: Add new financial accounts with custom colors
- **View Accounts**: Monitor individual account balances in a grid layout
- **Account Colors**: Visual identification with custom color selection
- **Quick Transfers**: Transfer money between accounts seamlessly
- **Chart Visualization**: Balance distribution pie chart
- **Recent Transfers**: View and manage transfer history

## Account Properties

- **Name**: User-defined account identifier
- **Balance**: Current account balance (automatically calculated)
- **Color**: Hex color code for visual identification (#FF6384 default)
- **Created Date**: Account creation timestamp

## Operations

### Create Account
- Set account name
- Choose identification color from predefined palette
- Set initial balance (creates initial deposit transaction if > 0)

### View Accounts
- Grid layout showing all user accounts
- Display current balances with color coding
- Quick action buttons for transfers and new accounts

### Account Management
- Edit account name, balance, and color
- Delete accounts (restrictions apply)
- Balance adjustments create corresponding transactions

### Transfers
- Quick transfer between accounts
- Transfer history with reverse functionality
- Automatic balance updates

## Restrictions

- Accounts with associated transactions or transfers cannot be deleted
- Must remove or reassign all related transactions first
- Balance adjustments create audit trail transactions
