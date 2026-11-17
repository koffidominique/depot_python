from database import init_db, SessionLocal
from services.auth_service import AuthService
from services.product_service import ProductService
from models.product import Category
from decimal import Decimal


def initialize_database():
    init_db()
    db = SessionLocal()
    
    try:
        auth_service = AuthService(db)
        if not auth_service.get_user_by_username('admin'):
            auth_service.create_user(
                username='admin',
                password='admin123',
                full_name='Administrateur',
                role='admin'
            )
            print("Utilisateur admin créé avec succès (identifiant: admin, mot de passe: admin123)")
        
        product_service = ProductService(db)
        categories = [
            "Eaux minérales",
            "Sodas",
            "Jus de fruits",
            "Bières",
            "Vins",
            "Spiritueux",
            "Boissons énergisantes",
            "Snacks"
        ]
        
        for cat_name in categories:
            existing = db.query(Category).filter(Category.name == cat_name).first()
            if not existing:
                product_service.create_category(name=cat_name, description=f"Catégorie {cat_name}")
                print(f"Catégorie {cat_name} créée avec succès")
        
        db.commit()
        print("Base de données initialisée avec succès!")
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de l'initialisation: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()