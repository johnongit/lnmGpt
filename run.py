import yfinance as yf
import json
import os
import time
from datetime import datetime, timedelta
import pytz
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()
# Constantes
BTC_SYMBOL = "BTC-USD"
THRESHOLD_PERCENT = float(os.environ.get('THRESHOLD_PERCENT', 3)) # Seuil de variation en pourcentage
LAST_EXEC_FILE = "last_execution.json"

def get_bitcoin_data(start_time):
    print(f"Récupération des données Bitcoin pour le symbole {BTC_SYMBOL}...")
    btc = yf.Ticker(BTC_SYMBOL)
    end_time = datetime.now(pytz.UTC)
    
    # Assurez-vous que start_time est en UTC
    
    if start_time.tzinfo is None:
        paris_tz = pytz.timezone('Europe/Paris')
        start_time = paris_tz.localize(start_time)
    start_time_utc = start_time.astimezone(pytz.UTC)
    # Arrondir start_time et end_time à des jours complets
    start_date = start_time.date()
    
    end_date = end_time.date() + timedelta(days=1)
    
    print(f"Période de récupération: de {start_date} à {end_date}")
    
    data = btc.history(start=start_date, interval="5m")
    start_time = start_time.replace(second=0, microsecond=0)

    
    mask = (data.index >= start_time_utc)
    
    filtered_data = data.loc[mask]
    
    print(f"Données filtrées. Nombre d'enregistrements: {len(filtered_data)}")

    
    return filtered_data

def load_last_execution():
    print(f"Chargement des données de la dernière exécution depuis {LAST_EXEC_FILE}...")
    if os.path.exists(LAST_EXEC_FILE):
        with open(LAST_EXEC_FILE, 'r') as f:
            data = json.load(f)
        print("Données chargées avec succès.")
        print(data)

        return data
    print("Aucune donnée de dernière exécution trouvée.")
    return None

def save_last_execution(price, high, low):
    data = {
        "timestamp": int(time.time()),
        "price": price,
        "high": high,
        "low": low
    }
    print(f"Sauvegarde des données de l'exécution actuelle dans {LAST_EXEC_FILE}...")
    with open(LAST_EXEC_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print("Données sauvegardées avec succès.")

def calculate_price_change(last_price, current_price):
    change = abs((current_price - last_price) / last_price) * 100
    print(f"Variation de prix calculée: {change:.2f}% (de {last_price:.2f} à {current_price:.2f})")
    return change

def should_execute():
    print("\nDétermination si le script principal doit être exécuté...")
    
    last_exec = load_last_execution()
    
    if last_exec is None:
        print("Première exécution détectée. Le script principal sera exécuté.")
        save_last_execution(current_price, current_price, current_price)
        return True

    last_timestamp = datetime.fromtimestamp(last_exec["timestamp"])

    
    btc_data = get_bitcoin_data(last_timestamp)
    #btc_data = get_bitcoin_data(last_timestamp - timedelta(days=50))
    if btc_data.empty:
        print("Aucune donnée Bitcoin disponible pour la période spécifiée.")
        exit(1)
        
    
    current_price = btc_data['Close'].iloc[-1]
    high_price = btc_data['High'].max()
    low_price = btc_data['Low'].min()

    print(f"Prix actuel: {current_price:.2f}")
    print(f"Prix le plus haut depuis la dernière exécution: {high_price:.2f}")
    print(f"Prix le plus bas depuis la dernière exécution: {low_price:.2f}")
    print(last_exec)
    last_price = last_exec["price"]
    last_high = last_exec["high"]
    last_low = last_exec["low"]

    print(f"Dernière exécution: prix = {last_price:.2f}, haut = {last_high:.2f}, bas = {last_low:.2f}")

    price_change = calculate_price_change(last_price, current_price)
    high_change = calculate_price_change(last_high, high_price)
    low_change = calculate_price_change(last_low, low_price)

    volatility = (high_price - low_price) / low_price * 100
    print(f"Volatilité calculée: {volatility:.2f}%")

    should_run = (price_change >= THRESHOLD_PERCENT or 
                  high_change >= THRESHOLD_PERCENT or 
                  low_change >= THRESHOLD_PERCENT or 
                  volatility >= THRESHOLD_PERCENT * 2)

    if should_run:
        print(f"Seuil de {THRESHOLD_PERCENT}% dépassé. Le script principal sera exécuté.")
        save_last_execution(current_price, high_price, low_price)
    else:
        print(f"Seuil de {THRESHOLD_PERCENT}% non atteint. Le script principal ne sera pas exécuté.")

    return should_run

import sys
import subprocess

def main_script():
    print("\nDébut de l'exécution du script principal...")
    command = ["python", "script-lnmAuto.py"]
    if len(sys.argv) > 1:
        if "oai" in sys.argv:
            command.append("oai")
        if "--auto-validate" in sys.argv:
            command.append("--auto-validate")
    result = subprocess.run(command)
    print(result.stdout)
    print("Fin de l'exécution du script principal.")

if __name__ == "__main__":
    print("Démarrage du script de vérification du prix Bitcoin...")
    
    if should_execute():
        main_script()
    else:
        print("\nRécapitulatif:")
        last_exec = load_last_execution()
        btc_data = get_bitcoin_data(datetime.fromtimestamp(last_exec["timestamp"]))
        current_price = btc_data['Close'].iloc[-1]
        high_price = btc_data['High'].max()
        low_price = btc_data['Low'].min()
        
        print(f"Dernière exécution : prix = {last_exec['price']:.2f}, haut = {last_exec['high']:.2f}, bas = {last_exec['low']:.2f}")
        print(f"Prix actuel : {current_price:.2f}, haut = {high_price:.2f}, bas = {low_price:.2f}")
        print(f"Variation de prix depuis la dernière exécution : {calculate_price_change(last_exec['price'], current_price):.2f}%")
        print(f"Variation du haut : {calculate_price_change(last_exec['high'], high_price):.2f}%")
        print(f"Variation du bas : {calculate_price_change(last_exec['low'], low_price):.2f}%")
        print(f"Volatilité : {((high_price - low_price) / low_price * 100):.2f}%")
    print("\nFin du script de vérification du prix Bitcoin.")