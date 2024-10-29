import anthropic
from dotenv import load_dotenv
import os
load_dotenv()
import json
from tokencost import calculate_prompt_cost, calculate_completion_cost
import re
import colorama
from colorama import Fore, Back, Style
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

colorama.init(autoreset=True)

model = "claude-3-5-sonnet-20241022"

api_key = os.getenv("ANTRHOPIC_API_KEY")

client = anthropic.Anthropic(
    api_key=api_key
)

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





@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(anthropic.InternalServerError),
    before_sleep=lambda retry_state: print(f"Retrying in {retry_state.next_action.sleep} seconds...")
)
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
            "role": "user",
            "content": text + system_prompt + custom_instruction
        }
    ]

    while True:
        try:
            message = client.messages.create(
                model=model,
                system=system_prompt,
                max_tokens=8192,
                temperature=0,
                messages=messages
            )

            assistant_response = message.content[0].text
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

        except anthropic.InternalServerError as e:
            print(f"Encountered error: {e}")
            raise
    
    return full_response



def analys_past_data(past_data_short,past_data_medium="", past_data_long="", data_history_short="", data_history="", data_history_long=""):
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
    past_data_analys = get_response(message, "past_data")
    print(f"{Fore.GREEN}Analyse des données passées - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{past_data_analys}{Style.RESET_ALL}\n")
    
    try:
        prompt_cost = calculate_prompt_cost(message, model)
        completion_cost = calculate_completion_cost(past_data_analys, model)

    except ValueError as e:
        prompt_cost = 0
        completion_cost = 0
    print(f"{Fore.CYAN}Coûts - Prompt : {prompt_cost}, Completion : {completion_cost}{Style.RESET_ALL}\n")
    return past_data_analys, prompt_cost, completion_cost


def analysClaudeV4(data, user_balance, whitelist, technical_data,past_data, active_positions, open_positions):
    prompt_template = read_template_from_file("./prompt_template.txt")
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
    data = get_response(message, "final")
    print(f"{Fore.GREEN}Analyse finale - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{data}{Style.RESET_ALL}\n")
    try:
        prompt_cost = calculate_prompt_cost(message, model)
        completion_cost = calculate_completion_cost(data, model)

    except ValueError as e:
        prompt_cost = 0
        completion_cost = 0

    return data, prompt_cost, completion_cost







def analyze_price_action(data_history_short, data_history, data_history_long, technical_data_short, technical_data, technical_data_long):
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
    technical_analysis = get_response(message, "price_action")
    
    print(f"{Fore.GREEN}Analyse Price Action - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{technical_analysis}{Style.RESET_ALL}\n")
    try:
        prompt_cost = calculate_prompt_cost(message, model)
        completion_cost = calculate_completion_cost(technical_analysis, model)

    except ValueError as e:
        prompt_cost = 0
        completion_cost = 0

    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
    
    
    return technical_analysis, prompt_cost, completion_cost

