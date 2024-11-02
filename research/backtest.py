import pandas as pd
import matplotlib.pyplot as plt
from data import query

def buy_stale_days():
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

    # Lists to store portfolio values and dates for plotting
    portfolio_values = []
    dates = []

    # Cooling period parameters
    cooling_period = 7  # Days to wait after two consecutive losses
    consecutive_losses = 0  # Counter for consecutive losing trades
    cooling_start_date = None  # Start date of the cooling period
    position_open = False  # Variable to track if a position is currently open

    for ticker in tickers:
        # Retrieve close prices for the ticker
        close_price = query.get_price(ticker)

        # Check if data is empty
        if close_price.empty:
            print(f"No data available for {ticker}")
            continue

        # Set index to Date and calculate indicators
        close_price.set_index('Date', inplace=True)
        start_date = close_price.index.min()
        end_date = close_price.index.max()

        # Calculate daily percentage change
        close_price['Daily Change'] = close_price['Close'].pct_change() * 100
        close_price['Down Day'] = close_price['Daily Change'] < 0
        close_price['Two Day Decline'] = close_price['Down Day'] & close_price['Down Day'].shift(1)

        # Calculate statistics for declines after two-day drops
        declines_after_two_day_drop = close_price[close_price['Two Day Decline']]['Daily Change']
        average_decline = declines_after_two_day_drop.mean()
        max_decline = declines_after_two_day_drop.min()

        # Counters for recovery statistics
        recovery_count = 0
        no_recovery_count = 0

        # Initialize capital for backtest
        capital = initial_capital
        capital_series = []

        # Backtest loop
        for i in range(len(close_price)):
            current_date = close_price.index[i]

            # Check if in cooling period
            if cooling_start_date and (current_date - cooling_start_date).days < cooling_period:
                continue  # Skip this date if within cooling period

            # Exit cooling period after 30 days and reset counter
            if cooling_start_date and (current_date - cooling_start_date).days >= cooling_period:
                cooling_start_date = None
                consecutive_losses = 0

            # Condition to buy after two consecutive down days, only if no position is open
            if close_price['Two Day Decline'].iloc[i] and not position_open:
                entry_date = current_date  # Record entry date
                buy_price = close_price['Close'].iloc[i] + transaction_cost
                capital_after_entry_fee = capital

                # Calculate number of shares bought
                shares = capital_after_entry_fee / buy_price
                position_open = True  # Mark that a position is now open

                # Look ahead 30 days to determine sell price
                future_prices = close_price['Close'].iloc[i + 1:i + 31]

                sell_price = None
                exit_date = None
                for j, future_price in enumerate(future_prices):
                    if future_price >= buy_price * 1.01:
                        sell_price = future_price - transaction_cost
                        recovery_count += 1
                        exit_date = future_prices.index[j]  # Record exit date
                        break

                # If no recovery, sell at the last price in the 30-day window
                if sell_price is None:
                    sell_price = future_prices.iloc[-1] - transaction_cost if not future_prices.empty else buy_price
                    no_recovery_count += 1
                    exit_date = future_prices.index[-1] if not future_prices.empty else entry_date  # Last date in window

                # Calculate resulting capital after trade
                capital_after_sale = shares * sell_price
                trade_result = (capital_after_sale - capital) / capital * 100  # Percentage return of the trade
                capital = capital_after_sale

                # Check for overlapping positions before logging the trade
                if not trades_log or trades_log[-1]['Exit Date'] <= entry_date:
                    # Log the trade details if no overlap with the previous trade
                    trades_log.append({
                        'Ticker': ticker[0],
                        'Entry Date': entry_date,
                        'Exit Date': exit_date,
                        'Position Return (%)': trade_result
                    })

                # Update consecutive loss count and cooling period if necessary
                if trade_result < 0:
                    consecutive_losses += 1
                else:
                    consecutive_losses = 0

                if consecutive_losses >= 2:
                    cooling_start_date = current_date
                    consecutive_losses = 0  # Reset consecutive losses

                # Mark the position as closed
                position_open = False

                # Record capital value for this date
                capital_series.append(capital)
                portfolio_values.append(capital)
                dates.append(current_date)

        # Calculate portfolio statistics
        portfolio_return = ((capital - initial_capital) / initial_capital) * 100

        # Calculate maximum drawdown and its date
        capital_series = pd.Series(capital_series, index=dates)
        cumulative_max = capital_series.cummax()
        drawdowns = (capital_series - cumulative_max) / cumulative_max
        max_drawdown = drawdowns.min() * 100
        max_drawdown_date = drawdowns.idxmin()

        # Calculate annualized return
        num_years = (end_date - start_date).days / 365.25
        annualized_return = ((capital / initial_capital) ** (1 / num_years) - 1) * 100

        # Update Bayesian probability for recovery
        alpha_posterior = alpha_prior + recovery_count
        beta_posterior = beta_prior + no_recovery_count
        probability_recovery = alpha_posterior / (alpha_posterior + beta_posterior)

        # Append results for the ticker
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

    # Convert results to a DataFrame and generate HTML table
    results_df = pd.DataFrame(results)
    results_html = results_df.to_html(index=False, classes='table table-striped')

    # Save trade log to CSV
    trades_log_df = pd.DataFrame(trades_log)
    trades_log_df.to_csv('trades_log.csv', index=False)

    # Plot portfolio performance
    plt.figure(figsize=(12, 6))
    plt.plot(dates, portfolio_values, label="Portfolio Value")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value (€)")
    plt.title("Portfolio Performance Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

    return results_html
