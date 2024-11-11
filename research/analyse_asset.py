import pandas as pd
from data import query


def find_trend(lookback_days, sma_period):
    results = []
    tickers = query.get_ticker()

    for ticker in tickers:

        close_price = query.get_price(ticker)

        if close_price.empty:
            print(f"No data available for {ticker}")
            continue

        df = pd.DataFrame(close_price)
        df.set_index('Date', inplace=True)
        df = df.tail(lookback_days + sma_period - 1)
        df[f'SMA_{sma_period}'] = df['Close'].rolling(window=sma_period).mean()
        df = df.tail(lookback_days)
        days_above_sma = int((df['Close'] > df[f'SMA_{sma_period}']).sum())
        total_days = int(df['Close'].count())
        percentage_above_sma = float((days_above_sma / total_days) * 100) if total_days > 0 else 0.0

        results.append({
            'Ticker': ticker[0],
            'Days Above SMA': days_above_sma,
            'Total Days': total_days,
            f'Percentage Above SMA {sma_period} (%)': percentage_above_sma
        })

    results_df = pd.DataFrame(results)
    results_html = results_df.to_html(index=False, classes='table table-striped')

    return results_html


def recovery_statistics(consecutive_days):
    results = []
    tickers = query.get_ticker()

    for ticker in tickers:
        close_price = query.get_price(ticker)

        if close_price.empty:
            print(f"No data available for {ticker}")
            continue

        close_price['Date'] = pd.to_datetime(close_price['Date'])
        close_price.set_index('Date', inplace=True)
        close_price['Daily Change'] = close_price['Close'].pct_change() * 100
        close_price['Down Day'] = close_price['Daily Change'] < 0

        condition = (close_price['Down Day'].rolling(window=consecutive_days)
                     .sum() == consecutive_days) & \
                    (close_price['Daily Change'].rolling(window=consecutive_days).sum() < -1)
        close_price['Decline Period'] = condition

        decline_periods = close_price[close_price['Decline Period']]
        print(f"\nIdentified decline periods for {ticker[0]}:")
        print(decline_periods[['Close', 'Daily Change']])

        recovery_days_list = []
        decline_percentage_list = []

        for start_date in decline_periods.index:

            pre_decline_price_index = close_price.index.get_loc(start_date) - 1
            if pre_decline_price_index < 0:
                continue

            pre_decline_price = close_price.iloc[pre_decline_price_index]['Close']
            total_decline = ((pre_decline_price - close_price.loc[start_date, 'Close']) / pre_decline_price) * 100
            decline_percentage_list.append(total_decline)

            recovery_date = None
            future_prices = close_price['Close'].loc[start_date:]
            for future_date, future_price in future_prices.items():
                if future_price >= pre_decline_price:
                    recovery_date = future_date
                    print(f"Price recovered to {pre_decline_price} on {recovery_date} for ticker {ticker[0]}")
                    break

            if recovery_date:
                days_to_recovery = (recovery_date - start_date).days
                recovery_days_list.append(days_to_recovery)
            else:
                print(
                    f"No recovery to pre-decline price found within the lookahead period after decline on {start_date}")

        if recovery_days_list:
            average_recovery_days = sum(recovery_days_list) / len(recovery_days_list)
        else:
            average_recovery_days = None

        if decline_percentage_list:
            average_decline_percentage = sum(decline_percentage_list) / len(decline_percentage_list)
        else:
            average_decline_percentage = None

        results.append({
            'Ticker': ticker[0],
            'Average Recovery Days': average_recovery_days,
            'Average Decline Percentage': average_decline_percentage,
            'Total Decline Periods': len(decline_percentage_list)
        })

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by='Average Recovery Days', ascending=True)
    results_html = results_df.to_html(index=False, classes='table table-striped')

    return results_html


def calculate_rebound_probability_within_days(close_prices, target_price, tolerance, days):
    rebound_count = 0
    no_rebound_count = 0
    max_rebound_levels = []

    for i in range(1, len(close_prices) - days):
        if close_prices[i - 1] > target_price and abs(close_prices[i] - target_price) / target_price <= tolerance:
            rebounded = False
            max_rebound_level = close_prices[i]

            for j in range(1, days + 1):
                if close_prices[i + j] > close_prices[i]:
                    rebound_count += 1
                    rebounded = True

                max_rebound_level = max(max_rebound_level, close_prices[i + j])

                if rebounded:
                    break

            if not rebounded:
                no_rebound_count += 1

            max_rebound_levels.append((max_rebound_level - close_prices[i]) / close_prices[i] * 100)

    total_tests = rebound_count + no_rebound_count
    if total_tests == 0:
        rebound_probability = None
        no_rebound_probability = None
        average_max_rebound = None
    else:
        rebound_probability = rebound_count / total_tests
        no_rebound_probability = no_rebound_count / total_tests
        average_max_rebound = sum(max_rebound_levels) / len(max_rebound_levels) if max_rebound_levels else None

    return {
        'Rebound Probability': rebound_probability,
        'No Rebound Probability': no_rebound_probability,
        'Average Max Rebound (%)': average_max_rebound,
        'Total Tests': total_tests
    }


def check_rebound_probability_for_ticker(ticker, target_price, tolerance, days):

    close_price = query.get_api_price(ticker)

    if close_price.empty:
        print(f"No data available for {ticker}")
        return None

    close_price['Date'] = pd.to_datetime(close_price['Date'])
    close_price.set_index('Date', inplace=True)
    close_prices = close_price['Close']

    result = calculate_rebound_probability_within_days(close_prices, target_price, tolerance, days)

    result_df = pd.DataFrame([{
        'Ticker': ticker,
        'Target Price': target_price,
        'Rebound Probability (within 7 days)': result['Rebound Probability'],
        'No Rebound Probability (within 7 days)': result['No Rebound Probability'],
        'Average Max Rebound (%)': result['Average Max Rebound (%)'],
        'Total Tests': result['Total Tests']
    }])

    return result_df.to_html(index=False, classes='table table-striped')
