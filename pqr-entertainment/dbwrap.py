# Thin wrapper to centralize database access
# Existing code uses `import database as db`.
# New modules can do: `from dbwrap import db`.
import database as db  # re-export
