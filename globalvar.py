import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

#
# db = apsw.Connection("DB.sqlite")
# dbcur = db.cursor()
# l = Lock()

# Warning Never, never, NEVER use Python string concatenation (+) or string parameters interpolation (%) to pass
# variables to a SQL query string. Not even at gunpoint.
# The correct way to pass variables in a SQL command is using the second argument of the execute() method:
#
# >>> SQL = "INSERT INTO authors (name) VALUES (%s);" # Note: no quotes
# >>> data = ("O'Reilly", )
# >>> cur.execute(SQL, data) # Note: no % operator
