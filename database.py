import streamlit as st
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import time
import re
import uuid
import datetime

NEON_DB_URL = "postgresql://neondb_owner:npg_pJYTD3klbVa8@ep-round-violet-azb55s71-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Create engine with connection pooling enabled
engine = create_engine(NEON_DB_URL, pool_size=10, max_overflow=20)

def get_connection():
    """
    Returns a connection from the SQLAlchemy connection pool.
    This eliminates the massive overhead of re-authenticating and performing SSL handshakes on every single click.
    """
    return engine.raw_connection()

def init_db():
    """
    Initializes the database metadata table if it doesn't already exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_metadata (
            id SERIAL PRIMARY KEY,
            table_name TEXT UNIQUE,
            display_name TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()

@st.cache_data(ttl=300)
def get_statuses():
    """Returns a list of all statuses (defaults + custom)."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM crm_settings WHERE key='statuses'")
    row = cursor.fetchone()
    conn.close()
    
    defaults = ['TO action', 'Acted', 'Converted', 'Failed']
    if row and row[0]:
        customs = row[0].split(',')
        # Maintain order: defaults first, then customs
        for c in customs:
            if c and c not in defaults:
                defaults.append(c)
    return defaults

def add_custom_status(status):
    """Adds a new custom status to the settings."""
    status = status.strip()
    if not status: return
    statuses = get_statuses()
    if status not in statuses:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM crm_settings WHERE key='statuses'")
        row = cursor.fetchone()
        
        customs = row[0].split(',') if (row and row[0]) else []
        customs.append(status)
        
        cursor.execute("""
            INSERT INTO crm_settings (key, value) VALUES ('statuses', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (','.join(customs),))
        conn.commit()
        conn.close()
        st.cache_data.clear()

def save_dataframe(df, file_name):
    """
    Imports a pandas DataFrame as a new CRM table in PostgreSQL.
    """
    init_db()
    
    unique_suffix = uuid.uuid4().hex[:8]
    sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', file_name).lower()
    table_name = f"crm_{sanitized_name}_{unique_suffix}"
    
    df_to_save = df.copy()
    
    valid_statuses = set(get_statuses())
    if 'status' not in df_to_save.columns:
        df_to_save['status'] = 'TO action'
    else:
        df_to_save['status'] = df_to_save['status'].fillna('TO action').astype(str)
        df_to_save['status'] = df_to_save['status'].apply(lambda x: x if x in valid_statuses else 'TO action')

    if '_crm_id' not in df_to_save.columns:
        df_to_save.insert(0, '_crm_id', range(1, len(df_to_save) + 1))
    
    df_to_save.to_sql(table_name, engine, if_exists='replace', index=False)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO crm_metadata (table_name, display_name) VALUES (%s, %s)",
        (table_name, file_name)
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()
    return table_name

@st.cache_data(ttl=300)
def get_tables():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT table_name, display_name, uploaded_at FROM crm_metadata ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"table_name": r[0], "display_name": r[1], "uploaded_at": str(r[2])} for r in rows]

def ensure_callback_columns(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s
    """, (table_name,))
    cols = [row[0] for row in cursor.fetchall()]
    modified = False
    if 'callback_time' not in cols:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN callback_time TEXT")
        modified = True
    if 'callback_notes' not in cols:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN callback_notes TEXT")
        modified = True
    if modified:
        conn.commit()

@st.cache_data(ttl=300)
def get_table_data(table_name):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", (table_name,))
        if not cursor.fetchone()[0]:
            conn.close()
            return None
        
        ensure_callback_columns(conn, table_name)
        
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", engine)
        conn.close()
        return df
    except Exception as e:
        conn.close()
        raise e

def update_status(table_name, crm_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {table_name} SET status = %s WHERE _crm_id = %s",
        (new_status, int(crm_id))
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()

def delete_row(table_name, crm_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"DELETE FROM {table_name} WHERE _crm_id = %s",
        (int(crm_id),)
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()

def update_lead_field(table_name, crm_id, col_name, new_val):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {table_name} SET \"{col_name}\" = %s WHERE _crm_id = %s",
        (new_val, int(crm_id))
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()

def add_column(table_name, col_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN \"{col_name}\" TEXT")
    conn.commit()
    conn.close()
    st.cache_data.clear()

def delete_column(table_name, col_name):
    if col_name in ('_crm_id', 'status'):
        return False
        
    conn = get_connection()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", engine)
        if col_name in df.columns:
            df = df.drop(columns=[col_name])
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            conn.close()
            st.cache_data.clear()
            return True
        conn.close()
        return False
    except Exception as e:
        conn.close()
        raise e

def delete_table(table_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute("DELETE FROM crm_metadata WHERE table_name = %s", (table_name,))
    conn.commit()
    conn.close()
    st.cache_data.clear()

def update_callback(table_name, crm_id, callback_time_str, callback_notes):
    conn = get_connection()
    ensure_callback_columns(conn, table_name)
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {table_name} SET callback_time = %s, callback_notes = %s WHERE _crm_id = %s",
        (callback_time_str, callback_notes, int(crm_id))
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()

@st.cache_data(ttl=60)
def get_due_callbacks():
    tables = get_tables()
    conn = get_connection()
    due = []
    
    now_str = datetime.datetime.now().isoformat()
    
    for t in tables:
        t_name = t['table_name']
        try:
            ensure_callback_columns(conn, t_name)
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT _crm_id, callback_time, callback_notes FROM {t_name} WHERE callback_time IS NOT NULL AND callback_time != '' AND callback_time != 'None' AND callback_time <= %s",
                (now_str,)
            )
            rows = cursor.fetchall()
            for r in rows:
                due.append({
                    'table_name': t_name,
                    'display_name': t['display_name'],
                    '_crm_id': r[0],
                    'callback_time': r[1],
                    'callback_notes': r[2]
                })
        except Exception:
            pass
    conn.close()
    return due
