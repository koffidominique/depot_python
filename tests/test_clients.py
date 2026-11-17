import pytest
from sqlalchemy.orm import Session
from services.client_service import ClientService


def test_create_client(db_session):
    client_service = ClientService(db_session)
    
    client = client_service.create_client({
        "name": "Test Client",
        "phone": "+22500000000",
        "email": "test@client.com",
        "address": "Test Address"
    })
    
    assert client is not None
    assert client.id is not None
    assert client.name == "Test Client"
    assert client.phone == "+22500000000"
    assert client.is_active == True


def test_client_validation(db_session):
    client_service = ClientService(db_session)
    
    with pytest.raises(Exception):
        client_service.create_client({
            "name": "",
            "phone": "invalid"
        })