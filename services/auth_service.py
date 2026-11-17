from sqlalchemy.orm import Session
from models.user import User, Role, Permission
from typing import Optional, List
import bcrypt
from datetime import datetime

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user or not user.is_active:
            return None
        if self.verify_password(password, user.password_hash):
            return user
        return None
    
    def authenticate_by_pin(self, pin: str) -> Optional[User]:
        if len(pin) != 4 or not pin.isdigit():
            return None
        user = self.db.query(User).filter(User.pin_code == pin, User.is_active == True).first()
        return user
    
    def update_pin_code(self, user_id: int, new_pin: str) -> bool:
        if len(new_pin) != 4 or not new_pin.isdigit():
            return False
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        user.pin_code = new_pin
        user.updated_at = datetime.now()
        self.db.commit()
        return True
    
    def create_user(self, username: str, password: str, full_name: str, role_id: int, email: str = None) -> User:
        password_hash = self.hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            role_id=role_id,
            email=email,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_all_roles(self) -> List[Role]:
        return self.db.query(Role).all()
    
    def create_role(self, name: str, description: str = None) -> Role:
        role = Role(name=name, description=description)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def initialize_default_roles(self):
        default_roles = [
            ('Administrateur', 'Accès complet à toutes les fonctionnalités'),
            ('Gérant', 'Gestion générale et validation'),
            ('Caissier', 'Gestion de la caisse et ventes'),
            ('Magasinier', 'Gestion des stocks et réceptions'),
            ('Commercial', 'Gestion des clients et ventes'),
            ('Livreur', 'Gestion des livraisons'),
            ('Comptable', 'Gestion comptable et rapports')
        ]
        
        for role_name, description in default_roles:
            existing_role = self.db.query(Role).filter(Role.name == role_name).first()
            if not existing_role:
                self.create_role(role_name, description)