import unicodedata
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.models.person import Person
from app.models.site import Site
from app.models.user import User
from app.schemas.person import PersonCreate, PersonUpdate, PersonMerge
from app.core.security import hash_password
from app.services.audit_service import AuditService

import logging

logger = logging.getLogger(__name__)


class PersonService:
    """Service per la gestione delle persone."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        site_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> tuple[list[dict], int]:
        """
        Recupera tutte le persone con filtri opzionali.
        Ritorna (lista_persone_con_sede, totale)
        """
        query = select(Person, Site.name.label('site_name'), User.username.label('linked_username')).outerjoin(Site, Person.site_id == Site.id).outerjoin(User, User.person_id == Person.id)

        # Filtro attivo/inattivo
        if is_active is not None:
            query = query.where(Person.is_active == is_active)

        # Filtro per sede
        if site_id is not None:
            query = query.where(Person.site_id == site_id)

        # Ricerca per nome, cognome o email
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Person.first_name.ilike(search_term),
                    Person.last_name.ilike(search_term),
                    Person.email.ilike(search_term)
                )
            )

        # Conta totale (prima di paginazione)
        total = db.scalar(select(func.count()).select_from(query.subquery()))

        # Paginazione e ordinamento
        query = query.order_by(Person.last_name, Person.first_name).offset(skip).limit(limit)
        results = db.execute(query).all()

        # Converti in dizionari con site_name
        people_with_site = []
        for person, site_name, linked_username in results:
            person_dict = {
                "id": person.id,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "site_id": person.site_id,
                "email": person.email,
                "extension": person.extension,
                "mobile_phone": person.mobile_phone,
                "notes": person.notes,
                "is_active": person.is_active,
                "created_at": person.created_at,
                "updated_at": person.updated_at,
                "site_name": site_name,
                "linked_username": linked_username
            }
            people_with_site.append(person_dict)

        return people_with_site, total or 0

    @staticmethod
    def get_by_id(db: Session, person_id: int) -> Optional[Person]:
        """Recupera una persona per ID."""
        return db.scalar(select(Person).where(Person.id == person_id))

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Person]:
        """Recupera una persona per email (case-insensitive)."""
        return db.scalar(select(Person).where(func.lower(Person.email) == email.lower()))

    @staticmethod
    def create(db: Session, person_data: PersonCreate) -> Person:
        """Crea una nuova persona e automaticamente un utente associato."""
        # Verifica duplicati email
        if person_data.email:
            existing = PersonService.get_by_email(db, person_data.email)
            if existing:
                raise ValueError(f"Esiste già una persona con email '{person_data.email}'")

        # Crea la persona
        person = Person(**person_data.model_dump())
        db.add(person)
        db.flush()  # Flush per ottenere person.id senza commit

        # Always create associated user when creating a person
        def _make_username(first: str, last: str) -> str:
            """Generate clean username from first_name + last_name: nome.cognome (lowercase, no accents, no apostrophes, no internal spaces)."""
            def _clean(s: str) -> str:
                if not s:
                    return ""
                # Remove accents (NFD decompose, strip combining chars)
                s = unicodedata.normalize("NFD", s)
                s = "".join(c for c in s if unicodedata.category(c) != "Mn")
                # Remove apostrophes and quotes
                s = s.replace("'", "").replace("'", "").replace("`", "")
                # Remove internal spaces and lowercase
                s = "".join(s.split()).lower()
                return s

            first_clean = _clean(first or "")
            last_clean = _clean(last or "")
            if not first_clean and not last_clean:
                base = "user"
            elif not last_clean:
                base = first_clean
            elif not first_clean:
                base = last_clean
            else:
                base = f"{first_clean}.{last_clean}"
            return base

        base_username = _make_username(person.first_name, person.last_name)
        username = base_username
        suffix = 0
        while db.scalar(select(User).where(User.username == username)):
            username = f"{base_username}{suffix}"
            suffix += 1

        user = User(
            username=username,
            password_hash=hash_password("Password123!"),
            role="user",
            person_id=person.id,
            is_active=True
        )
        db.add(user)

        db.commit()
        db.refresh(person)

        # Audit log
        try:
            AuditService.log_action(
                db=db,
                action="CREATE",
                entity_type="person",
                entity_id=person.id,
                details=f"Creata persona {person.first_name} {person.last_name}",
                new_value={
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                    "email": person.email,
                    "site_id": person.site_id
                }
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        return person

    @staticmethod
    def update(db: Session, person_id: int, person_data: PersonUpdate) -> Optional[Person]:
        """Aggiorna una persona esistente."""
        person = PersonService.get_by_id(db, person_id)
        if not person:
            return None

        # Salva old values per audit
        old_value = {
            "first_name": person.first_name,
            "last_name": person.last_name,
            "email": person.email,
            "site_id": person.site_id
        }

        # Verifica duplicati email se viene modificata
        if person_data.email and person_data.email != person.email:
            existing = PersonService.get_by_email(db, person_data.email)
            if existing and existing.id != person_id:
                raise ValueError(f"Esiste già una persona con email '{person_data.email}'")

        # Aggiorna solo i campi forniti
        update_data = person_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)

        db.commit()

        # Audit log
        try:
            new_value = {
                "first_name": person.first_name,
                "last_name": person.last_name,
                "email": person.email,
                "site_id": person.site_id
            }
            AuditService.log_action(
                db=db,
                action="UPDATE",
                entity_type="person",
                entity_id=person.id,
                details=f"Aggiornata persona {person.first_name} {person.last_name}",
                old_value=old_value,
                new_value=new_value
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        db.refresh(person)
        return person

    @staticmethod
    def delete(db: Session, person_id: int) -> bool:
        """Disattiva una persona (soft delete: is_active=False)."""
        person = PersonService.get_by_id(db, person_id)
        if not person:
            return False

        # Salva dati per audit
        person_name = f"{person.first_name} {person.last_name}"

        person.is_active = False
        
        # Disattiva anche l'utente associato se esiste
        user = db.scalar(select(User).where(User.person_id == person_id))
        if user:
            user.is_active = False
        
        db.commit()

        # Audit log
        try:
            AuditService.log_action(
                db=db,
                action="DELETE",
                entity_type="person",
                entity_id=person.id,
                details=f"Persona disattivata (soft delete): {person_name}",
                old_value={"is_active": True}
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        return True

    @staticmethod
    def hard_delete(db: Session, person_id: int) -> bool:
        """Elimina definitivamente una persona dal database."""
        person = PersonService.get_by_id(db, person_id)
        if not person:
            return False

        # Elimina anche l'utente associato se esiste
        user = db.scalar(select(User).where(User.person_id == person_id))
        if user:
            db.delete(user)

        db.delete(person)
        db.commit()
        return True

    @staticmethod
    def merge(db: Session, merge_data: PersonMerge) -> Person:
        """
        Unisce due persone: sposta i dati dalla source alla target e disattiva la source.
        """
        source = PersonService.get_by_id(db, merge_data.source_id)
        target = PersonService.get_by_id(db, merge_data.target_id)

        if not source or not target:
            raise ValueError("Una o entrambe le persone non esistono")

        if source.id == target.id:
            raise ValueError("Non è possibile unire una persona con se stessa")

        # Unisci le note se richiesto
        if merge_data.merge_notes and source.notes:
            if target.notes:
                target.notes = f"{target.notes}\n\n--- Unito da {source.full_name} ---\n{source.notes}"
            else:
                target.notes = f"--- Unito da {source.full_name} ---\n{source.notes}"

        # Copia dati mancanti dalla source alla target
        if not target.email and source.email:
            target.email = source.email
        if not target.extension and source.extension:
            target.extension = source.extension
        if not target.mobile_phone and source.mobile_phone:
            target.mobile_phone = source.mobile_phone
        if not target.site_id and source.site_id:
            target.site_id = source.site_id

        # Disattiva la persona source
        source.is_active = False
        
        # Disattiva anche l'utente source se esiste
        source_user = db.scalar(select(User).where(User.person_id == source.id))
        if source_user:
            source_user.is_active = False

        db.commit()
        db.refresh(target)
        return target
