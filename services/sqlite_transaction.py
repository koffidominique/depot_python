"""Verrou d'écriture SQLite pour les opérations métier autonomes."""
from functools import wraps
from sqlalchemy import text


def lock_for_write(db):
    """Réserve SQLite avant les lectures métier sans écraser des changements en attente."""
    if db.new or db.dirty or db.deleted:
        raise ValueError('Terminez les modifications en cours avant cette opération.')
    connection = db.connection()
    raw = connection.connection.driver_connection
    if raw.in_transaction:
        raise ValueError('Une transaction d’écriture est déjà en cours.')
    connection.execute(text('BEGIN IMMEDIATE'))
    db.expire_all()


def locked_write(method):
    """Verrouille avant les contrôles et annule toute opération refusée."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        lock_for_write(self.db)
        try:
            return method(self, *args, **kwargs)
        except Exception:
            self.db.rollback()
            raise
    return wrapped
