from flask import Flask
from research import backtest, analyse_asset

app = Flask(__name__)


@app.route('/stale_days')
def call_stale_days():
    return backtest.backtest_stale_days()


@app.route('/resilient_asset')
def call_resilient_asset():
    return analyse_asset.find_resilient_asset()


@app.route('/recovering_stat')
def call_recovering_analyse():
    return analyse_asset.analyze_recovery_days()


if __name__ == '__main__':
    app.run()
