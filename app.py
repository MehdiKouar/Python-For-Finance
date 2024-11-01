from flask import Flask
from research import backtest

app = Flask(__name__)


@app.route('/price_stale')
def find_stale_days():
    return backtest.find_stale_days()


if __name__ == '__main__':
    app.run()
