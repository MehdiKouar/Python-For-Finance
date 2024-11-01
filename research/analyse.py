import pandas as pd
from data import query


def find_stale_days():

    results = []

    tickers = query.get_ticker()

    for ticker in tickers:

        close_price = query.get_price(ticker)

        if close_price.empty:
            print(f"No data available for {ticker}")
            continue

        close_price.set_index('Date', inplace=True)

        close_price['Daily Change'] = close_price['Close'].pct_change() * 100
        close_price['Down Day'] = close_price['Daily Change'] < 0
        close_price['Two Day Decline'] = close_price['Down Day'] & close_price['Down Day'].shift(1)

        declines_after_two_day_drop = close_price[close_price['Two Day Decline']]['Daily Change']
        average_decline = declines_after_two_day_drop.mean()
        max_decline = declines_after_two_day_drop.min()

        recovery_count = 0
        no_recovery_count = 0

        for i in range(len(close_price)):
            if close_price['Two Day Decline'].iloc[i]:
                start_price = close_price['Close'].iloc[i]
                future_prices = close_price['Close'].iloc[i + 1:i + 31]
                if (future_prices > start_price * 1.01).any():
                    recovery_count += 1
                else:
                    no_recovery_count += 1

        results.append({
            'Ticker': ticker,
            'Average Decline (%)': average_decline,
            'Max Decline (%)': max_decline,
            'Recovery Count': recovery_count,
            'No Recovery Count': no_recovery_count
        })

    results_df = pd.DataFrame(results)
    results_html = results_df.to_html(index=False, classes='table table-striped')

    return results_html
