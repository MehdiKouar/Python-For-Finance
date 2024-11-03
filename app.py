from flask import Flask
from research import backtest, analyse_asset

app = Flask(__name__)


@app.route('/backtest')
def stale_days_api():
    return backtest.backtest_stale_days()


@app.route('/resilient_asset')
def resilient_asset_api():
    return analyse_asset.find_resilient_asset()


@app.route('/recovering_stat')
def recovering_analyse_api():
    return analyse_asset.calculate_recovery_days()


if __name__ == '__main__':
    app.run()
