import requests
import json
from typing import Dict, Optional
import time
from requests.exceptions import RequestException

def get_bitmex_orderbook(depth: int = 25, max_retries: int = 3, retry_delay: float = 1.0) -> Optional[Dict]:
    """
    Fetch BitMEX orderbook data and return structured JSON.
    
    Args:
        depth (int): Orderbook depth (1-500). Defaults to 25.
        max_retries (int): Maximum number of retry attempts
        retry_delay (float): Delay between retries in seconds
    
    Returns:
        dict: Formatted orderbook data with bids and asks
        None: If request fails after all retries
    
    Example response:
    {
        "bids": [
            {"price": float, "size": int},
            ...
        ],
        "asks": [
            {"price": float, "size": int},
            ...
        ],
        "timestamp": str
    }
    """
    
    # Validate depth parameter
    if not 1 <= depth <= 500:
        raise ValueError("Depth must be between 1 and 500")
        
    url = f"https://www.bitmex.com/api/v1/orderBook/L2"
    params = {
        "symbol": "XBTUSD",
        "depth": depth
    }
    headers = {
        "Accept": "application/json"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Structure orderbook
            orderbook = {
                "bids": [],
                "asks": [],
                "timestamp": response.headers.get("Date", "")
            }
            
            # Process orders
            for order in data:
                order_data = {
                    "price": float(order["price"]),
                    "size": int(order["size"])
                }
                
                if order["side"] == "Buy":
                    orderbook["bids"].append(order_data)
                else:
                    orderbook["asks"].append(order_data)
            
            # Sort orders
            orderbook["bids"] = sorted(orderbook["bids"], key=lambda x: x["price"], reverse=True)
            orderbook["asks"] = sorted(orderbook["asks"], key=lambda x: x["price"])
            
            return orderbook

        except RequestException as e:
            if attempt == max_retries - 1:
                print(f"Failed to fetch BitMEX orderbook after {max_retries} attempts: {str(e)}")
                return None
            
            time.sleep(retry_delay)
            continue
            
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            print(f"Error processing BitMEX response: {str(e)}")
            return None
        
