#!/usr/bin/env python3
"""
Script para restaurar datos básicos después de la limpieza accidental.
Este script crea un usuario principal con algunas categorías y cuentas básicas.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Category, Account, Transaction
from app.config import Config
from datetime import datetime, timedelta
import random

def restore_basic_data():
    """Restaurar datos básicos para continuar trabajando."""
    print("🔄 Restaurando datos básicos...")
    
    # Crear la aplicación
    app = create_app(Config)
    
    with app.app_context():
        # Crear usuario principal
        user = User(
            username='admin',
            email='admin@dumpmycash.com'
        )
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        print(f"✅ Usuario principal creado: {user.username}")
        
        # Crear categorías básicas de ingresos
        income_categories = [
            {'name': 'Salario', 'emoji': '💰'},
            {'name': 'Freelance', 'emoji': '💼'},
            {'name': 'Inversiones', 'emoji': '📈'},
            {'name': 'Otros Ingresos', 'emoji': '💵'},
        ]
        
        # Crear categorías básicas de gastos
        expense_categories = [
            {'name': 'Comida', 'emoji': '🍕'},
            {'name': 'Transporte', 'emoji': '🚗'},
            {'name': 'Entretenimiento', 'emoji': '🎬'},
            {'name': 'Compras', 'emoji': '🛒'},
            {'name': 'Servicios', 'emoji': '💡'},
            {'name': 'Salud', 'emoji': '🏥'},
            {'name': 'Educación', 'emoji': '📚'},
            {'name': 'Otros Gastos', 'emoji': '💸'},
        ]
        
        created_categories = {}
        
        # Crear categorías de ingresos
        for cat_data in income_categories:
            category = Category(
                name=cat_data['name'],
                type='income',
                unicode_emoji=cat_data['emoji'],
                user_id=user.id
            )
            db.session.add(category)
            created_categories[cat_data['name']] = category
        
        # Crear categorías de gastos
        for cat_data in expense_categories:
            category = Category(
                name=cat_data['name'],
                type='expense',
                unicode_emoji=cat_data['emoji'],
                user_id=user.id
            )
            db.session.add(category)
            created_categories[cat_data['name']] = category
        
        db.session.commit()
        print(f"✅ {len(income_categories)} categorías de ingresos creadas")
        print(f"✅ {len(expense_categories)} categorías de gastos creadas")
        
        # Crear cuentas básicas
        accounts_data = [
            {'name': 'Cuenta Corriente', 'balance': 5000.0, 'color': '#2563eb'},
            {'name': 'Cuenta de Ahorros', 'balance': 15000.0, 'color': '#16a34a'},
            {'name': 'Tarjeta de Crédito', 'balance': -2500.0, 'color': '#dc2626'},
            {'name': 'Efectivo', 'balance': 500.0, 'color': '#ca8a04'},
        ]
        
        created_accounts = {}
        for acc_data in accounts_data:
            account = Account(
                name=acc_data['name'],
                user_id=user.id,
                balance=acc_data['balance'],
                color=acc_data['color']
            )
            db.session.add(account)
            created_accounts[acc_data['name']] = account
        
        db.session.commit()
        print(f"✅ {len(accounts_data)} cuentas creadas")
        
        # Crear algunas transacciones de ejemplo
        now = datetime.now()
        sample_transactions = [
            {
                'amount': 3000.0,
                'description': 'Salario mensual',
                'account': 'Cuenta Corriente',
                'category': 'Salario',
                'date': now.replace(day=1, hour=9)
            },
            {
                'amount': -450.0,
                'description': 'Supermercado semanal',
                'account': 'Cuenta Corriente',
                'category': 'Comida',
                'date': now - timedelta(days=2)
            },
            {
                'amount': -80.0,
                'description': 'Gasolina',
                'account': 'Cuenta Corriente',
                'category': 'Transporte',
                'date': now - timedelta(days=3)
            },
            {
                'amount': -120.0,
                'description': 'Cena con amigos',
                'account': 'Cuenta Corriente',
                'category': 'Entretenimiento',
                'date': now - timedelta(days=1)
            },
            {
                'amount': 500.0,
                'description': 'Trabajo freelance',
                'account': 'Cuenta Corriente',
                'category': 'Freelance',
                'date': now - timedelta(days=5)
            },
            {
                'amount': -200.0,
                'description': 'Compras varias',
                'account': 'Tarjeta de Crédito',
                'category': 'Compras',
                'date': now - timedelta(days=4)
            },
        ]
        
        for trans_data in sample_transactions:
            transaction = Transaction(
                amount=trans_data['amount'],
                description=trans_data['description'],
                account_id=created_accounts[trans_data['account']].id,
                category_id=created_categories[trans_data['category']].id,
                user_id=user.id,
                date=trans_data['date']
            )
            db.session.add(transaction)
        
        db.session.commit()
        print(f"✅ {len(sample_transactions)} transacciones de ejemplo creadas")
        
        print("\n" + "="*60)
        print("🎉 DATOS BÁSICOS RESTAURADOS EXITOSAMENTE")
        print("="*60)
        print(f"👤 Usuario: {user.username}")
        print(f"📧 Email: {user.email}")
        print(f"🔑 Password: admin123")
        print(f"📁 Categorías: {len(created_categories)}")
        print(f"💳 Cuentas: {len(created_accounts)}")
        print(f"💰 Transacciones: {len(sample_transactions)}")
        print("\n📋 CUENTAS CREADAS:")
        for name, account in created_accounts.items():
            balance_str = f"${account.balance:,.2f}" if account.balance >= 0 else f"-${abs(account.balance):,.2f}"
            print(f"   💳 {name}: {balance_str}")
        print("\n🌐 Puedes acceder en: http://127.0.0.1:5005")
        print("="*60)

if __name__ == "__main__":
    restore_basic_data()
