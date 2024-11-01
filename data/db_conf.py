import psycopg
from dotenv import dotenv_values
env = dotenv_values(".env")

conn = psycopg.connect(
    host=env["HOST"],
    dbname=env["DBNAME"],
    user=env["USER"],
    password=env["PASSWORD"])


