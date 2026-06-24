from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.sim import Sim, SimStatus
from app.models.person import Person
from app.schemas.sim import SimCreate, SimUpdate, SimResponse, SimWithCredentials
from app.services.encryption_service import EncryptionService
from app.services.audit_service import AuditService
from fastapi import HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SimService:
    """Servizio per la gestione delle SIM"""
    
    @staticmethod
    def create_sim(db: Session, sim_data: SimCreate) -> Sim:
        """
        Crea una nuova SIM con PIN/PUK criptati
        
        Args:
            db: Sessione database
            sim_data: Dati SIM da creare
            
        Returns:
            SIM creata
            
        Raises:
            HTTPException: Se seriale o numero_telefono già esistono
        """
        # Verifica unicità seriale
        existing_seriale = db.query(Sim).filter(Sim.seriale == sim_data.seriale).first()
        if existing_seriale:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Seriale '{sim_data.seriale}' già esistente"
            )
        
        # Verifica unicità numero telefono
        existing_phone = db.query(Sim).filter(Sim.numero_telefono == sim_data.numero_telefono).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Numero telefono '{sim_data.numero_telefono}' già assegnato"
            )
        
        # Cripta PIN e PUK
        try:
            pin_criptato = EncryptionService.encrypt(sim_data.pin)
            puk_criptato = EncryptionService.encrypt(sim_data.puk)
        except Exception as e:
            logger.error(f"Errore criptazione PIN/PUK: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante la criptazione delle credenziali"
            )
        
        # Crea SIM
        db_sim = Sim(
            seriale=sim_data.seriale,
            operatore=sim_data.operatore,
            site_id=sim_data.site_id,
            numero_telefono=sim_data.numero_telefono,
            pin_criptato=pin_criptato,
            puk_criptato=puk_criptato,
            status=sim_data.status
        )
        
        db.add(db_sim)
        db.commit()
        db.refresh(db_sim)

        # Audit log
        try:
            AuditService.log_action(
                db=db,
                action="CREATE",
                entity_type="sim",
                entity_id=db_sim.id,
                details=f"Creata SIM {db_sim.numero_telefono} - {db_sim.operatore}",
                new_value={
                    "phone_number": db_sim.numero_telefono,
                    "carrier": db_sim.operatore,
                    "person_id": db_sim.person_id,
                    "site_id": db_sim.site_id
                }
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        logger.info(f"SIM creata: {db_sim.seriale} - {db_sim.numero_telefono}")
        return db_sim
    
    @staticmethod
    def get_sim_by_id(db: Session, sim_id: int) -> Optional[Sim]:
        """Ottiene una SIM per ID"""
        return db.query(Sim).filter(Sim.id == sim_id).first()
    
    @staticmethod
    def get_sim_by_seriale(db: Session, seriale: str) -> Optional[Sim]:
        """Ottiene una SIM per seriale"""
        return db.query(Sim).filter(Sim.seriale == seriale).first()
    
    @classmethod
    def get_by_person_id(cls, db: Session, person_id: int) -> Optional[Sim]:
        """
        Recupera la SIM assegnata a una persona
        """
        return db.query(Sim).filter(
            Sim.person_id == person_id,
            Sim.status == SimStatus.assegnata,
            Sim.is_active == True
        ).first()
    
    @staticmethod
    def get_sims(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[SimStatus] = None,
        operatore: Optional[str] = None
    ) -> tuple[list[dict], int]:
        """
        Ottiene lista SIM con filtri e paginazione, includendo dati persona

        Args:
            db: Sessione database
            skip: Numero record da saltare
            limit: Numero massimo record da restituire
            search: Ricerca in seriale, numero_telefono, operatore
            status: Filtra per status
            operatore: Filtra per operatore

        Returns:
            Tupla (lista dict SIM con dati persona, totale)
        """
        from app.models.person import Person
        from sqlalchemy.orm import joinedload

        # Query con LEFT JOIN su people (joinedload evita N+1)
        query = db.query(Sim).outerjoin(Person, Sim.person_id == Person.id).options(
            joinedload(Sim.person)
        )

        # Filtro ricerca
        if search:
            search_filter = or_(
                Sim.seriale.ilike(f"%{search}%"),
                Sim.numero_telefono.ilike(f"%{search}%"),
                Sim.operatore.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # Filtro status
        if status:
            query = query.filter(Sim.status == status)

        # Filtro operatore
        if operatore:
            query = query.filter(Sim.operatore.ilike(f"%{operatore}%"))

        # Conta totale (prima di paginazione)
        total = query.count()

        # Applica paginazione e ordina per data creazione
        sims_with_person = query.order_by(Sim.created_at.desc()).offset(skip).limit(limit).all()

        # Costruisci lista di dict con dati persona
        result = []
        for sim in sims_with_person:
            sim_dict = {
                "id": sim.id,
                "seriale": sim.seriale,
                "operatore": sim.operatore,
                "site_id": sim.site_id,
                "numero_telefono": sim.numero_telefono,
                "person_id": sim.person_id,
                "status": sim.status,
                "created_at": sim.created_at,
                "updated_at": sim.updated_at,
                "is_active": sim.is_active,
                "person_first_name": sim.person.first_name if sim.person else None,
                "person_last_name": sim.person.last_name if sim.person else None,
            }
            result.append(sim_dict)

        return result, total
    
    @staticmethod
    def update_sim(db: Session, sim_id: int, sim_data: SimUpdate) -> Sim:
        """
        Aggiorna una SIM esistente
        
        Args:
            db: Sessione database
            sim_id: ID SIM da aggiornare
            sim_data: Dati da aggiornare
            
        Returns:
            SIM aggiornata
            
        Raises:
            HTTPException: Se SIM non trovata o vincoli violati
        """
        db_sim = SimService.get_sim_by_id(db, sim_id)
        if not db_sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SIM con ID {sim_id} non trovata"
            )

        # Salva old values per audit
        old_value = {
            "phone_number": db_sim.numero_telefono,
            "carrier": db_sim.operatore,
            "person_id": db_sim.person_id,
            "site_id": db_sim.site_id
        }

        # Verifica unicità seriale (se modificato)
        if sim_data.seriale and sim_data.seriale != db_sim.seriale:
            existing = db.query(Sim).filter(Sim.seriale == sim_data.seriale, Sim.id != sim_id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Seriale '{sim_data.seriale}' già esistente"
                )
            db_sim.seriale = sim_data.seriale
        
        # Verifica unicità numero telefono (se modificato)
        if sim_data.numero_telefono and sim_data.numero_telefono != db_sim.numero_telefono:
            existing = db.query(Sim).filter(Sim.numero_telefono == sim_data.numero_telefono, Sim.id != sim_id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Numero telefono '{sim_data.numero_telefono}' già assegnato"
                )
            
            # Salva vecchio numero prima di aggiornare
            old_phone = db_sim.numero_telefono
            db_sim.numero_telefono = sim_data.numero_telefono
            
            # Se la SIM è assegnata e cambio il numero, aggiorno anche people.mobile_phone
            if db_sim.status == SimStatus.assegnata:
                SimService._sync_phone_to_person(db, db_sim, old_phone)
        
        # Aggiorna altri campi
        if sim_data.operatore:
            db_sim.operatore = sim_data.operatore

        if sim_data.site_id is not None:
            db_sim.site_id = sim_data.site_id

        if sim_data.status:
            db_sim.status = sim_data.status
        
        # Aggiorna PIN/PUK se forniti (criptandoli)
        if sim_data.pin:
            try:
                db_sim.pin_criptato = EncryptionService.encrypt(sim_data.pin)
            except Exception as e:
                logger.error(f"Errore criptazione PIN: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Errore durante la criptazione del PIN"
                )
        
        if sim_data.puk:
            try:
                db_sim.puk_criptato = EncryptionService.encrypt(sim_data.puk)
            except Exception as e:
                logger.error(f"Errore criptazione PUK: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Errore durante la criptazione del PUK"
                )
        
        db.commit()

        # Audit log
        try:
            new_value = {
                "phone_number": db_sim.numero_telefono,
                "carrier": db_sim.operatore,
                "person_id": db_sim.person_id,
                "site_id": db_sim.site_id
            }
            AuditService.log_action(
                db=db,
                action="UPDATE",
                entity_type="sim",
                entity_id=db_sim.id,
                details=f"Aggiornata SIM {db_sim.numero_telefono}",
                old_value=old_value,
                new_value=new_value
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        db.refresh(db_sim)
        
        logger.info(f"SIM aggiornata: {db_sim.seriale}")
        return db_sim
    
    @staticmethod
    def delete_sim(db: Session, sim_id: int) -> bool:
        """
        Elimina una SIM
        
        Args:
            db: Sessione database
            sim_id: ID SIM da eliminare
            
        Returns:
            True se eliminata
            
        Raises:
            HTTPException: Se SIM non trovata o assegnata
        """
        db_sim = SimService.get_sim_by_id(db, sim_id)
        if not db_sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SIM con ID {sim_id} non trovata"
            )

        # Salva dati per audit
        phone_number = db_sim.numero_telefono

        # Non permettere eliminazione di SIM assegnata
        if db_sim.status == SimStatus.assegnata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossibile eliminare una SIM assegnata. Rimuovere prima l'assegnazione."
            )
        
        db.delete(db_sim)
        db.commit()

        # Audit log
        try:
            AuditService.log_action(
                db=db,
                action="DELETE",
                entity_type="sim",
                entity_id=db_sim.id,
                details=f"SIM disattivata (soft delete): {phone_number}",
                old_value={"is_active": True}
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        logger.info(f"SIM eliminata: {db_sim.seriale}")
        return True
    
    @staticmethod
    def get_sim_credentials(db: Session, sim_id: int) -> dict:
        """
        Ottiene le credenziali decriptate di una SIM (solo per admin)
        
        Args:
            db: Sessione database
            sim_id: ID SIM
            
        Returns:
            Dict con PIN e PUK decriptati
            
        Raises:
            HTTPException: Se SIM non trovata o errore decriptazione
        """
        db_sim = SimService.get_sim_by_id(db, sim_id)
        if not db_sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SIM con ID {sim_id} non trovata"
            )
        
        try:
            pin = EncryptionService.decrypt(db_sim.pin_criptato)
            puk = EncryptionService.decrypt(db_sim.puk_criptato)
        except Exception as e:
            logger.error(f"Errore decriptazione credenziali SIM {sim_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante la decriptazione delle credenziali"
            )
        
        return {"pin": pin, "puk": puk}
    
    @staticmethod
    def assign_sim_to_person(db: Session, sim_id: int, person_id: int) -> Sim:
        """
        Assegna una SIM a una persona e sincronizza people.mobile_phone
        
        Args:
            db: Sessione database
            sim_id: ID SIM da assegnare
            person_id: ID persona destinataria
            
        Returns:
            SIM aggiornata
            
        Raises:
            HTTPException: Se SIM/persona non trovate o SIM già assegnata
        """
        # Verifica SIM
        db_sim = SimService.get_sim_by_id(db, sim_id)
        if not db_sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SIM con ID {sim_id} non trovata"
            )
        
        if db_sim.status == SimStatus.assegnata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SIM {db_sim.seriale} già assegnata"
            )
        
        # Verifica persona
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona con ID {person_id} non trovata"
            )
        
        # Aggiorna status SIM
        db_sim.status = SimStatus.assegnata
        db_sim.person_id = person_id
        
        # Sincronizza numero telefono in people.mobile_phone
        person.mobile_phone = db_sim.numero_telefono
        
        db.commit()
        db.refresh(db_sim)
        db.refresh(person)
        
        logger.info(f"SIM {db_sim.seriale} assegnata a {person.first_name} {person.last_name}")
        return db_sim
    
    @staticmethod
    def unassign_sim(db: Session, sim_id: int, person_id: int) -> Sim:
        """
        Rimuove assegnazione SIM da una persona e pulisce people.mobile_phone
        
        Args:
            db: Sessione database
            sim_id: ID SIM da rimuovere
            person_id: ID persona
            
        Returns:
            SIM aggiornata
            
        Raises:
            HTTPException: Se SIM/persona non trovate
        """
        # Verifica SIM
        db_sim = SimService.get_sim_by_id(db, sim_id)
        if not db_sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SIM con ID {sim_id} non trovata"
            )
        
        # Verifica persona
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona con ID {person_id} non trovata"
            )
        
        # Aggiorna status SIM
        db_sim.status = SimStatus.disponibile
        db_sim.person_id = None
        
        # Pulisci numero telefono in people.mobile_phone SOLO se corrisponde a questa SIM
        if person.mobile_phone == db_sim.numero_telefono:
            person.mobile_phone = None
        
        db.commit()
        db.refresh(db_sim)
        db.refresh(person)
        
        logger.info(f"SIM {db_sim.seriale} rimossa da {person.first_name} {person.last_name}")
        return db_sim
    
    @staticmethod
    def _sync_phone_to_person(db: Session, sim: Sim, old_phone: Optional[str] = None):
        """
        Metodo interno per sincronizzare numero telefono SIM con people.mobile_phone
        (usato quando si modifica il numero di una SIM già assegnata)
        
        Args:
            db: Sessione database
            sim: SIM con il nuovo numero
            old_phone: Vecchio numero telefono (se None, usa sim.numero_telefono)
        """
        # Trova la persona che ha il vecchio numero nel campo mobile_phone
        search_phone = old_phone if old_phone else sim.numero_telefono
        person = db.query(Person).filter(Person.mobile_phone == search_phone).first()
        if person:
            # Aggiorna con il nuovo numero
            person.mobile_phone = sim.numero_telefono
            db.commit()
