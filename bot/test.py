import sqlite3 as sq
import time

conn = sq.connect("db.db")
cur = conn.cursor()

# айди Тимура Богданова - 322615766
cur.execute("UPDATE players SET event_wishes=10, standard_wishes=10 WHERE user_id=322615766");conn.commit()
#a = cur.execute("SELECT rolls_standard from players WHERE user_id=322615766");a = a.fetchone();print(a)

