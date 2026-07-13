import os

import psycopg2


def get_db_connection():
    host = os.getenv("DCORE_HOST", "localhost")
    dbname = os.getenv("DCORE_DB", "dcoredb")
    user = os.getenv("DCORE_USER", "glennehmke")
    # No hardcoded fallback (ecosystem D1 / wlist ADR-002): if DCORE_PASSWORD isn't
    # set, password=None lets psycopg2 fall back to ~/.pgpass.
    password = os.getenv("DCORE_PASSWORD")
    port = int(os.getenv("DCORE_PORT", "5432"))
    return psycopg2.connect(host=host, dbname=dbname, user=user, password=password, port=port)
