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
