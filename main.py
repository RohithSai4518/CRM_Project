"""
OmniFlow CRM - Main Executable Application Entrypoint
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server import create_crm_app
from seeds.mock_crm_data import seed_database
from config.app_config import CONFIG


def main():
    print("Initializing OmniFlow Enterprise CRM...")
    if not os.path.exists(CONFIG.database.db_path):
        print("Provisioning storage and initial data seed...")
        seed_database()

    app = create_crm_app()
    app.start()


if __name__ == "__main__":
    main()
