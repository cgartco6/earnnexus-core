# file: api/ledger.py
import os
import time
import psycopg2
from psycopg2 import errors

def load_local_env_fallback():
    """Reads .env variables sequentially if running inside a local development environment."""
    # Look for .env in the parent directory of this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

# Run environmental fallback loader instantly upon system runtime initialization
load_local_env_fallback()

def commit_transaction_to_db(reference: str, gross: int, cushion: int, secondary: int, banking: int) -> dict:
    """
    Commits transactional splits with an enterprise-grade retry matrix 
    and explicit database integrity checks.
    """
    db_uri = os.environ.get("SUPABASE_DB_CONNECTION_STRING")
    
    # If no database URI is supplied, drop down to safe, structured local mock logging
    if not db_uri:
        print("\n" + "[LOCAL MOCK MODE - NO DATABASE URI DETECTED]" + "-"*24)
        print(f"Ref ID:     {reference}")
        print(f"Gross:      {gross}¢ (R{gross/100:.2f})")
        print(f"Cushion:    {cushion}¢ (40%)")
        print(f"Secondary:  {secondary}¢ (50%)")
        print(f"Banking:    {banking}¢ (10%)")
        print("-"*60)
        return {"success": True, "strategy": "MOCK_LOGGED", "error": None}

    max_retries = 3
    base_delay = 1.0  # seconds
    
    for attempt in range(1, max_retries + 1):
        connection = None
        cursor = None
        try:
            # Establish dynamic network handle with Supabase Cluster
            connection = psycopg2.connect(db_uri, connect_timeout=5)
            cursor = connection.cursor()
            
            insert_query = """
                INSERT INTO public.transaction_ledger 
                (reference_id, total_gross_cents, allocation_cushion_cents, allocation_secondary_cents, allocation_banking_cents) 
                VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (reference, gross, cushion, secondary, banking))
            connection.commit()
            
            return {"success": True, "strategy": "PERSISTED", "error": None}
            
        except errors.UniqueViolation:
            # Cryptographic/App Level Idempotency Protection: Catches exact duplicate webhook replays instantly
            if connection:
                connection.rollback()
            return {"success": False, "strategy": "REJECTED_DUPLICATE", "error": "Transaction reference already processed."}
            
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as net_err:
            if connection:
                connection.rollback()
            if attempt == max_retries:
                return {"success": False, "strategy": "FAILURE", "error": f"Database network paths exhausted: {str(net_err)}"}
            # Exponential backoff retry loop: Wait 1s, then 2s, then 4s...
            time.sleep(base_delay * (2 ** (attempt - 1)))
            
        except Exception as general_err:
            if connection:
                connection.rollback()
            return {"success": False, "strategy": "FAILURE", "error": str(general_err)}
            
        finally:
            if cursor: 
                cursor.close()
            if connection: 
                connection.close()
            
    return {"success": False, "strategy": "FAILURE", "error": "Unknown connection state failure."}
