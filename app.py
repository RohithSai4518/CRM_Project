"""
OmniFlow CRM - App Runner Interface
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server import create_crm_app

app = create_crm_app()

if __name__ == "__main__":
    app.start()
