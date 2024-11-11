from flask import Flask
from research import analyse_asset


app = Flask(__name__)


@app.route('/trend')
def trend_stat_api():
    return analyse_asset.find_trend(90, 20)


@app.route('/recovering_stat')
def recovering_analyse_api():
    return analyse_asset.recovery_statistics(2)


@app.route('/rebound_signals')
def rebound_analyse_api():
    return analyse_asset.check_rebound_probability_for_ticker('sp500', 3800, 0.004, 7)


if __name__ == '__main__':
    app.run()
