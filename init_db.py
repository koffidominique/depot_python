from database import engine, SessionLocal, Base
from services.auth_service import AuthService
from services.product_service import ProductService
from models.product import Category
from models.user import Role
import models
from decimal import Decimal
from logger import log_error, log_business, log_audit


def initialize_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        auth_service = AuthService(db)
        
        auth_service.initialize_default_roles()
        log_business("Initialisation rôles", "Rôles et permissions initialisés avec succès")
        
        if not auth_service.get_user_by_username('admin'):
            admin_role = db.query(Role).filter(Role.name == 'Administrateur').first()
            auth_service.create_user(
                username='admin',
                password='admin123',
                full_name='Administrateur',
                role_id=admin_role.id,
                email='admin@depotpro.ci'
            )
            log_business("Création utilisateur", "Utilisateur admin créé avec succès (identifiant: admin, mot de passe: admin123, PIN: 0000)")
        
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
                log_business("Création catégorie", f"Catégorie {cat_name} créée avec succès")
        
        db.commit()
        log_business("Initialisation base de données", "Base de données initialisée avec succès!")
        
    except Exception as e:
        db.rollback()
        log_error(f"Erreur lors de l'initialisation: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()