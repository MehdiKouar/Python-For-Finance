import pandas as pd
import matplotlib.pyplot as plt
from data import query


def backtest_stale_days():
    results = []
    trades_log = []  # List to store trade details for CSV export
    tickers = query.get_ticker()

    # Bayesian prior parameters for recovery probability
    alpha_prior = 1
    beta_prior = 1

    # Initial capital and transaction cost parameters
    initial_capital = 20000
    transaction_cost_pips = 200
    pip_value = 0.0001
    transaction_cost = transaction_cost_pips * pip_value

    # Cooling period parameters
    cooling_period = 7  # Days to wait after two consecutive losses
    consecutive_losses = 0  # Counter for consecutive losing trades
    cooling_start_date = None  # Start date of the cooling period
    position_open = False  # Variable to track if a position is currently open

    # Global lists for portfolio values and dates
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

        # Statistics for two-day drops
        declines_after_two_day_drop = close_price[close_price['Two Day Decline']]['Daily Change']
        average_decline = declines_after_two_day_drop.mean()
        max_decline = declines_after_two_day_drop.min()

        # Recovery counters
        recovery_count = 0
        no_recovery_count = 0

        # Initialize capital and series for backtest
        capital = initial_capital
        capital_series = []
        date_series = []

        for i in range(len(close_price)):
            current_date = close_price.index[i]

            # Check if in cooling period
            if cooling_start_date and (current_date - cooling_start_date).days < cooling_period:
                continue  # Skip this date if within cooling period

            # Exit cooling period after the set period and reset counter
            if cooling_start_date and (current_date - cooling_start_date).days >= cooling_period:
                cooling_start_date = None
                consecutive_losses = 0

            # Condition to buy after two consecutive down days, only if no position is open
            if close_price['Two Day Decline'].iloc[i] and not position_open:
                entry_date = current_date
                buy_price = close_price['Close'].iloc[i] + transaction_cost
                capital_after_entry_fee = capital
                shares = capital_after_entry_fee / buy_price
                position_open = True

                # Look ahead to determine sell price with stop-loss and recovery threshold
                future_prices = close_price['Close'].iloc[i + 1:i + 37]
                sell_price = None
                exit_date = None

                for j, future_price in enumerate(future_prices):
                    if future_price >= buy_price * 1.02:  # Recovery condition
                        sell_price = future_price - transaction_cost
                        recovery_count += 1
                        exit_date = future_prices.index[j]
                        break
                    elif future_price <= buy_price * 0.9:  # Stop-loss condition
                        sell_price = future_price - transaction_cost
                        no_recovery_count += 1
                        exit_date = future_prices.index[j]
                        break

                if sell_price is None:
                    sell_price = future_prices.iloc[-1] - transaction_cost if not future_prices.empty else buy_price
                    no_recovery_count += 1
                    exit_date = future_prices.index[-1] if not future_prices.empty else entry_date

                capital_after_sale = shares * sell_price
                trade_result = (capital_after_sale - capital) / capital * 100
                capital = capital_after_sale

                if not trades_log or trades_log[-1]['Exit Date'] <= entry_date:
                    trades_log.append({
                        'Ticker': ticker[0],
                        'Entry Date': entry_date,
                        'Exit Date': exit_date,
                        'Position Return (%)': trade_result
                    })

                if trade_result < 0:
                    consecutive_losses += 1
                else:
                    consecutive_losses = 0

                if consecutive_losses >= 2:
                    cooling_start_date = current_date
                    consecutive_losses = 0

                position_open = False
                capital_series.append(capital)
                date_series.append(current_date)

        portfolio_values.extend(capital_series)
        dates.extend(date_series)

        # Calculate portfolio statistics
        portfolio_return = ((capital - initial_capital) / initial_capital) * 100
        capital_series = pd.Series(capital_series, index=date_series)
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
            'Ticker': ticker[0],
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

    # Create results DataFrame and generate HTML table
    results_df = pd.DataFrame(results)
    results_html = results_df.to_html(index=False, classes='table table-striped')

    # Save trade log to CSV
    trades_log_df = pd.DataFrame(trades_log)
    trades_log_df.to_csv('trades_log.csv', index=False)

    # Plot portfolio performance
    if dates and portfolio_values:
        plt.figure(figsize=(12, 6))
        plt.plot(dates, portfolio_values, label="Portfolio Value")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value (€)")
        plt.title("Portfolio Performance Over Time")
        plt.legend()
        plt.grid(True)
        plt.show()

    return results_html
