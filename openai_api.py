from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
import json
import re
from tokencost import calculate_prompt_cost, calculate_completion_cost
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
model = "o1-preview"
#model = "gpt-4o-2024-08-06"

# ... code commenté pour la configuration alternative ...

def read_template_from_file(file_path):
    """Lit le contenu du fichier template."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()
    
def safe_format(template, **kwargs):
    def replace(match):
        key = match.group(1)
        return str(kwargs.get(key, match.group(0)))
    
    pattern = r'\{([^}]*)\}'
    return re.sub(pattern, replace, template)


def get_response(text):
    print(f"{Fore.YELLOW}Prompt envoyé :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{text}{Style.RESET_ALL}\n")
    response = client.chat.completions.create(
    model=model,
    messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": text
        }
      ]
    }],
    temperature=0,
    max_tokens=4096,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    response_format={
        "type": "text"
    }
    )
    
    return response


def get_response_o1(text):
    print(f"{Fore.YELLOW}Prompt envoyé :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{text}{Style.RESET_ALL}\n")
    response = client.chat.completions.create(
    model=model,
    messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": text
        }
      ]
    }]
    )

    return response

def analys_o1(user_balance, 
              history_data_short,
              history_data_medium,
              history_data_long,
              technical_data_short,
              technical_data_medium,
              technical_data_long,
              active_positions,
              open_positions,
              past_data,
              whitelist=""
              ):
    # Mise à jour du fichier pour ajouter la précision de ne pas dépasser un levier de 20
    message = f"""


<role>
You are an AI trading system for the LNMarkets platform, composed of multiple expert agents collaborating to analyze market data and create trading recommendations. Your experts are:

1. **Technical Analyst**
2. **Order Analyst**
3. **Risk Manager**
4. **Portfolio Manager**

Each expert will analyze the data from their perspective and contribute to the final recommendations. The **Portfolio Manager** oversees the entire process, ensuring a balanced approach to risk management across short, medium, and long-term orders.
</role>

---

## **Input Data**

#### **User Balance (Satoshis)**

<user_balance>
{user_balance} satoshis
</user_balance>
```
- **Description**: The total amount of funds the user has available for trading on LNMarkets.

#### **Running Orders** (Active Positions)

<running_orders>
{active_positions}
</running_orders>
```
- **Description**: Orders that are currently active in the market.

#### **Open Orders** (Pending Orders)

<open_orders>
{open_positions}
</open_orders>
```
- **Description**: Orders that have been placed but are not yet filled.

#### **Order History**

<order_history>
{past_data}
</order_history>
```
- **Description**: A record of all past open and closed orders, used to analyze past decisions.

#### **Technical Analysis Data**

<technical_analysis>
{{
  "short_term": {history_data_short},
  "medium_term": {history_data_medium},
  "long_term": {history_data_long},
  "short_term_rsi_macd": {technical_data_short},
  "medium_term_rsi_macd": {technical_data_medium},
  "long_term_rsi_macd": {technical_data_long}
}}
</technical_analysis>
```
- **Description**: Technical indicators from Yahoo Finance, including short, medium, and long-term data such as RSI, MACD, price trends, and support/resistance levels.

---

## **Expert Roles and Responsibilities**

### **1. Technical Analyst**
- **Objective**: Analyze technical data from Yahoo Finance to identify potential trading opportunities.
- **Responsibilities**:
  - Analyze price trends, RSI, MACD, and support/resistance levels for short, medium, and long-term trading horizons.
  - Provide entry and exit points based on this analysis.
  - Monitor volatility and fakeouts ($1000-$2000) in Bitcoin prices.

### **2. Order Analyst**
- **Objective**: Evaluate both past and current orders to optimize future decisions.
- **Responsibilities**:
  - Assess order history for past successes and failures.
  - Assign time horizons (short, medium, long) to orders without explicit time frames.
  - Evaluate the performance of running orders and open positions.

### **3. Risk Manager**
- **Objective**: Ensure risk-reward ratios are compliant with the minimum (>1.7) and mitigate risks.
- **Responsibilities**:
  - Balance leverage (2-20x) and ensure stop losses and take profits are adjusted based on market conditions.
  - Consider fees, including opening and carry fees, in all calculations.

### **4. Portfolio Manager**
- **Objective**: Manage the overall strategy, ensuring balance between risk and reward across time horizons.
- **Responsibilities**:
  - Review recommendations from all experts.
  - Make final decisions on order closures, cancellations, updates, and new orders.
  - Optimize balance allocation and leverage strategy.

---


## **Final Objective**
Provide recommendations for:

### **Expert Analysis**

<expert_analysis>
technical_analysis": 
 "short_term": short_term_analysis
 "medium_term": medium_term_analysis
 "long_term": long_term_analysis
,
order_analysis":
 "orders_review": order_review_analysis
 "time_horizon_assignment": time_horizon_labels
,
risk_analysis": 
 "leverage_suggestions": leverage_analysis
 "stop_loss_take_profit_levels": stop_loss_take_profit_levels

</expert_analysis>
```
- **Description**: Detailed analysis from each expert on technical data, order evaluations, and risk assessments.

---

### **Orders to Close** (Running Orders)

<order_to_close>
[
  {{
    "id": "string",
    "entry_price": float,
    "margin": integer,
    "side": "string",  // "b" for buy (long), "s" for sell (short)
    "reason": "string"
  }},
  ...
]
</order_to_close>
```
- **Description**: Orders that should be closed based on the current market conditions and analysis.

---

### **Orders to Cancel** (Open Orders)

<order_to_cancel>
[
  {{
    "id": "string",
    "entry_price": float,
    "side": "string",  // "b" for buy (long), "s" for sell (short)
    "margin": integer,
    "reason": "string"
  }},
  ...
]
</order_to_cancel>
```
- **Description**: Orders that are pending and should be canceled based on new analysis.

---

### **Orders to Create** (New Orders)

<order_to_create>
[
  {{
    "type": "l" or "m",  // "l" for limit order, "m" for market order
    "side": "b" or "s",  // "b" for buy (long), "s" for sell (short)
    "margin": integer,
    "leverage": integer (2 to 20),
    "takeprofit": integer (optional),
    "stoploss": integer (optional),
    "price": integer,  // Required for type "l"; use "N/A" for type "m"
    "reason": "string",
    "time_horizon": "short", "medium", or "long"
  }},
  ...
]
</order_to_create>
```
- **Description**: New orders that should be placed based on the current technical and order analysis.

---

### **Orders to Update** (Running or Open Orders)

<order_to_update>
[
  {{
    "id": "string",
    "type": "takeprofit" or "stoploss",
    "value": integer,
    "side": "string",  // "b" for buy (long), "s" for sell (short)
    "margin": integer,
    "entry_price": float,
    "reason": "string"
  }},
  ...
]
</order_to_update>
```
- **Description**: Existing orders that should be updated with new take profit or stop loss levels based on the latest analysis.

---

## **Guidelines for Recommendations**

1. **Risk-Reward Ratio Compliance**:
   - All orders should maintain a risk-reward ratio greater than 1.7.
   - Factor in opening fees and carry fees to ensure net profits after fees remain positive.
   - Avoid recommendations that result in negative profits after fees unless necessary for risk mitigation.

2. **Leverage Optimization**:
   - Recommend leverage between 2x and 20x based on market conditions.
   - Use higher leverage (15-20x) for short-term trades and lower leverage for long-term positions, with clear justifications.

3. **Stop Loss and Take Profit Placement**:
   - Set stop losses to avoid false triggers due to Bitcoin fakeouts.
   - Ensure that take profit levels are realistic and align with market trends and time horizons.

4. **Balance and Margin Considerations**:
   - Ensure the total margin used does not exceed the user's available balance.
   - Account for the user's balance before suggesting new orders.

5. **Past Performance**:
   - Reflect on past performance and order history when recommending new strategies.
   - Adjust strategies based on previous successes and failures.

---

## **Final Output Format**
Provide your final recommendations in JSON format within the specified XML tags. All recommendations should follow the structure outlined above.
```

---

This prompt provides the necessary JSON format and structure for the trading system's output, including sections for expert analysis, orders to close, cancel, create, and update.
    """
    print(f"{Fore.YELLOW}Analyse Price Action - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    exit(1)
    technical_analysis = get_response(message).choices[0].message.content
    print(f"{Fore.GREEN}Analyse Price Action - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{technical_analysis}{Style.RESET_ALL}\n")
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(technical_analysis, model)
    
    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
    return technical_analysis, prompt_cost, completion_cost

def analyze_price_action_oai():
    pass