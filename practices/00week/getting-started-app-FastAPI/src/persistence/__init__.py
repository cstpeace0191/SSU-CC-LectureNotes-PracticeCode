import os

if os.getenv("MYSQL_HOST"):
    from . import mysql as db
else:
    from . import sqlite as db

__all__ = ["db"]
