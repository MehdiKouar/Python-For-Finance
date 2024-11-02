from flask import Flask
from research import backtest, analyse_asset

app = Flask(__name__)


@app.route('/find_stale_days')
def find_stale_days():
    return backtest.buy_stale_days()


@app.route('/resilient_asset')
def find_resilient_asset():
    return analyse_asset.find_resilient_asset()


if __name__ == '__main__':
    app.run()
