import json
import os
from datetime import datetime, timedelta
from parse import filter_order_history


def read_order_history(days_back=30):
    filename = "order_history.txt"
    history = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    try:
        with open(filename, "r") as file:
            for line in file:
                order = json.loads(line.strip())
                order_date = datetime.strptime(order['timestamp'], "%Y-%m-%d %H:%M:%S")
                if order_date >= cutoff_date:
                    history.append(order)
    except FileNotFoundError:
        print(f"Fichier {filename} non trouvé. L'historique sera vide.")
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON dans {filename}. Certaines entrées peuvent être ignorées.")
        print(e)
        print('=============================================================================================')

    return history



def save_order_history(order_type, order_data):
    filename = "order_history.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    history_entry = {
        "timestamp": timestamp,
        "type": order_type,
        "data": order_data
    }
    
   
    with open(filename, "a") as file:
        json_data = json.dumps(history_entry)
        print("to save")
        print(json_data)
        file.write(json_data + "\n")

def identify_open_orders(positions):
    open_orders = []
    for p in positions:
        try:
            data = json.loads(p['data'])
            if not data.get('closed', False):
                open_orders.append(p)
        except json.JSONDecodeError:
            print(f"Erreur de décodage JSON pour la position: {p}")
        except KeyError:
            print(f"Clé 'data' manquante dans la position: {p}")
    return open_orders


def identify_missing_closed_orders(formatted_output, history):
    missing_closed_orders = []
    
    for closed_position in formatted_output["closed_positions"]["positions"]:
        order_id = closed_position['id']
        created_found = False
        closed_found = False
        
        for entry in history:
            try:
                data = entry['data']
                if data['id'] == order_id:
                    if entry['type'] == 'created':
                        created_found = True
                    elif entry['type'] == 'closed':
                        closed_found = True
                    
                    if created_found and closed_found:
                        break
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Erreur lors du traitement de l'entrée: {entry}. Erreur: {e}")
        
        if created_found and not closed_found:
            missing_closed_orders.append(closed_position)
            save_order_history(order_type="closed",order_data=closed_position)
    
    

# Fonction principale
def update_history(formatted_output, history_filename):
    # Lire l'historique existant
    #history = read_history_file(history_filename)
    history = read_order_history(200)
    
    
    #open_orders = identify_open_orders(history)
    history = filter_order_history(history)
    identify_missing_closed_orders(formatted_output=formatted_output,history=history)
    
    
    
def find_not_closed_orders_old(orders):
    open_orders = []
    closed_order_ids = set()
    created_order_ids = set()
    for event in orders:
        if event['type'] == 'closed':
            closed_order_ids.add(event['data']['id'])
        if event['type'] == 'created':
            created_order_ids.add(event['data']['id'])
    for event in orders:
        if event['type'] == 'created' or event['type'] == 'updated':
            order_id = event['data']['id']
            if order_id not in closed_order_ids and order_id in created_order_ids and not event['data']['closed']:
                open_orders.append(event)


    return open_orders


def find_not_closed_orders(orders):
    
    order_dict = {}

    # Premier parcours : stocker les états de chaque ordre
    for event in orders:
        order_id = event['data']['id']
        event_timestamp = datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S')
        
        if event['type'] == 'closed':
            if order_id in order_dict:
                del order_dict[order_id]
        elif event['type'] == 'created':
            order_dict[order_id] = {'created': event, 'updated': None}
        elif event['type'] == 'updated':
            if order_id in order_dict:
                order_dict[order_id]['updated'] = event

    # Deuxième parcours : collecter les ordres actifs
    active_orders = []
    for order_id, events in order_dict.items():
        if events['created']:  # Ne conserver que les ordres avec un 'created'
            active_orders.append(events['created'])
            if events['updated']:
                active_orders.append(events['updated'])

    # Trier les ordres actifs par timestamp
    active_orders.sort(key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'))
    
    active_orders = format_json(active_orders)
    
    return active_orders



from datetime import datetime
import json
def find_closed_orders(orders, time_horizon=None):
  order_dict = {}
  stats = {
      'total_trades': 0,
      'winning_trades': 0,
      'losing_trades': 0,
      'total_pl': 0,
      'avg_pl': 0,
      'win_rate': 0,
      'max_profit': 0,
      'max_loss': 0,
      'avg_leverage': 0,
      'total_leverage': 0
  }

  # Premier parcours : stocker les états de chaque ordre
  for event in orders:
      order_id = event['data']['id']
      event_timestamp = datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S')
      
      if order_id not in order_dict:
          order_dict[order_id] = {
              'created': None, 
              'closed': None, 
              'updates': [], 
              'time_horizon': None
          }
      
      if event['type'] == 'created':
          order_dict[order_id]['created'] = event
          if 'time_horizon' in event['data']:
              order_dict[order_id]['time_horizon'] = event['data']['time_horizon']
      elif event['type'] == 'closed':
          order_dict[order_id]['closed'] = event
      elif event['type'] == 'updated':
          order_dict[order_id]['updates'].append(event)

  # Deuxième parcours : collecter les ordres fermés et calculer les stats
  closed_orders = []
  for order_id, events in order_dict.items():
      if events['created'] and events['closed']:
          closed_event = events['closed']
          profit_loss = closed_event['data'].get('profit_loss', closed_event['data'].get('pl', 0))
          
          # Vérifier si l'ordre a été exécuté (profit/perte non nul)
          if profit_loss != 0:
              # Vérifier si le time_horizon correspond (si spécifié)
              if time_horizon is None or events['time_horizon'] == time_horizon:
                  # Mise à jour des statistiques
                  stats['total_trades'] += 1
                  stats['total_pl'] += profit_loss
                  
                  
                  if profit_loss > 0:
                      stats['winning_trades'] += 1
                      stats['max_profit'] = max(stats['max_profit'], profit_loss)
                  else:
                      stats['losing_trades'] += 1
                      stats['max_loss'] = min(stats['max_loss'], profit_loss)
                  
                  order_events = [events['created']] + events['updates'] + [events['closed']]
                  closed_orders.extend(order_events)

  # Calcul des moyennes et ratios
  if stats['total_trades'] > 0:
      stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
      stats['avg_pl'] = stats['total_pl'] / stats['total_trades']
      stats['avg_leverage'] = stats['total_leverage'] / stats['total_trades']

  # Trier les ordres fermés par timestamp
  closed_orders.sort(key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'))
  
  # Limiter le nombre d'ordres selon l'horizon temporel
  limit = 30 if time_horizon == "short" else 50 if time_horizon == "medium" else 100
  limited_closed_orders = closed_orders[-limit:]

  # Formater les ordres en JSON
  formatted_orders = format_json(limited_closed_orders)
  
  # Ajouter les statistiques au résultat
  result = {
      'orders': formatted_orders,
      'stats': stats
  }
  
  
  return result



def format_json(data):
    # Charger le JSON
    
    
    # Formater chaque élément
    formatted_data = []
    for item in data:
        formatted_item = {
            "timestamp": item.get("timestamp", ""),
            "type": item.get("type", ""),
            "id": item.get("data", {}).get("id", ""),
            "uid": item.get("data", {}).get("uid", ""),
            "order_type": item.get("data", {}).get("type", ""),
            "side": item.get("data", {}).get("side", ""),
            "pl": item.get("data", {}).get("pl") or item.get("data", {}).get("profit_loss", ""),
            "quantity": item.get("data", {}).get("quantity", ""),
            "margin": item.get("data", {}).get("margin", ""),
            "leverage": item.get("data", {}).get("leverage", ""),
            "price": item.get("data", {}).get("price", ""),
            "stoploss": item.get("data", {}).get("stoploss", ""),
            "takeprofit": item.get("data", {}).get("takeprofit", ""),
            "open": item.get("data", {}).get("open", ""),
            "time_horizon": item.get("data", {}).get("time_horizon", ""),
            "reason": item.get("data", {}).get("reason", ""),
        }
        formatted_data.append(formatted_item)
    
    
    # Convertir en JSON formaté
    formatted_json = json.dumps(formatted_data, indent=2)
    #print(formatted_json)
    
    return formatted_json

def update_pl_from_active_positions(not_closed_orders, active_positions):
    active_positions_dict = {pos['id']: pos['pl'] for pos in active_positions}
    
    updated_orders = json.loads(not_closed_orders)
    for order in updated_orders:
        order['pl'] = active_positions_dict.get(order['id'], order.get('pl', 0))
    
    return json.dumps(updated_orders, indent=2)