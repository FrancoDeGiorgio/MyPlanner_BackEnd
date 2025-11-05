"""
Repository Layer per il dominio Tasks.

Responsabile dell'accesso ai dati per la tabella 'tasks'.
Usa il decorator @with_rls_context per applicare automaticamente
Row-Level Security su tutte le operazioni.
"""
from typing import List, Optional, Dict
from uuid import UUID
import psycopg2
from fastapi import HTTPException, status

from core.decorators import with_rls_context


class TaskRepository:
    """
    Repository per la gestione delle task nel database.
    
    Tutti i metodi che accedono alla tabella 'tasks' sono decorati
    con @with_rls_context per garantire che:
    1. Le policy RLS siano attive (ruolo 'authenticated')
    2. Il contesto JWT sia configurato correttamente
    3. L'utente possa accedere SOLO alle proprie task
    
    IMPORTANTE: La sicurezza multi-tenant è garantita a livello database
    tramite RLS, non a livello applicativo. Il decorator applica
    automaticamente il contesto necessario.
    """
    
    @with_rls_context
    def get_all_tasks(self, conn: psycopg2.connect, username: str) -> List[Dict[str, any]]:
        """
        Recupera tutte le task dell'utente autenticato.
        
        Grazie all'RLS, questa query SELECT restituisce SOLO le task
        dove tenant_id corrisponde all'ID dell'utente autenticato.
        
        Args:
            conn: Connessione al database
            username: Username dell'utente autenticato (per contesto RLS)
        
        Returns:
            List[Dict]: Lista di dizionari, ciascuno rappresentante una task
                        Keys: id, tenant_id, title, description, color,
                              date_time, end_time, duration_minutes, completed, created_at
        
        Note:
            - @with_rls_context configura automaticamente il contesto RLS
            - Le task sono ordinate per date_time discendente (più recenti prima)
            - Restituisce lista vuota se l'utente non ha task
        """
        with conn.cursor() as cur:
            # Query semplice: l'RLS filtra automaticamente per tenant_id
            cur.execute("""
                SELECT id, tenant_id, title, description, color,
                       date_time, end_time, duration_minutes, completed, created_at
                FROM tasks
                ORDER BY date_time DESC
            """)
            
            results = cur.fetchall()
            
            # Mappa le tuple risultato in dizionari per facilità d'uso
            tasks = []
            for row in results:
                tasks.append({
                    'id': row[0],
                    'tenant_id': row[1],
                    'title': row[2],
                    'description': row[3],
                    'color': row[4],
                    'date_time': row[5],
                    'end_time': row[6],
                    'duration_minutes': row[7],
                    'completed': row[8],
                    'created_at': row[9]
                })
            
            return tasks
    
    @with_rls_context
    def create_task(
        self,
        conn: psycopg2.connect,
        username: str,
        tenant_id: UUID,
        title: str,
        description: str,
        color: str,
        date_time,
        end_time,
        duration_minutes: Optional[int],
        completed: bool
    ) -> Dict[str, any]:
        """
        Crea una nuova task nel database.
        
        L'RLS verifica che il tenant_id fornito corrisponda all'utente
        autenticato (policy INSERT WITH CHECK). Se non corrisponde,
        l'INSERT fallisce e non viene restituita alcuna riga.
        
        Args:
            conn: Connessione al database
            username: Username dell'utente autenticato (per contesto RLS)
            tenant_id: UUID del tenant (deve corrispondere all'utente autenticato!)
            title: Titolo della task
            description: Descrizione della task
            color: Colore della task (green, purple, orange, cyan, pink, yellow)
            date_time: Data/ora di inizio della task
            end_time: Data/ora di fine (opzionale, mutuamente esclusivo con duration_minutes)
            duration_minutes: Durata in minuti (opzionale, mutuamente esclusivo con end_time)
            completed: Flag di completamento
        
        Returns:
            Dict: Dizionario con tutti i campi della task creata
        
        Raises:
            HTTPException 400: Se l'RLS blocca l'inserimento (tenant_id non valido)
            HTTPException 500: Per altri errori database
        
        Note:
            - Il decorator @with_rls_context gestisce commit/rollback
            - L'ID e created_at vengono generati automaticamente dal database
        """
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tasks (
                    tenant_id, title, description, color,
                    date_time, end_time, duration_minutes, completed
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, tenant_id, title, description, color,
                          date_time, end_time, duration_minutes, completed, created_at
            """, (
                str(tenant_id),
                title,
                description,
                color,
                date_time,
                end_time,
                duration_minutes,
                completed
            ))
            
            result = cur.fetchone()
            
            if result is None:
                # L'INSERT non ha restituito righe: probabilmente bloccato da RLS
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Task creation failed. Possible RLS violation (tenant_id mismatch)."
                )
            
            # Mappa il risultato in un dizionario
            return {
                'id': result[0],
                'tenant_id': result[1],
                'title': result[2],
                'description': result[3],
                'color': result[4],
                'date_time': result[5],
                'end_time': result[6],
                'duration_minutes': result[7],
                'completed': result[8],
                'created_at': result[9]
            }
    
    @with_rls_context
    def update_task(
        self,
        conn: psycopg2.connect,
        username: str,
        task_id: UUID,
        title: str,
        description: str,
        color: str,
        date_time,
        end_time,
        duration_minutes: Optional[int],
        completed: bool
    ) -> Optional[Dict[str, any]]:
        """
        Aggiorna una task esistente.
        
        L'RLS garantisce che l'UPDATE possa modificare SOLO task
        appartenenti all'utente autenticato (policy UPDATE USING + WITH CHECK).
        
        Args:
            conn: Connessione al database
            username: Username dell'utente autenticato (per contesto RLS)
            task_id: UUID della task da aggiornare
            title: Nuovo titolo
            description: Nuova descrizione
            color: Nuovo colore
            date_time: Nuova data/ora di inizio
            end_time: Nuova data/ora di fine (opzionale)
            duration_minutes: Nuova durata (opzionale)
            completed: Nuovo stato di completamento
        
        Returns:
            Optional[Dict]: Dizionario con i dati aggiornati se successo, None se task non trovata
        
        Note:
            - Se l'RLS blocca l'UPDATE, fetchone() restituisce None
            - Non modifichiamo tenant_id per sicurezza (la policy lo vieta comunque)
            - Il decorator gestisce commit/rollback
        """
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE tasks
                SET title = %s,
                    description = %s,
                    color = %s,
                    date_time = %s,
                    end_time = %s,
                    duration_minutes = %s,
                    completed = %s
                WHERE id = %s
                RETURNING id, tenant_id, title, description, color,
                          date_time, end_time, duration_minutes, completed, created_at
            """, (
                title,
                description,
                color,
                date_time,
                end_time,
                duration_minutes,
                completed,
                str(task_id)
            ))
            
            result = cur.fetchone()
            
            if result is None:
                # Task non trovata o non appartiene all'utente (RLS block)
                return None
            
            # Mappa il risultato in un dizionario
            return {
                'id': result[0],
                'tenant_id': result[1],
                'title': result[2],
                'description': result[3],
                'color': result[4],
                'date_time': result[5],
                'end_time': result[6],
                'duration_minutes': result[7],
                'completed': result[8],
                'created_at': result[9]
            }
    
    @with_rls_context
    def delete_task(
        self,
        conn: psycopg2.connect,
        username: str,
        task_id: UUID
    ) -> bool:
        """
        Elimina una task dal database.
        
        L'RLS garantisce che il DELETE possa rimuovere SOLO task
        appartenenti all'utente autenticato (policy DELETE USING).
        
        Args:
            conn: Connessione al database
            username: Username dell'utente autenticato (per contesto RLS)
            task_id: UUID della task da eliminare
        
        Returns:
            bool: True se la task è stata eliminata, False se non trovata o non accessibile
        
        Note:
            - Se l'RLS blocca il DELETE, fetchone() restituisce None
            - Il decorator gestisce commit/rollback
        """
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM tasks
                WHERE id = %s
                RETURNING id
            """, (str(task_id),))
            
            result = cur.fetchone()
            
            # Se result è None, la task non esisteva o l'RLS l'ha bloccata
            return result is not None

