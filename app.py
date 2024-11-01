from flask import Flask
from research import analyse

app = Flask(__name__)


@app.route('/price_stale')
def price_stale():
    return analyse.find_stale_days()


if __name__ == '__main__':
    app.run()
