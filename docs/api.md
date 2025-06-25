# API Reference

## Authentication

All endpoints require user authentication via session-based login.

## User Management

### Login
- **POST** `/auth/login`
- **Body**: `email`, `password`, `remember` (optional)
- **Response**: Redirect to dashboard or error

### Register  
- **POST** `/auth/register`
- **Body**: `username`, `email`, `password`
- **Response**: User creation confirmation

### Logout
- **POST** `/auth/logout`
- **Response**: Session termination

## Account Operations

### List Accounts
- **GET** `/account`
- **Response**: User accounts with balances

### Create Account
- **POST** `/account/create`
- **Body**: `name`, `color`, `initial_balance`

### Update Account
- **POST** `/account/update/<id>`
- **Body**: `name`, `color`

## Transaction Operations

### List Transactions
- **GET** `/transactions`
- **Query**: `page`, `category`, `account`, `date_filter`

### Create Transaction
- **POST** `/transactions/add`
- **Body**: `amount`, `description`, `account_id`, `category_id`, `date`

### Update Transaction
- **POST** `/transactions/edit/<id>`
- **Body**: `amount`, `description`, `account_id`, `category_id`, `date`

### Delete Transaction
- **POST** `/transactions/delete/<id>`

## Category Operations

### List Categories
- **GET** `/categories`
- **Response**: User categories grouped by type

### Create Category
- **POST** `/categories/add`
- **Body**: `name`, `type`, `unicode_emoji`

### Update Category
- **POST** `/categories/edit/<id>`
- **Body**: `name`, `unicode_emoji`

### Delete Category
- **POST** `/categories/delete/<id>`

## Transfer Operations

### Create Transfer
- **POST** `/transactions/transfer`
- **Body**: `amount`, `from_account_id`, `to_account_id`, `description`, `date`

## Response Formats

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed",
  "data": {}
}
```

### Error Response
```json
{
  "status": "error", 
  "message": "Error description",
  "errors": {}
}
```
