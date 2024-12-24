import anthropic
from dotenv import load_dotenv
import os
import json
from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd

@dataclass
class AnalysisResult:
    content: str
    prompt_cost: float
    completion_cost: float

class IntegratedTradingAnalyzer:
    def __init__(self):
        load_dotenv()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTRHOPIC_API_KEY"))
        self.model = "claude-3-sonnet-20240229"
        self.context_history = []
        
    def _calculate_costs(self, prompt: str, completion: str) -> Tuple[float, float]:
        # Implement your token cost calculation here
        # This is a placeholder implementation
        prompt_cost = len(prompt) * 0.0001
        completion_cost = len(completion) * 0.0001
        return prompt_cost, completion_cost

    def _format_dataframe(self, df: pd.DataFrame) -> str:
        """Format DataFrame for prompt input"""
        return df.to_string(index=True, max_rows=50)

    def _get_system_prompt(self, analysis_type: str) -> str:
        """Get appropriate system prompt based on analysis type"""
        base_prompt = """You are an expert cryptocurrency trading analyst. 
        Analyze the provided data thoroughly and provide detailed insights."""
        
        type_specific = {
            "technical": "\nFocus on technical indicators, price patterns, and market trends.",
            "historical": "\nAnalyze past trading performance and identify patterns in successful trades.",
            "integrated": "\nProvide a comprehensive analysis combining technical and historical data."
        }
        
        return base_prompt + type_specific.get(analysis_type, "")

    def _analyze(self, prompt: str, analysis_type: str) -> AnalysisResult:
        """Core analysis method"""
        system_prompt = self._get_system_prompt(analysis_type)
        
        message = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            max_tokens=4096,
            temperature=0,
            messages=[
                *self.context_history,
                {"role": "user", "content": prompt}
            ]
        )
        
        response = message.content[0].text
        prompt_cost, completion_cost = self._calculate_costs(prompt, response)
        
        # Update context history
        self.context_history.append({"role": "user", "content": prompt})
        self.context_history.append({"role": "assistant", "content": response})
        
        # Maintain context window size
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]
            
        return AnalysisResult(response, prompt_cost, completion_cost)

    def analyze_technical(self, 
                        price_data_short: pd.DataFrame,
                        price_data_medium: pd.DataFrame,
                        price_data_long: pd.DataFrame,
                        technical_indicators: Dict[str, pd.DataFrame]) -> AnalysisResult:
        """Analyze technical data across multiple timeframes"""
        prompt = f"""
        Analyze the following market data across different timeframes:
        
        Short-term Price Data:
        {self._format_dataframe(price_data_short)}
        
        Medium-term Price Data:
        {self._format_dataframe(price_data_medium)}
        
        Long-term Price Data:
        {self._format_dataframe(price_data_long)}
        
        Technical Indicators:
        {json.dumps(technical_indicators, indent=2)}
        
        Provide a comprehensive technical analysis with specific focus on:
        1. Trend identification across timeframes
        2. Support and resistance levels
        3. Technical indicator signals
        4. Potential entry and exit points
        
        Enclose your analysis within <technical_analysis></technical_analysis> tags.
        """
        
        return self._analyze(prompt, "technical")

    def analyze_historical_performance(self,
                                    closed_orders_short: List[Dict],
                                    closed_orders_medium: List[Dict],
                                    closed_orders_long: List[Dict],
                                    price_history: Optional[pd.DataFrame] = None) -> AnalysisResult:
        """Analyze historical trading performance"""
        prompt = f"""
        Analyze the following historical trading data:
        
        Short-term Closed Orders:
        {json.dumps(closed_orders_short, indent=2)}
        
        Medium-term Closed Orders:
        {json.dumps(closed_orders_medium, indent=2)}
        
        Long-term Closed Orders:
        {json.dumps(closed_orders_long, indent=2)}
        
        {f'Price History:\n{self._format_dataframe(price_history)}' if price_history is not None else ''}
        
        Provide a detailed analysis of trading performance with focus on:
        1. Win/loss ratios across timeframes
        2. Most successful strategies
        3. Common patterns in profitable trades
        4. Risk management effectiveness
        
        Enclose your analysis within <past_data_analys></past_data_analys> tags.
        """
        
        return self._analyze(prompt, "historical")

    def analyze_integrated(self,
                         technical_analysis: str,
                         historical_analysis: str,
                         current_positions: List[Dict],
                         open_orders: List[Dict],
                         user_balance: int,
                         whitelist: List[str]) -> AnalysisResult:
        """Perform integrated analysis and generate trading recommendations"""
        prompt = f"""
        Based on the following analyses and current market state:
        
        Technical Analysis:
        {technical_analysis}
        
        Historical Performance Analysis:
        {historical_analysis}
        
        Current Positions:
        {json.dumps(current_positions, indent=2)}
        
        Open Orders:
        {json.dumps(open_orders, indent=2)}
        
        User Balance: {user_balance} satoshis
        Whitelist: {json.dumps(whitelist)}
        
        Provide comprehensive trading recommendations including:
        1. Orders to close
        2. Orders to cancel
        3. New orders to create
        4. Orders to update
        
        Ensure all recommendations follow risk management guidelines and consider:
        - Position sizing relative to account balance
        - Risk-reward ratios (1:2 for short-term, 1:3 for long-term)
        - Maximum leverage guidelines
        - Fee impact on profitability
        
        Format your response using the specified JSON structure within appropriate XML tags.
        """
        
        return self._analyze(prompt, "integrated")