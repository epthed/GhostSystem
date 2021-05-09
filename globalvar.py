import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

#
# db = apsw.Connection("DB.sqlite")
# dbcur = db.cursor()
# l = Lock()
