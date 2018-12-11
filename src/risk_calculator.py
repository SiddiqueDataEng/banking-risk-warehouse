"""
Banking Risk Analytics - Risk Calculation Engine
Implements credit risk, market risk, and operational risk calculations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CreditRiskCalculator:
    """Calculate credit risk metrics (PD, LGD, EAD)"""
    
    def __init__(self):
        self.pd_model_params = {
            'intercept': -2.5,
            'credit_score_coef': -0.015,
            'debt_ratio_coef': 1.2,
            'delinquency_coef': 0.8
        }
    
    def calculate_pd(self, credit_score: float, debt_ratio: float, 
                     delinquency_count: int) -> float:
        """
        Calculate Probability of Default (PD)
        
        Args:
            credit_score: Credit score (300-850)
            debt_ratio: Debt to income ratio
            delinquency_count: Number of past delinquencies
        
        Returns:
            PD as probability (0-1)
        """
        try:
            logit = (self.pd_model_params['intercept'] +
                    self.pd_model_params['credit_score_coef'] * credit_score +
                    self.pd_model_params['debt_ratio_coef'] * debt_ratio +
                    self.pd_model_params['delinquency_coef'] * delinquency_count)
            
            pd = 1 / (1 + np.exp(-logit))
            return min(max(pd, 0.0001), 0.9999)  # Cap between 0.01% and 99.99%
        
        except Exception as e:
            logger.error(f"Error calculating PD: {e}")
            return 0.05  # Default 5% PD
    
    def calculate_lgd(self, collateral_value: float, exposure: float,
                      recovery_rate: float = 0.4) -> float:
        """
        Calculate Loss Given Default (LGD)
        
        Args:
            collateral_value: Value of collateral
            exposure: Total exposure amount
            recovery_rate: Expected recovery rate
        
        Returns:
            LGD as percentage (0-1)
        """
        try:
            if exposure <= 0:
                return 0.0
            
            unsecured_portion = max(0, exposure - collateral_value)
            secured_portion = min(exposure, collateral_value)
            
            # Assume 80% recovery on secured, recovery_rate on unsecured
            expected_loss = (unsecured_portion * (1 - recovery_rate) +
                           secured_portion * 0.2)
            
            lgd = expected_loss / exposure
            return min(max(lgd, 0.0), 1.0)
        
        except Exception as e:
            logger.error(f"Error calculating LGD: {e}")
            return 0.45  # Default 45% LGD
    
    def calculate_ead(self, current_balance: float, credit_limit: float,
                      utilization_rate: float = 0.75) -> float:
        """
        Calculate Exposure at Default (EAD)
        
        Args:
            current_balance: Current outstanding balance
            credit_limit: Total credit limit
            utilization_rate: Expected utilization at default
        
        Returns:
            EAD amount
        """
        try:
            unused_limit = credit_limit - current_balance
            expected_drawdown = unused_limit * utilization_rate
            ead = current_balance + expected_drawdown
            
            return max(ead, 0.0)
        
        except Exception as e:
            logger.error(f"Error calculating EAD: {e}")
            return current_balance
    
    def calculate_expected_loss(self, pd: float, lgd: float, ead: float) -> float:
        """Calculate Expected Loss (EL = PD * LGD * EAD)"""
        return pd * lgd * ead


class MarketRiskCalculator:
    """Calculate market risk metrics (VaR, CVaR)"""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
    
    def calculate_var(self, returns: np.ndarray, method: str = 'historical') -> float:
        """
        Calculate Value at Risk (VaR)
        
        Args:
            returns: Array of historical returns
            method: 'historical', 'parametric', or 'monte_carlo'
        
        Returns:
            VaR value
        """
        try:
            if method == 'historical':
                return self._historical_var(returns)
            elif method == 'parametric':
                return self._parametric_var(returns)
            elif method == 'monte_carlo':
                return self._monte_carlo_var(returns)
            else:
                raise ValueError(f"Unknown VaR method: {method}")
        
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return 0.0
    
    def _historical_var(self, returns: np.ndarray) -> float:
        """Historical simulation VaR"""
        percentile = (1 - self.confidence_level) * 100
        return np.percentile(returns, percentile)
    
    def _parametric_var(self, returns: np.ndarray) -> float:
        """Parametric (variance-covariance) VaR"""
        mean = np.mean(returns)
        std = np.std(returns)
        z_score = stats.norm.ppf(1 - self.confidence_level)
        return mean + z_score * std
    
    def _monte_carlo_var(self, returns: np.ndarray, n_simulations: int = 10000) -> float:
        """Monte Carlo simulation VaR"""
        mean = np.mean(returns)
        std = np.std(returns)
        simulated_returns = np.random.normal(mean, std, n_simulations)
        return self._historical_var(simulated_returns)
    
    def calculate_cvar(self, returns: np.ndarray) -> float:
        """
        Calculate Conditional Value at Risk (CVaR/Expected Shortfall)
        
        Args:
            returns: Array of historical returns
        
        Returns:
            CVaR value
        """
        try:
            var = self._historical_var(returns)
            # CVaR is the average of losses beyond VaR
            tail_losses = returns[returns <= var]
            return np.mean(tail_losses) if len(tail_losses) > 0 else var
        
        except Exception as e:
            logger.error(f"Error calculating CVaR: {e}")
            return 0.0


class OperationalRiskCalculator:
    """Calculate operational risk using Loss Distribution Approach"""
    
    def calculate_operational_risk_capital(self, 
                                          loss_events: List[Dict]) -> Dict[str, float]:
        """
        Calculate operational risk capital using historical loss data
        
        Args:
            loss_events: List of loss events with 'amount' and 'date'
        
        Returns:
            Dictionary with risk metrics
        """
        try:
            if not loss_events:
                return {'capital_requirement': 0.0, 'expected_loss': 0.0}
            
            losses = np.array([event['amount'] for event in loss_events])
            
            # Calculate statistics
            mean_loss = np.mean(losses)
            std_loss = np.std(losses)
            max_loss = np.max(losses)
            
            # Operational risk capital (simplified)
            # Using 99.9th percentile approach
            capital_requirement = mean_loss + 3 * std_loss
            
            return {
                'expected_loss': mean_loss,
                'std_dev': std_loss,
                'max_loss': max_loss,
                'capital_requirement': capital_requirement,
                'loss_count': len(losses)
            }
        
        except Exception as e:
            logger.error(f"Error calculating operational risk: {e}")
            return {'capital_requirement': 0.0, 'expected_loss': 0.0}


class RegulatoryReporting:
    """Generate regulatory reports (Basel III, CCAR)"""
    
    def __init__(self):
        self.basel_risk_weights = {
            'sovereign': 0.0,
            'bank': 0.2,
            'corporate': 1.0,
            'retail': 0.75,
            'residential_mortgage': 0.35,
            'commercial_real_estate': 1.0
        }
    
    def calculate_rwa(self, exposures: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Risk-Weighted Assets (RWA) for Basel III
        
        Args:
            exposures: DataFrame with columns ['exposure_type', 'amount', 'pd', 'lgd']
        
        Returns:
            DataFrame with RWA calculations
        """
        try:
            exposures = exposures.copy()
            
            # Apply risk weights
            exposures['risk_weight'] = exposures['exposure_type'].map(
                self.basel_risk_weights
            ).fillna(1.0)
            
            # Calculate RWA
            exposures['rwa'] = exposures['amount'] * exposures['risk_weight']
            
            # For IRB approach, adjust by PD and LGD
            if 'pd' in exposures.columns and 'lgd' in exposures.columns:
                exposures['rwa_irb'] = (exposures['amount'] * 
                                       exposures['pd'] * 
                                       exposures['lgd'] * 12.5)
            
            return exposures
        
        except Exception as e:
            logger.error(f"Error calculating RWA: {e}")
            return exposures
    
    def calculate_capital_ratios(self, tier1_capital: float, tier2_capital: float,
                                 total_rwa: float) -> Dict[str, float]:
        """
        Calculate Basel III capital ratios
        
        Args:
            tier1_capital: Tier 1 capital amount
            tier2_capital: Tier 2 capital amount
            total_rwa: Total risk-weighted assets
        
        Returns:
            Dictionary with capital ratios
        """
        try:
            if total_rwa <= 0:
                return {
                    'cet1_ratio': 0.0,
                    'tier1_ratio': 0.0,
                    'total_capital_ratio': 0.0
                }
            
            total_capital = tier1_capital + tier2_capital
            
            return {
                'cet1_ratio': (tier1_capital * 0.9) / total_rwa,  # Assume 90% is CET1
                'tier1_ratio': tier1_capital / total_rwa,
                'total_capital_ratio': total_capital / total_rwa,
                'leverage_ratio': tier1_capital / (total_rwa * 0.03)  # Simplified
            }
        
        except Exception as e:
            logger.error(f"Error calculating capital ratios: {e}")
            return {}


def run_stress_test(portfolio: pd.DataFrame, scenario: Dict) -> pd.DataFrame:
    """
    Run stress testing scenario on portfolio
    
    Args:
        portfolio: DataFrame with portfolio positions
        scenario: Dictionary with stress parameters
    
    Returns:
        DataFrame with stressed values
    """
    try:
        stressed_portfolio = portfolio.copy()
        
        # Apply stress factors
        if 'equity_shock' in scenario:
            mask = stressed_portfolio['asset_class'] == 'equity'
            stressed_portfolio.loc[mask, 'value'] *= (1 + scenario['equity_shock'])
        
        if 'interest_rate_shock' in scenario:
            mask = stressed_portfolio['asset_class'] == 'fixed_income'
            duration = stressed_portfolio.loc[mask, 'duration'].fillna(5)
            rate_change = scenario['interest_rate_shock']
            stressed_portfolio.loc[mask, 'value'] *= (1 - duration * rate_change)
        
        if 'credit_spread_shock' in scenario:
            mask = stressed_portfolio['asset_class'] == 'corporate_bond'
            stressed_portfolio.loc[mask, 'value'] *= (1 + scenario['credit_spread_shock'])
        
        # Calculate losses
        stressed_portfolio['loss'] = portfolio['value'] - stressed_portfolio['value']
        stressed_portfolio['loss_pct'] = (stressed_portfolio['loss'] / 
                                          portfolio['value'] * 100)
        
        return stressed_portfolio
    
    except Exception as e:
        logger.error(f"Error running stress test: {e}")
        return portfolio


if __name__ == "__main__":
    # Example usage
    print("Banking Risk Analytics - Risk Calculator")
    print("=" * 50)
    
    # Credit Risk Example
    credit_calc = CreditRiskCalculator()
    pd = credit_calc.calculate_pd(credit_score=650, debt_ratio=0.4, delinquency_count=1)
    lgd = credit_calc.calculate_lgd(collateral_value=200000, exposure=250000)
    ead = credit_calc.calculate_ead(current_balance=50000, credit_limit=100000)
    el = credit_calc.calculate_expected_loss(pd, lgd, ead)
    
    print(f"\nCredit Risk Metrics:")
    print(f"  PD: {pd:.2%}")
    print(f"  LGD: {lgd:.2%}")
    print(f"  EAD: ${ead:,.2f}")
    print(f"  Expected Loss: ${el:,.2f}")
    
    # Market Risk Example
    returns = np.random.normal(-0.001, 0.02, 1000)  # Simulated returns
    market_calc = MarketRiskCalculator(confidence_level=0.95)
    var = market_calc.calculate_var(returns, method='historical')
    cvar = market_calc.calculate_cvar(returns)
    
    print(f"\nMarket Risk Metrics (95% confidence):")
    print(f"  VaR: {var:.2%}")
    print(f"  CVaR: {cvar:.2%}")
    
    # Regulatory Reporting
    reg_report = RegulatoryReporting()
    ratios = reg_report.calculate_capital_ratios(
        tier1_capital=1000000,
        tier2_capital=500000,
        total_rwa=10000000
    )
    
    print(f"\nCapital Ratios:")
    print(f"  CET1 Ratio: {ratios['cet1_ratio']:.2%}")
    print(f"  Tier 1 Ratio: {ratios['tier1_ratio']:.2%}")
    print(f"  Total Capital Ratio: {ratios['total_capital_ratio']:.2%}")
