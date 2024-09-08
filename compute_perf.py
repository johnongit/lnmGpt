import json
from datetime import datetime
from lnmarkets import rest
from history import read_order_history, update_history
import os
from dotenv import load_dotenv
import json
load_dotenv()

lnm_key = os.getenv("LNM_KEY")
lnm_secret = os.getenv("LNM_SECRET")
lnm_passphrase = os.getenv("LNM_PASS")

# Configurez vos informations d'authentification
options = {
    'key': lnm_key,
    'secret': lnm_secret,
    'passphrase': lnm_passphrase
}
lnm = rest.LNMarketsRest(**options)

def format_position(position):
    return {
        "id": position.get('id', 'N/A'),
        "type": "Market" if position.get('type') == 'm' else "Limit",
        "side": "Buy" if position.get('side') == 'b' else "Sell",
        "quantity": position.get('quantity', 'N/A'),
        "entry_price": position.get('price', 'N/A'),
        "leverage": position.get('leverage', 'N/A'),
        "profit_loss": position.get('pl', 'N/A'),
        "liquidation_price": position.get('liquidation', 'N/A')
    }

def read_whitelist(filename='whitelist.txt'):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]
    
def calculate_performance(entry_price, exit_price, side, quantity, leverage, profit_loss=None, margin=None):
    if profit_loss is not None and margin is not None:
        # Calcul basé sur le profit/perte et la marge
        if margin != 0:
            return (profit_loss / margin) * 100
        else:
            print(f"Avertissement : Marge nulle pour un ordre avec profit/perte de {profit_loss}")
            return 0  # ou une autre valeur par défaut
    elif exit_price is not None:
        # Calcul basé sur les prix d'entrée et de sortie
        if side == 'b':  # Buy
            return (exit_price - entry_price) / entry_price * 100 * leverage
        elif side == 's':  # Sell
            return (entry_price - exit_price) / entry_price * 100 * leverage
    return 0

def process_orders(filename):
    orders = {}
    performances = []
    total_pl = 0

    with open(filename, 'r') as file:
        for line in file:
            trade_info = json.loads(line)
            data = trade_info['data']
            
            if trade_info['type'] == 'created':
                orders[data['id']] = {
                    'entry_price': float(data['price']),
                    'side': data['side'],
                    'quantity': float(data['quantity']),
                    'leverage': float(data['leverage']),
                    'margin': float(data['margin'])
                }
            
            elif trade_info['type'] == 'closed':
                if data['id'] in orders:
                    entry_data = orders[data['id']]
                else:
                    print(f"Avertissement : Données d'entrée manquantes pour l'ordre {data['id']}")
                    continue
                
                if 'profit_loss' in data:
                    pl = float(data['profit_loss'])
                    if pl == 0:
                        continue
                    margin = entry_data['margin']
                    if margin != 0:
                        performance = (pl / margin) * 100
                    else:
                        print(f"Avertissement : Marge nulle pour l'ordre {data['id']}")
                        performance = 0
                elif 'pl' in data:
                    pl = float(data['pl'])
                    if pl == 0:
                        continue
                    margin = entry_data['margin']
                    if margin != 0:
                        performance = (pl / margin) * 100
                    else:
                        print(f"Avertissement : Marge nulle pour l'ordre {data['id']}")
                        performance = 0
                else:
                    print(f"Avertissement : Profit/Perte manquant pour l'ordre {data['id']}")
                    continue
                
                performances.append(performance)
                total_pl += pl
                
                print(f"Ordre {data['id']}:")
                print(f"  Side: {'Buy' if entry_data['side'] == 'b' else 'Sell'}")
                print(f"  Entry Price: {entry_data['entry_price']}")
                print(f"  Performance: {performance:.2f}%")
                print(f"  Profit/Loss: {pl}")
                print(f"  Leverage: {entry_data['leverage']}x")
                print(f"  Margin: {margin}")
                print()
                
                del orders[data['id']]

    return performances, total_pl

whitelist = read_whitelist()
active_positions_raw = lnm.futures_get_trades({'type': 'running'})
closed_positions_raw = lnm.futures_get_trades({'type': 'closed', 'limit': 1000})
open_positions_raw = lnm.futures_get_trades({'type': 'open'})
active_positions = json.loads(active_positions_raw)
active_positions = [position for position in active_positions if position['id'] not in whitelist]


closed_positions = json.loads(closed_positions_raw)
open_positions = json.loads(open_positions_raw)
open_positions = [position for position in open_positions if position['id'] not in whitelist]
formatted_output = {
    "active_positions": {"total": len(active_positions), "positions": []},
    "closed_positions": {"total": len(closed_positions), "positions": []},
    "open_positions": {"total": len(open_positions), "positions": []}
}
for key in formatted_output:
    formatted_output[key]["positions"] = [format_position(p) for p in locals()[key]]

update_history(formatted_output=formatted_output, history_filename="order_history.txt")

# Traitement des ordres
performances, total_pl = process_orders('order_history.txt')

# Calcul et affichage des statistiques globales
if performances:
    average_performance = sum(performances) / len(performances)
    print("Résumé global:")
    print(f"Nombre total d'ordres fermés: {len(performances)}")
    print(f"Performance moyenne: {average_performance:.2f}%")
    print(f"Profit/Perte total: {total_pl:.2f}")
else:
    print("Aucun ordre fermé n'a été trouvé.")