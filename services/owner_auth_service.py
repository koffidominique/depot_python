"""Authentification locale du propriétaire (le PIN ne chiffre pas SQLite)."""
import re
import time

import bcrypt
from sqlalchemy import text
from models.owner_security import OwnerSecurity


class PinLocked(ValueError):
    def __init__(self, seconds):
        self.seconds = seconds
        super().__init__(f'Trop de tentatives. Réessayez dans {seconds} secondes.')


class OwnerAuthService:
    def __init__(self, session_factory, clock=time.time):
        self.session_factory = session_factory
        self.clock = clock

    @staticmethod
    def _validate(pin):
        if not isinstance(pin, str) or not re.fullmatch(r'[0-9]{6}', pin):
            raise ValueError('Le code PIN doit contenir exactement six chiffres.')

    @staticmethod
    def _lock(db):
        db.execute(text('BEGIN IMMEDIATE'))

    def is_configured(self):
        with self.session_factory() as db:
            row = db.get(OwnerSecurity, 1)
            return bool(row and row.pin_hash)

    def setup_pin(self, pin, confirmation):
        self._validate(pin)
        if pin != confirmation:
            raise ValueError('Les deux codes PIN ne correspondent pas.')
        hashed = bcrypt.hashpw(pin.encode('ascii'), bcrypt.gensalt()).decode('ascii')
        with self.session_factory() as db:
            self._lock(db)
            row = db.get(OwnerSecurity, 1)
            if row and row.pin_hash:
                raise ValueError('Un code PIN est déjà configuré.')
            if row is None:
                row = OwnerSecurity(id=1)
                db.add(row)
            row.pin_hash = hashed
            row.failed_attempts = 0
            row.locked_until = 0
            db.commit()

    def verify_pin(self, pin):
        self._validate(pin)
        with self.session_factory() as db:
            self._lock(db)
            row = db.get(OwnerSecurity, 1)
            if not row or not row.pin_hash:
                raise ValueError('Configurez d’abord votre code PIN.')
            now = int(self.clock())
            if row.locked_until > now:
                raise PinLocked(row.locked_until - now)
            if bcrypt.checkpw(pin.encode('ascii'), row.pin_hash.encode('ascii')):
                row.failed_attempts = 0
                row.locked_until = 0
                db.commit()
                return True
            row.failed_attempts += 1
            if row.failed_attempts >= 3:
                row.locked_until = now + min(300, 5 * 2 ** min(row.failed_attempts - 3, 6))
            db.commit()
            return False

    def change_pin(self, current, new, confirmation):
        self._validate(new)
        if new != confirmation:
            raise ValueError('Les deux nouveaux codes PIN ne correspondent pas.')
        if not self.verify_pin(current):
            raise ValueError('Code PIN actuel incorrect.')
        hashed = bcrypt.hashpw(new.encode('ascii'), bcrypt.gensalt()).decode('ascii')
        with self.session_factory() as db:
            self._lock(db)
            row = db.get(OwnerSecurity, 1)
            row.pin_hash = hashed
            db.commit()

    def get_inactivity_seconds(self):
        with self.session_factory() as db:
            row = db.get(OwnerSecurity, 1)
            return row.inactivity_seconds if row else 900

    def set_inactivity_seconds(self, seconds):
        if isinstance(seconds, bool) or not isinstance(seconds, int) or not 60 <= seconds <= 86400:
            raise ValueError('Le délai doit être compris entre 1 et 1 440 minutes.')
        with self.session_factory() as db:
            self._lock(db)
            row = db.get(OwnerSecurity, 1)
            if not row or not row.pin_hash:
                raise ValueError('Configurez d’abord votre code PIN.')
            row.inactivity_seconds = seconds
            db.commit()
