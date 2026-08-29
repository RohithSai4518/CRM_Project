"""
CRM System - Database Migration Runner
Auto-provisions tables and verifies schema integrity
"""

from core.database.connection import DB
from core.database.schema import SCHEMA_DDL


def run_migrations():
    """Execute all schema DDL scripts to ensure tables and indexes exist."""
    try:
        DB.execute_script(SCHEMA_DDL)
        print("Database schema migrations applied successfully.")
    except Exception as e:
        print(f"Error executing database migrations: {e}")
        raise e


if __name__ == "__main__":
    run_migrations()
