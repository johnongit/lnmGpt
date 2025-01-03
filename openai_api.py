from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
import json
import re
from tokencost import calculate_prompt_cost, calculate_completion_cost
import colorama
from colorama import Fore, Back, Style
import datetime
colorama.init(autoreset=True)

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
model_o1 = "o1-preview"
model = "chatgpt-4o-latest"
#model = "gpt-4o-mini"

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




def get_response(text, type=""):
    custom_instruction = ""
    if type == "past_data":
        custom_instruction = "Don't forget your entire analysis MUST be enclosed within <past_data_analys></past_data_analys> tags"
    elif type == "final":
        custom_instruction = "Don't forget orders MUST be enclosed within <order_to_close></order_to_close>,<order_to_cancel></order_to_cancel>, <order_to_create></order_to_create> and <order_to_update></order_to_update> tags"
    elif type == "price_action":
        custom_instruction = "Don't forget your entire analysis MUST be enclosed within <technical_analysis></technical_analysis> tags"
    full_response = ""

    continue_token = "<CONTINUE>"
  
    system_prompt = f'''
    
    You are an AI assistant that explains your reasoning step by step, incorporating dynamic Chain of Thought (CoT), reflection, and verbal reinforcement learning. Follow these instructions:

1. Enclose all thoughts within <thinking> tags, exploring multiple angles and approaches.
2. Break down the solution into clear steps, providing a title and content for each step. Use a maximum of 20 steps.
3. After each step, decide if you need another step or if you're ready to give the final answer.
4. Continuously adjust your reasoning based on intermediate results and reflections, adapting your strategy as you progress.
5. Regularly evaluate your progress, being critical and honest about your reasoning process.
6. Assign a quality score between 0.0 and 1.0 to guide your approach:
- 0.8+: Continue current approach
- 0.5-0.7: Consider minor adjustments
- Below 0.5: Seriously consider backtracking and trying a different approach
7. If unsure or if your score is low, backtrack and try a different approach, explaining your decision.
8. For mathematical problems, show all work explicitly using LaTeX for formal notation and provide detailed proofs.
9. Explore multiple solutions individually if possible, comparing approaches in your reflections.
10. Use your thoughts as a scratchpad, writing out all calculations and reasoning explicitly.
11. Use at least 3 methods to derive the answer and consider alternative viewpoints.
12. Be aware of your limitations as an AI and what you can and cannot do.

After every 3 steps, perform a detailed self-reflection on your reasoning so far, considering potential biases and alternative viewpoints.

If your response is incomplete, end it with the token "{continue_token}" to indicate there's more to follow.

'''


    messages = [
      {
          "role": "system",
          "content": system_prompt 
      },
      {
          "role": "user",
          "content": text + system_prompt + custom_instruction
      }
    ]

    while True:
        try:
            message = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=4096,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={
                    "type": "text"
                }
            )

            assistant_response = message.choices[0].message.content
            full_response += assistant_response

            messages.append({
                "role": "assistant",
                "content": assistant_response
            })

            if assistant_response.strip().endswith(continue_token):
                full_response = full_response.rsplit(continue_token, 1)[0]
                messages.append({
                    "role": "user",
                    "content": f"{continue_token}"
                })
            else:
                break

        except Exception as e:
            print(f"Encountered error: {e}")
            raise
    
    return full_response




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


def analys_past_data_oai(past_data_short,past_data_medium="", past_data_long="", data_history_short="", data_history="", data_history_long=""):
    message = f'''
You are an AI cryptocurrency market analyst specializing in order analysis. Your task is to analyze previous orders executed by other AI Agents in the Bitcoin market across three different time horizons, with a particular focus on stop-loss effectiveness and positioning.

Here is the past order data you will analyze:
<past_data_short>
{past_data_short}
</past_data_short>

<past_data_medium>
{past_data_medium}
</past_data_medium>

<past_data_long>
{past_data_long}
</past_data_long>

Market Context:
<history_price_short>
{data_history_short}
</history_price_short>

<history_price>
{data_history}
</history_price>

<history_price_long>
{data_history_long}
</history_price_long>

Important Context:
- The trading bot executes at most once per day
- Not all days have executions
- Bitcoin can experience significant price movements (\$1000-\$3000) within a day
- Stop-losses need to account for daily volatility and the bot's execution frequency

For each time horizon, analyze:

1. Stop-Loss Analysis:
 - Calculate the average distance between entry price and stop-loss for both winning and losing trades
 - Identify patterns in stop-loss hits (time of day, market conditions, volatility)
 - Evaluate if stop-losses were too tight given daily Bitcoin volatility
 - Compare stop-loss distances across different market conditions
 - Analyze if wider stop-losses would have resulted in eventual profitable trades
 - Calculate the percentage of losses due to stop-loss hits vs. manual closures

2. Stop-Loss Recommendations:
 - Suggest minimum stop-loss distances based on:
   * Daily Bitcoin volatility (\$1000-\$3000 range)
   * Time horizon of the trade
   * Market conditions (trending vs. ranging)
 - Recommend stop-loss adjustment strategies for different market conditions
 - Propose position sizing adjustments to accommodate wider stop-losses

3. Performance Metrics:
 - Win rate with detailed stop-loss analysis
 - Average profit/loss including stop-loss impact
 - Risk management effectiveness
 - Entry and exit timing accuracy
 - Correlation between stop-loss distance and trade success

4. Market Context Analysis:
 - Impact of volatility on stop-loss hits
 - Relationship between market conditions and optimal stop-loss placement
 - Analysis of false breakouts leading to stop-loss hits
 - Identification of optimal stop-loss zones based on market structure

5. Time Horizon-Specific Analysis:
 Short-term trades (1-3 days):
 - Minimum recommended stop-loss distance
 - Optimal stop-loss placement relative to support/resistance
 - Impact of intraday volatility

 Medium-term trades (4-14 days):
 - Stop-loss positioning for multi-day holds
 - Adjustment for weekly volatility patterns
 - Balance between protection and trade thesis

 Long-term trades (15+ days):
 - Wide stop-loss strategies
 - Major support/resistance consideration
 - Market cycle impact on stop-loss placement

6. Risk Management Recommendations:
 - Position sizing guidelines based on stop-loss distance
 - Leverage adjustment recommendations
 - Stop-loss placement strategies for different market conditions
 - Risk-reward ratio optimization

Present your analysis in a structured format with:
1. Quantitative analysis of stop-loss effectiveness
2. Pattern identification in stop-loss hits
3. Specific recommendations for improvement
4. Time horizon-specific guidelines
5. Risk management framework adjustments

Your analysis must be data-driven and include:
- Specific examples of both successful and failed trades
- Statistical analysis of stop-loss distances
- Clear recommendations for minimum stop-loss distances by time horizon
- Position sizing and leverage recommendations based on stop-loss requirements

Remember that the bot's daily execution frequency means:
- Stop-losses must account for normal daily Bitcoin volatility
- Position sizing must be conservative enough for wider stop-losses
- Risk management must consider the inability to adjust positions intraday

Your entire analysis must be enclosed within <past_data_analys></past_data_analys> tags.

Remember, your goal is to provide a precise and insightful analysis of the successes and failures in the past Bitcoin trading data across short, medium, and long-term strategies. Focus on delivering actionable insights that could be used to improve future trading strategies in the cryptocurrency market, taking into account the unique characteristics and challenges of each time horizon.

    '''
    print(f"{Fore.YELLOW}Analyse des données passées - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    past_data_analys = get_response(message)
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
    data = get_response(message)
    print(f"{Fore.GREEN}Nouveau prompt :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{data}{Style.RESET_ALL}\n")
    
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(data, model)
    return data, prompt_cost, completion_cost


def analysGptV2(data, user_balance, whitelist, technical_data,past_data, active_positions, open_positions,orderbook):
    prompt_template = read_template_from_file("./prompt_template.txt")
    ## get current date in the format day of the month day of the week month year - hour pm/am minute second

    current_date = datetime.datetime.now().strftime("%d %A %B %Y - %I %p %M %S")
    variables = {
        'data': data,
        'user_balance': user_balance,
        'whitelist': whitelist,
        'technical_data': technical_data,
        'past_data': past_data,
        'active_positions': active_positions,
        'open_positions': open_positions,
        'current_date': current_date,
        'orderbook': orderbook
    }
    message = safe_format(prompt_template, **variables)
    
    print(f"{Fore.YELLOW}Analyse finale - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    data = get_response(message)
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
    technical_analysis = get_response(message)
    print(f"{Fore.GREEN}Analyse Price Action - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{technical_analysis}{Style.RESET_ALL}\n")
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(technical_analysis, model)
    
    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
    return technical_analysis, prompt_cost, completion_cost
