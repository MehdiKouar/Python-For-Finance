import pandas as pd
import matplotlib.pyplot as plt
from data import query

def find_stale_days():
    results = []
    tickers = query.get_ticker()

    alpha_prior = 1
    beta_prior = 1

    initial_capital = 20000

    transaction_cost_pips = 200
    pip_value = 0.0001

    transaction_cost = transaction_cost_pips * pip_value

    portfolio_values = []
    dates = []

    for ticker in tickers:
        close_price = query.get_price(ticker)

        if close_price.empty:
            print(f"No data available for {ticker}")
            continue

        close_price.set_index('Date', inplace=True)

        start_date = close_price.index.min()
        end_date = close_price.index.max()

        close_price['Daily Change'] = close_price['Close'].pct_change() * 100
        close_price['Down Day'] = close_price['Daily Change'] < 0
        close_price['Two Day Decline'] = close_price['Down Day'] & close_price['Down Day'].shift(1)

        declines_after_two_day_drop = close_price[close_price['Two Day Decline']]['Daily Change']
        average_decline = declines_after_two_day_drop.mean()
        max_decline = declines_after_two_day_drop.min()

        recovery_count = 0
        no_recovery_count = 0

        capital = initial_capital

        capital_series = []

        for i in range(len(close_price)):
            if close_price['Two Day Decline'].iloc[i]:

                buy_price = close_price['Close'].iloc[i] + transaction_cost
                capital_after_entry_fee = capital

                shares = capital_after_entry_fee / buy_price

                future_prices = close_price['Close'].iloc[i + 1:i + 31]

                sell_price = None
                for future_price in future_prices:
                    if future_price >= buy_price * 1.01:
                        sell_price = future_price - transaction_cost
                        recovery_count += 1
                        break

                if sell_price is None:
                    sell_price = future_prices.iloc[-1] - transaction_cost if not future_prices.empty else buy_price
                    no_recovery_count += 1

                capital = shares * sell_price

                capital_series.append(capital)
                portfolio_values.append(capital)
                dates.append(close_price.index[i])

        portfolio_return = ((capital - initial_capital) / initial_capital) * 100

        capital_series = pd.Series(capital_series, index=dates)
        cumulative_max = capital_series.cummax()
        drawdowns = (capital_series - cumulative_max) / cumulative_max
        max_drawdown = drawdowns.min() * 100
        max_drawdown_date = drawdowns.idxmin()

        num_years = (end_date - start_date).days / 365.25
        annualized_return = ((capital / initial_capital) ** (1 / num_years) - 1) * 100

        alpha_posterior = alpha_prior + recovery_count
        beta_posterior = beta_prior + no_recovery_count
        probability_recovery = alpha_posterior / (alpha_posterior + beta_posterior)

        results.append({
            'Ticker': ticker,
            'Average Decline (%)': average_decline,
            'Max Decline (%)': max_decline,
            'Recovery Count': recovery_count,
            'No Recovery Count': no_recovery_count,
            'Probability Recovery >1% in 30 Days': probability_recovery,
            'Final Capital (€)': capital,
            'Portfolio Return (%)': portfolio_return,
            'Annualized Return (%)': annualized_return,
            'Max Drawdown (%)': max_drawdown,
            'Max Drawdown Date': max_drawdown_date
        })

    results_df = pd.DataFrame(results)
    results_html = results_df.to_html(index=False, classes='table table-striped')

    plt.figure(figsize=(12, 6))
    plt.plot(dates, portfolio_values, label="Portfolio Value")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value (€)")
    plt.title("Portfolio Performance Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

    return results_html
