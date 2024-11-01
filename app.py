from flask import Flask
from research import analyse

app = Flask(__name__)


@app.route('/price_stale')
def find_stale_days():
    return analyse.proba_recovery()


if __name__ == '__main__':
    app.run()
