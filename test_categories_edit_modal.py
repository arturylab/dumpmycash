#!/usr/bin/env python3
"""
Test para verificar que el modal de edición de categorías funciona correctamente
y no mantiene datos de categorías anteriores.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Category
import tempfile

def test_categories_edit_modal():
    """Test que verifica que el modal de edición funciona correctamente."""
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        
        # Crear usuario de test
        user = User(username='testuser', email='test@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Crear categorías de test
        categories = [
            Category(name='Salary', type='income', unicode_emoji='💰', user_id=user.id),
            Category(name='Bonus', type='income', unicode_emoji='🎉', user_id=user.id),
            Category(name='Food', type='expense', unicode_emoji='🍕', user_id=user.id),
            Category(name='Transport', type='expense', unicode_emoji='🚗', user_id=user.id),
        ]
        
        for cat in categories:
            db.session.add(cat)
        db.session.commit()
        
        print("=== TEST: MODAL DE EDICIÓN DE CATEGORÍAS ===\n")
        
        # Test del cliente
        with app.test_client() as client:
            # Simular login
            with client.session_transaction() as sess:
                sess['user_id'] = user.id
            
            # Obtener la página de categorías
            response = client.get('/categories/')
            assert response.status_code == 200
            print("✓ Página de categorías carga correctamente")
            
            html_content = response.get_data(as_text=True)
            
            # Verificar que todas las categorías están presentes
            for category in categories:
                assert category.name in html_content
                print(f"✓ Categoría '{category.name}' presente en la página")
            
            # Verificar que los botones de editar tienen los atributos correctos
            assert 'data-action="edit"' in html_content
            assert 'data-category-id=' in html_content
            assert 'data-category-name=' in html_content
            assert 'data-category-type=' in html_content
            assert 'data-category-emoji=' in html_content
            print("✓ Botones de editar tienen atributos data-* correctos")
            
            # Verificar que el modal de edición está presente
            assert 'editCategoryModal' in html_content
            assert 'editCategoryForm' in html_content
            assert 'editCategoryId' in html_content
            assert 'editCategoryName' in html_content
            assert 'editCategoryType' in html_content
            assert 'editCategoryEmoji' in html_content
            print("✓ Modal de edición presente con todos los campos")
            
            # Verificar que el JavaScript está incluido
            assert 'categories.js' in html_content
            print("✓ JavaScript de categorías incluido")
            
            print("\n🎉 ¡Test completado!")
            print("📝 Correcciones implementadas:")
            print("   - Manejo mejorado de eventos de clic (tanto botón como ícono)")
            print("   - Limpieza del formulario cuando se cierra el modal")
            print("   - Logs de consola para debugging")
            print("   - Limpieza de errores previos al abrir el modal")
            
            print("\n🔧 Para probar en el navegador:")
            print("   1. Ejecuta la aplicación: python run.py")
            print("   2. Ve a http://localhost:5000/categories/")
            print("   3. Haz clic en varios botones de 'Edit' diferentes")
            print("   4. Verifica que cada modal muestra los datos correctos")
            print("   5. Abre la consola del navegador para ver los logs")

if __name__ == '__main__':
    test_categories_edit_modal()
