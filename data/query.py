from data.db_conf import conn
import pandas as pd


def get_ticker():
    cur = conn.cursor()
    cur.execute("SELECT name FROM ticker")
    ticker_name = cur.fetchall()
    conn.commit()
    cur.close()
    return ticker_name


def get_price(table_name):
    cur = conn.cursor()
    cur.execute("SELECT daily_date, close FROM " + table_name[0] + " ORDER BY daily_date ASC")
    price_result = cur.fetchall()
    conn.commit()
    cur.close()
    data = pd.DataFrame(price_result, columns=['Date', 'Close'])
    return data
