from sqlalchemy.orm import Session
from models.user import User, Role, Permission
from typing import Optional, List
import bcrypt
from datetime import datetime
from utils.permissions import ROLE_PERMISSIONS, PermissionEnum

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
        raise RuntimeError("L'authentification multi-utilisateur par PIN est désactivée.")

    def update_pin_code(self, user_id: int, new_pin: str) -> bool:
        raise RuntimeError("Utilisez la configuration du PIN propriétaire.")

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
                role = self.create_role(role_name, description)
                self._assign_default_permissions(role)
    
    def _assign_default_permissions(self, role: Role):
        role_name = role.name
        if role_name in ROLE_PERMISSIONS:
            for perm_name in ROLE_PERMISSIONS[role_name]:
                existing_perm = self.db.query(Permission).filter(
                    Permission.role_id == role.id,
                    Permission.permission_name == perm_name
                ).first()
                if not existing_perm:
                    perm = Permission(role_id=role.id, permission_name=perm_name)
                    self.db.add(perm)
            self.db.commit()
    
    def user_has_permission(self, user: User, permission: PermissionEnum) -> bool:
        if not user or not user.role:
            return False
        user_permissions = self.db.query(Permission).filter(Permission.role_id == user.role.id).all()
        user_perm_names = [p.permission_name for p in user_permissions]
        return permission.value in user_perm_names
    
    def get_user_permissions(self, user: User) -> List[str]:
        if not user or not user.role:
            return []
        permissions = self.db.query(Permission).filter(Permission.role_id == user.role.id).all()
        return [p.permission_name for p in permissions]
    
    def add_permission_to_role(self, role_id: int, permission_name: str) -> bool:
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return False
        existing_perm = self.db.query(Permission).filter(
            Permission.role_id == role_id,
            Permission.permission_name == permission_name
        ).first()
        if existing_perm:
            return True
        perm = Permission(role_id=role_id, permission_name=permission_name)
        self.db.add(perm)
        self.db.commit()
        return True
    
    def remove_permission_from_role(self, role_id: int, permission_name: str) -> bool:
        perm = self.db.query(Permission).filter(
            Permission.role_id == role_id,
            Permission.permission_name == permission_name
        ).first()
        if not perm:
            return False
        self.db.delete(perm)
        self.db.commit()
        return True
    
    def get_role_permissions(self, role_id: int) -> List[Permission]:
        return self.db.query(Permission).filter(Permission.role_id == role_id).all()