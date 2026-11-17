from sqlalchemy.orm import Session
from models.client import Client
from typing import List, Optional
from datetime import datetime

class ClientService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_clients(self, include_inactive: bool = False) -> List[Client]:
        query = self.db.query(Client)
        if not include_inactive:
            query = query.filter(Client.is_active == True)
        return query.all()
    
    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        return self.db.query(Client).filter(Client.id == client_id).first()
    
    def get_client_by_code(self, code: str) -> Optional[Client]:
        return self.db.query(Client).filter(Client.code == code).first()
    
    def search_clients(self, search_term: str) -> List[Client]:
        return self.db.query(Client).filter(
            Client.name.ilike(f"%{search_term}%") |
            Client.code.ilike(f"%{search_term}%") |
            Client.phone.ilike(f"%{search_term}%")
        ).all()
    
    def create_client(self, client_data: dict) -> Client:
        code = self._generate_client_code()
        client = Client(code=code, **client_data)
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client
    
    def update_client(self, client_id: int, client_data: dict) -> Optional[Client]:
        client = self.get_client_by_id(client_id)
        if not client:
            return None
        for key, value in client_data.items():
            setattr(client, key, value)
        self.db.commit()
        self.db.refresh(client)
        return client
    
    def deactivate_client(self, client_id: int) -> bool:
        client = self.get_client_by_id(client_id)
        if not client:
            return False
        client.is_active = False
        self.db.commit()
        return True
    
    def get_active_clients_count(self) -> int:
        return self.db.query(Client).filter(Client.is_active == True).count()
    
    def get_total_client_debts(self) -> float:
        clients = self.db.query(Client).filter(Client.is_active == True).all()
        total = sum(client.financial_balance for client in clients)
        return total
    
    def _generate_client_code(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"CLI-{timestamp}"