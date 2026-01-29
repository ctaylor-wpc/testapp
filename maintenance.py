# maintenance.py
# Maintenance mode controlled by environment variable

import os

# Check environment variable (defaults to False if not set)
MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

MAINTENANCE_MESSAGE = """
### 🔧 System Maintenance

Our job application system is currently being updated.

**Please check back in 3-4 minutes.**

We apologize for any inconvenience!
"""