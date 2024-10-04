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
model_o1 = "o1-preview"
model = "gpt-4o-2024-08-06"

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
   - for short term, orders should maintain a risk-reward ratio around  1 : 2 (mean for 1 USD web expect 2 USD).
   - for long term, orders should maintain a risk-reward ratio around  1 : 3 (mean for 1 USD web expect 3 USD).
   - Factor in opening fees and carry fees to ensure net profits after fees remain positive.
   - Avoid recommendations that result in negative profits after fees unless necessary for risk mitigation.

2. **Leverage Optimization**:
   - Recommend leverage between 2x and 20x based on market conditions.
   - Use higher leverage (15-20x) for short-term trades and lower leverage for long-term positions, with clear justifications.

3. **Stop Loss and Take Profit Placement**:
   - Set stop losses to avoid false triggers due to Bitcoin fakeouts (can be between 1000-3000 USD).
   - Ensure that take profit levels are realistic and align with market trends, support, resistance and time horizons.

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
    
    technical_analysis = get_response_o1(message).choices[0].message.content
    print(f"{Fore.GREEN}Analyse Price Action - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{technical_analysis}{Style.RESET_ALL}\n")
    prompt_cost = calculate_prompt_cost(message, model_o1)
    completion_cost = calculate_completion_cost(technical_analysis, model_o1)
    
    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
    return technical_analysis, prompt_cost, completion_cost


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
    model=model_o1,
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


def analys_past_data_aoi(past_data):
    message=f'''
You are an AI cryptocurrency market analyst specializing in order analysis. Your task is to analyze previous orders executed by other AI Agents in the Bitcoin market. You will be provided with past order data, and you need to give a precise analysis of the successes and failures.

Here is the past order data you will analyze:
<past_order>
{past_data}
</past_order>

To complete this task, follow these steps:

    Carefully review the past order data provided, paying attention to all fields including timestamp, type, order_type, side, pl, quantity, margin, leverage, price, stoploss, takeprofit, and reason.
    Identify patterns of successful and unsuccessful orders, considering both created and closed orders.
    Analyze the factors that contributed to the success or failure of each order, including the reasoning provided in the "reason" field.
    Consider market conditions, timing, order size, leverage used, and the relationship between entry price, stoploss, and takeprofit levels.
    Evaluate the overall performance of the AI Agents based on their orders, considering both long (buy) and short (sell) positions.

In your analysis, make sure to:

    Provide specific examples from the data to support your observations, using order IDs when relevant.
    Highlight any recurring strategies or mistakes, such as repeated entries at certain price levels or common reasons for closing positions.
    Offer insights into what made certain orders successful and others unsuccessful, considering the balance between risk (stoploss) and reward (takeprofit).
    Consider the broader market context if apparent from the data, including any trends in Bitcoin price movement that can be inferred from the orders.
    Analyze the use of different order types (market vs limit) and their effectiveness.
    Evaluate the risk management strategies employed, including the use of leverage and the setting of stoploss and takeprofit levels.

Present your analysis in a clear, structured format. Begin with an overview of your findings, followed by detailed observations on successes and failures. Include sections on:

    Entry strategies
    Exit strategies
    Risk management
    Market timing
    Use of leverage
    Overall performance trends

Conclude with any overall patterns or trends you've identified and potential recommendations for improving the trading strategy.

Your entire response should be enclosed within <past_data_analys> tags. Do not include the opening and closing tags in your response; they will be added automatically.

Remember, your goal is to provide a precise and insightful analysis of the successes and failures in the past Bitcoin trading data. Focus on delivering actionable insights that could be used to improve future trading strategies in the cryptocurrency market.

    '''
    print(f"{Fore.YELLOW}Analyse des données passées - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    past_data_analys = get_response(message).choices[0].message.content
    print(f"{Fore.GREEN}Analyse des données passées - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{past_data_analys}{Style.RESET_ALL}\n")
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(past_data_analys, model)
    
    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
    return past_data_analys, prompt_cost, completion_cost


def customize_final_prompt_gpt(past_data):
    prompt_template = read_template_from_file("./prompt_template.txt")
    message = f'''
Based on the data inside <past_data>, adapt the template prompt inside <template>. 
The new prompt should remain in English and be placed inside <new_prompt_template>.

<past_data>
{past_data}
</past_data>

<template>
{prompt_template}
</template
'''
    print(f"{Fore.YELLOW}Personnalisation du prompt final - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    data = get_response(message).choices[0].message.content
    print(f"{Fore.GREEN}Nouveau prompt :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{data}{Style.RESET_ALL}\n")
    
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(data, model)
    return data, prompt_cost, completion_cost


def analysGptV2(data, user_balance, whitelist, technical_data,past_data, active_positions, open_positions, prompt_template):
    prompt_template = str(prompt_template)
    variables = {
        'data': data,
        'user_balance': user_balance,
        'whitelist': whitelist,
        'technical_data': technical_data,
        'past_data': past_data,
        'active_positions': active_positions,
        'open_positions': open_positions
    }
    message = safe_format(prompt_template, **variables)
    
    print(f"{Fore.YELLOW}Analyse finale - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    data = get_response_o1(message).choices[0].message.content
    print(f"{Fore.GREEN}Analyse finale - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{data}{Style.RESET_ALL}\n")
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(data, model)
    return data, prompt_cost, completion_cost


def analyze_price_action_oai(data_history_short, data_history, data_history_long, technical_data_short, technical_data, technical_data_long):
    message = f'''
    You are a professional stock market analyst specializing in bitcoin and price action analysis. Your task is to thoroughly analyze bitcoin price data, as well as the RSI and MACD technical indicators, to provide a detailed analysis for short, medium, and long term.

Input data for your analysis:

<history_price_short>
{data_history_short}
</history_price_short>

<history_price>
{data_history}
</history_price>

<history_price_long>
{data_history_long}
</history_price_long>

<technical_price_short>
{technical_data_short}
</technical_price_short>

<technical_price>
{technical_data}
</technical_price>

<technical_data_long>
{technical_data_long}
</technical_data_long>

For each time horizon (short, medium, and long term), analyze and provide the following information:

    Key resistance and support levels
    Current trend and trend strength
    Market configuration (range, bullish trend, bearish trend, etc.)
    Significant Japanese candlestick patterns
    Potential divergences between price and technical indicators (RSI, MACD)
    Volumes and their interpretation, including identification of low volume cycles
    Market momentum
    Relevant Fibonacci levels
    Anticipation of potential future movements

Analysis procedure for each time horizon:

    Carefully examine historical and technical data.
    Identify key support and resistance levels by observing important turning points.
    Determine the current trend and its strength by analyzing price direction and technical indicators.
    Assess the market configuration considering the trend and recent price movements.
    Spot significant Japanese candlestick patterns and their implications.
    Look for divergences between price and technical indicators.
    Analyze volumes and their impact on price movements, paying special attention to identifying low volume cycles and their significance.
    Evaluate market momentum using indicators and price movements.
    Identify relevant Fibonacci levels for retracements and extensions.
    Formulate anticipations of potential future movements based on the overall analysis.

Present your complete technical analysis between the tags <technical_analysis> and </technical_analysis>. Structure your analysis into three distinct sections: short term, medium term, and long term. For each section, provide the requested information in a clear, concise, and reasoned manner.

Conclude your analysis with an overall summary and strategic recommendations for traders and investors.

Added directive to reduce hallucinations:
To reduce hallucinations, do not invent or provide any metrics or specific numerical values if you are not certain you can determine them with certainty based on the given data. If you are unsure about a specific metric or value, state that it cannot be determined with the available information.
    '''
    print(f"{Fore.YELLOW}Analyse Price Action - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    technical_analysis = get_response(message).choices[0].message.content
    print(f"{Fore.GREEN}Analyse Price Action - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{technical_analysis}{Style.RESET_ALL}\n")
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(technical_analysis, model)
    
    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
    return technical_analysis, prompt_cost, completion_cost
