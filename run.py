import yfinance as yf
import json
import os
import time
from datetime import datetime, timedelta
import pytz
import subprocess
import sys
from dotenv import load_dotenv
import logging
import schedule
from colorama import init, Fore, Style

# Initialiser colorama
init(autoreset=True)

load_dotenv()
# Constantes
BTC_SYMBOL = "BTC-USD"
THRESHOLD_PERCENT = float(os.environ.get('THRESHOLD_PERCENT', 3)) # Seuil de variation en pourcentage
LAST_EXEC_FILE = "last_execution.json"

# Configuration du logging
log_file = "bitcoin_script.log"
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')

# Fonction pour le logging coloré dans la console
def console_log(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if level == "INFO":
        print(f"{Fore.GREEN}{timestamp} - INFO: {message}{Style.RESET_ALL}")
    elif level == "WARNING":
        print(f"{Fore.YELLOW}{timestamp} - WARNING: {message}{Style.RESET_ALL}")
    elif level == "ERROR":
        print(f"{Fore.RED}{timestamp} - ERROR: {message}{Style.RESET_ALL}")
    else:
        print(f"{timestamp} - {level}: {message}")

def get_bitcoin_data(start_time):
    console_log(f"Récupération des données Bitcoin pour le symbole {BTC_SYMBOL}...")
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
    
    console_log(f"Période de récupération: de {start_date} à {end_date}")
    
    data = btc.history(start=start_date, interval="5m")
    start_time = start_time.replace(second=0, microsecond=0)

    
    mask = (data.index >= start_time_utc)
    
    filtered_data = data.loc[mask]
    
    console_log(f"Données filtrées. Nombre d'enregistrements: {len(filtered_data)}")

    
    return filtered_data

def load_last_execution():
    console_log(f"Chargement des données de la dernière exécution depuis {LAST_EXEC_FILE}...")
    if os.path.exists(LAST_EXEC_FILE):
        with open(LAST_EXEC_FILE, 'r') as f:
            data = json.load(f)
        console_log("Données chargées avec succès.")
        console_log(data)

        return data
    console_log("Aucune donnée de dernière exécution trouvée.")
    return None

def save_last_execution(price, high, low):
    data = {
        "timestamp": int(time.time()),
        "price": price,
        "high": high,
        "low": low
    }
    console_log(f"Sauvegarde des données de l'exécution actuelle dans {LAST_EXEC_FILE}...")
    with open(LAST_EXEC_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    console_log("Données sauvegardées avec succès.")

def calculate_price_change(last_price, current_price):
    change = abs((current_price - last_price) / last_price) * 100
    console_log(f"Variation de prix calculée: {change:.2f}% (de {last_price:.2f} à {current_price:.2f})")
    return change

def should_execute():
    console_log("\nDétermination si le script principal doit être exécuté...")
    logging.info(f'''Détermination si le script principal doit être exécuté...''')
    last_exec = load_last_execution()
    if last_exec is None:
        console_log("Première exécution détectée. Le script principal sera exécuté.")
        t = time.time()
        t = datetime.fromtimestamp(t)
        t = t - timedelta(hours=10)
        t = datetime.timestamp(t)
        t = datetime.fromtimestamp(t)
        btc_data = get_bitcoin_data(t)
        
        
        current_price = btc_data['Close'].iloc[-1]
        save_last_execution(current_price, current_price, current_price)
        return True
    
    
    
    last_timestamp = datetime.fromtimestamp(last_exec["timestamp"])
    try:
        btc_data = get_bitcoin_data(last_timestamp)

        current_price = btc_data['Close'].iloc[-1]
        high_price = btc_data['High'].max()
        low_price = btc_data['Low'].min()
        
    except Exception as e:
        console_log(f'''Erreur lors de la récupération des données Bitcoin. On considère que le seuil est dépassé''')
        return True

    
    
    #btc_data = get_bitcoin_data(last_timestamp - timedelta(days=50))
    if btc_data.empty:
        console_log("Aucune donnée Bitcoin disponible pour la période spécifiée.")
        exit(1)
        


    console_log(f"Prix actuel: {current_price:.2f}")
    console_log(f"Prix le plus haut depuis la dernière exécution: {high_price:.2f}")
    console_log(f"Prix le plus bas depuis la dernière exécution: {low_price:.2f}")
    console_log(last_exec)
    last_price = last_exec["price"]
    last_high = last_exec["high"]
    last_low = last_exec["low"]

    console_log(f"Dernière exécution: prix = {last_price:.2f}, haut = {last_high:.2f}, bas = {last_low:.2f}")

    price_change = calculate_price_change(last_price, current_price)
    high_change = calculate_price_change(last_high, high_price)
    low_change = calculate_price_change(last_low, low_price)

    volatility = (high_price - low_price) / low_price * 100
    console_log(f"Volatilité calculée: {volatility:.2f}%")

    should_run = (price_change >= THRESHOLD_PERCENT or 
                  high_change >= THRESHOLD_PERCENT or 
                  low_change >= THRESHOLD_PERCENT or 
                  volatility >= THRESHOLD_PERCENT * 2)

    if should_run:
        console_log(f"Seuil de {THRESHOLD_PERCENT}% dépassé. Le script principal sera exécuté.")
        save_last_execution(current_price, high_price, low_price)
    else:
        console_log(f"Seuil de {THRESHOLD_PERCENT}% non atteint. Le script principal ne sera pas exécuté.")

    return should_run

def main_script(scheduled=False):
    logging.info(f'''Début de l'exécution du script principal...''')
    console_log(f'''Début de l'exécution du script principal...''')
    command = ["python", "script-lnmAuto.py"]
    if len(sys.argv) > 1:
        if "oai" in sys.argv:
            command.append("oai")
    if scheduled or "--auto-validate" in sys.argv:
        command.append("--auto-validate")
    
    start_time = datetime.now()

    result = subprocess.run(command, capture_output=True, text=True)
    end_time = datetime.now()
    
    execution_time = (end_time - start_time).total_seconds()
    
    log_message = f"Exécution terminée en {execution_time:.2f} secondes. "
    if result.returncode == 0:
        log_message += "Succès."
        console_log(log_message, "INFO")
    else:
        log_message += f"Erreur (code {result.returncode})."
        console_log(log_message, "ERROR")
    
    logging.info(log_message)
    
    with open(log_file, "a") as f:
        f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sortie du script:\n{result.stdout}\n")
        if result.stderr:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Erreurs:\n{result.stderr}\n")
    
    console_log("Fin de l'exécution du script principal.")

def scheduled_run():
    console_log("Exécution programmée démarrée", "INFO")
    if should_execute():
        main_script(scheduled=True)
    else:
        console_log("Seuil non atteint, pas d'exécution du script principal", "WARNING")
    console_log("Fin de l'exécution programmée", "INFO")

def should_run_always():
    console_log("Vérification de la dernière exécution du script principal...", "INFO")
    if os.path.exists(LAST_EXEC_FILE):
        with open(LAST_EXEC_FILE, 'r') as f:
            data = json.load(f)
        last_exec_time = datetime.fromtimestamp(data.get("timestamp", 0))
        current_time = datetime.now()
        elapsed_time = current_time - last_exec_time
        console_log(f"Temps écoulé depuis la dernière exécution: {elapsed_time}", "INFO")
        # Définir la période maximale entre les exécutions (par exemple, 24 heures)
        if elapsed_time > timedelta(hours=24):
            console_log("Période maximale écoulée. Déclenchement de l'exécution du script principal.", "INFO")
            return True
    else:
        console_log("Aucune exécution précédente trouvée. Déclenchement de l'exécution du script principal.", "INFO")
        return True
    console_log("Exécution récente détectée. Aucune action requise.", "INFO")
    return False

def scheduled_run_alternate():
    console_log("Exécution du second mécanisme de scheduling.", "INFO")
    if should_run_always():
        main_script(scheduled=True)
    else:
        console_log("Aucune exécution nécessaire via le second mécanisme.", "INFO")

if __name__ == "__main__":
    console_log("Démarrage du script de vérification du prix Bitcoin...")
    logging.info("Début du script de vérification du prix Bitcoin...")
    
    if "--scheduled" in sys.argv:
        console_log("Mode programmé activé (exécution toutes les 20 minutes)", "INFO")
        schedule.every(20).minutes.do(scheduled_run)  # Mécanisme principal
        schedule.every().hour.do(scheduled_run_alternate)  # Second mécanisme

        console_log("Première exécution immédiate", "INFO")
        scheduled_run()
        scheduled_run_alternate()  # Exécution immédiate du second mécanisme

        while True:
            schedule.run_pending()
            time.sleep(1)

    else:
        if should_execute():
            main_script()
        else:
            console_log("\nRécapitulatif:", "INFO")
            last_exec = load_last_execution()
            if last_exec:
                btc_data = get_bitcoin_data(datetime.fromtimestamp(last_exec["timestamp"]))
                current_price = btc_data['Close'].iloc[-1]
                high_price = btc_data['High'].max()
                low_price = btc_data['Low'].min()
                
                console_log(f"Dernière exécution : prix = {last_exec['price']:.2f}, haut = {last_exec['high']:.2f}, bas = {last_exec['low']:.2f}", "INFO")
                console_log(f"Prix actuel : {current_price:.2f}, haut = {high_price:.2f}, bas = {low_price:.2f}", "INFO")
                console_log(f"Variation de prix depuis la dernière exécution : {calculate_price_change(last_exec['price'], current_price):.2f}%", "INFO")
                console_log(f"Variation du haut : {calculate_price_change(last_exec['high'], high_price):.2f}%", "INFO")
                console_log(f"Variation du bas : {calculate_price_change(last_exec['low'], low_price):.2f}%", "INFO")
                console_log(f"Volatilité : {((high_price - low_price) / low_price * 100):.2f}%", "INFO")
            else:
                console_log("Aucune donnée de dernière exécution disponible", "WARNING")
    console_log("Fin du script de vérification du prix Bitcoin.")