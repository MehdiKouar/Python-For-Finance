import pandas as pd
from data import query


def find_resilient_asset():
    # Récupère tous les tickers
    tickers = query.get_ticker()

    # Liste pour stocker les résultats
    results = []

    # Boucle pour chaque ticker
    for ticker in tickers:
        # Récupère les prix de clôture pour le ticker
        close_price = query.get_price(ticker)

        # Vérifie que les données ne sont pas vides
        if close_price.empty:
            print(f"No data available for {ticker}")
            continue

        # Convertit les données en DataFrame et fixe l'index sur la date
        df = pd.DataFrame(close_price)
        df.set_index('Date', inplace=True)

        # Calcule la SMA 200
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # Calcule le nombre de jours où le prix de clôture est supérieur à la SMA 200
        days_above_sma = int((df['Close'] > df['SMA_200']).sum())

        # Calcule le nombre total de jours de cotation
        total_days = int(df['Close'].count())

        # Calcule le pourcentage de jours au-dessus de la SMA 200
        percentage_above_sma = float((days_above_sma / total_days) * 100) if total_days > 0 else 0.0

        # Stocke le résultat dans la liste
        results.append({
            'Ticker': ticker[0],
            'Days Above SMA 200': days_above_sma,
            'Total Days': total_days,
            'Percentage Above SMA 200 (%)': percentage_above_sma
        })

    # Convertir les résultats en DataFrame
    results_df = pd.DataFrame(results)

    # Convertir le DataFrame en HTML
    results_html = results_df.to_html(index=False, classes='table table-striped')

    return results_html


def analyze_recovery_days():
    results = []
    tickers = query.get_ticker()

    # Loop through each ticker
    for ticker in tickers:
        # Retrieve close prices for the ticker
        close_price = query.get_price(ticker)

        # Check if data is empty
        if close_price.empty:
            print(f"No data available for {ticker}")
            continue

        # Set index to Date and calculate daily percentage change
        close_price.set_index('Date', inplace=True)
        close_price['Daily Change'] = close_price['Close'].pct_change() * 100

        # Identify consecutive down days and total percentage drop for those days
        close_price['Down Day'] = close_price['Daily Change'] < 0
        close_price['Two Day Decline'] = (close_price['Down Day'] & close_price['Down Day'].shift(1))
        close_price['Two Day Drop %'] = close_price['Daily Change'] + close_price['Daily Change'].shift(1)

        # Find periods where there's a two-day decline greater than 1%
        decline_periods = close_price[close_price['Two Day Decline'] & (close_price['Two Day Drop %'] < -1)]

        recovery_days_list = []  # List to store recovery days for each period

        # Analyze each decline period
        for start_date in decline_periods.index:
            start_price = close_price.loc[start_date, 'Close']
            future_prices = close_price['Close'].loc[start_date:]

            # Find the first day in the future where there's a 1% recovery from the start price
            recovery_date = None
            for future_date, future_price in future_prices.items():
                if future_price >= start_price * 1.01:
                    recovery_date = future_date
                    break

            # Calculate the number of days to recovery
            if recovery_date:
                days_to_recovery = (recovery_date - start_date).days
                recovery_days_list.append(days_to_recovery)

        # Calculate average recovery days for this ticker
        if recovery_days_list:
            average_recovery_days = sum(recovery_days_list) / len(recovery_days_list)
        else:
            average_recovery_days = None

        # Store the results for this ticker
        results.append({
            'Ticker': ticker[0],
            'Average Recovery Days': average_recovery_days,
            'Total Decline Periods': len(recovery_days_list)
        })

    # Convert results to DataFrame and return as HTML table
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by='Average Recovery Days', ascending=True)
    results_html = results_df.to_html(index=False, classes='table table-striped')

    return results_html
