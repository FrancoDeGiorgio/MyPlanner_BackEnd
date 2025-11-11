"""
Base Repository - Classe astratta per repository con funzionalità comuni.

Fornisce metodi CRUD base e utility condivise che possono essere
ereditati dai repository specifici, riducendo la duplicazione di codice.

Design Pattern: Repository Pattern + Template Method
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from uuid import UUID
import psycopg2
from fastapi import HTTPException, status


# Type variable per genericità
T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Repository base astratto con operazioni CRUD comuni.
    
    Questa classe fornisce un'interfaccia comune per tutti i repository,
    implementando pattern e utility condivise. I repository concreti
    ereditano da questa classe e implementano i metodi specifici.
    
    Generic Type T: Rappresenta il tipo di entità gestita dal repository
    
    Benefits:
    - DRY: Evita duplicazione di codice tra repository
    - Consistency: Interfaccia uniforme per tutti i repository
    - Maintainability: Modifiche alle utility si propagano a tutti i repository
    
    Note:
        - Questa è una classe astratta, non può essere istanziata direttamente
        - I metodi astratti DEVONO essere implementati dalle sottoclassi
        - I metodi concreti possono essere sovrascritti se necessario
    """
    
    def __init__(self, table_name: str):
        """
        Inizializza il repository con il nome della tabella.
        
        Args:
            table_name: Nome della tabella nel database
        """
        self.table_name = table_name
    
    @abstractmethod
    def _row_to_dict(self, row: tuple, cursor_description: Any) -> Dict[str, Any]:
        """
        Converte una riga del database in un dizionario.
        
        Metodo astratto che deve essere implementato da ogni repository
        per mappare le colonne specifiche della tabella.
        
        Args:
            row: Tupla con i valori della riga
            cursor_description: Descrizione delle colonne dal cursor
        
        Returns:
            Dict: Dizionario con i dati della riga
        
        Example:
            >>> def _row_to_dict(self, row, cursor_description):
            ...     return {
            ...         'id': row[0],
            ...         'name': row[1],
            ...         'created_at': row[2]
            ...     }
        """
        pass
    
    def _execute_query(
        self,
        conn: psycopg2.extensions.connection,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Optional[Any]:
        """
        Esegue una query SQL con gestione errori standardizzata.
        
        Utility method per eseguire query con:
        - Gestione automatica del cursor
        - Commit automatico
        - Error handling standardizzato
        
        Args:
            conn: Connessione al database
            query: Query SQL da eseguire
            params: Parametri per prepared statement
            fetch_one: Se True, restituisce una riga
            fetch_all: Se True, restituisce tutte le righe
        
        Returns:
            Optional: Risultato della query o None
        
        Raises:
            HTTPException 500: In caso di errore database
        """
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                
                result = None
                if fetch_one:
                    result = cur.fetchone()
                elif fetch_all:
                    result = cur.fetchall()
                
                conn.commit()
                return result
                
        except Exception as e:
            conn.rollback()
            print(f"Database error in {self.table_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database operation failed on {self.table_name}"
            )
    
    def _check_exists(
        self,
        conn: psycopg2.extensions.connection,
        field: str,
        value: Any
    ) -> bool:
        """
        Verifica se esiste un record con un determinato valore.
        
        Utility per verificare l'esistenza di un record prima di
        operazioni come INSERT o UPDATE.
        
        Args:
            conn: Connessione al database
            field: Nome del campo da verificare
            value: Valore da cercare
        
        Returns:
            bool: True se esiste, False altrimenti
        
        Example:
            >>> if self._check_exists(conn, 'email', 'user@example.com'):
            ...     raise AlreadyExistsError("Email già registrata")
        """
        query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {field} = %s"
        result = self._execute_query(conn, query, (value,), fetch_one=True)
        return result[0] > 0 if result else False
    
    def _build_update_query(
        self,
        updates: Dict[str, Any],
        where_clause: str
    ) -> tuple:
        """
        Costruisce una query UPDATE dinamica da un dizionario.
        
        Utility per generare query UPDATE basate su quali campi
        devono essere aggiornati, evitando di dover scrivere
        query diverse per ogni combinazione di campi.
        
        Args:
            updates: Dizionario {campo: valore} dei campi da aggiornare
            where_clause: Clausola WHERE (es. "id = %s")
        
        Returns:
            tuple: (query_sql, parametri)
        
        Example:
            >>> updates = {'name': 'Mario', 'email': 'mario@example.com'}
            >>> query, params = self._build_update_query(updates, "id = %s")
            >>> print(query)
            UPDATE users SET name = %s, email = %s WHERE id = %s
            >>> print(params)
            ('Mario', 'mario@example.com', user_id)
        """
        if not updates:
            raise ValueError("Updates dictionary cannot be empty")
        
        # Costruisce "field1 = %s, field2 = %s, ..."
        set_clause = ", ".join(f"{field} = %s" for field in updates.keys())
        
        # Query completa
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}"
        
        # Parametri nell'ordine corretto
        params = tuple(updates.values())
        
        return query, params
    
    def count(self, conn: psycopg2.extensions.connection) -> int:
        """
        Conta il numero totale di record nella tabella.
        
        Args:
            conn: Connessione al database
        
        Returns:
            int: Numero di record
        
        Example:
            >>> total_users = user_repository.count(conn)
            >>> print(f"Totale utenti: {total_users}")
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        result = self._execute_query(conn, query, fetch_one=True)
        return result[0] if result else 0

