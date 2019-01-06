"""
Banking Risk Analytics - REST API
Provides endpoints for risk calculations and reporting
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.risk_calculator import (
    CreditRiskCalculator, MarketRiskCalculator, 
    OperationalRiskCalculator, RegulatoryReporting, run_stress_test
)

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize calculators
credit_calc = CreditRiskCalculator()
market_calc = MarketRiskCalculator()
op_risk_calc = OperationalRiskCalculator()
reg_report = RegulatoryReporting()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Banking Risk Analytics API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/credit-risk/calculate', methods=['POST'])
def calculate_credit_risk():
    """
    Calculate credit risk metrics (PD, LGD, EAD, EL)
    
    Request body:
    {
        "credit_score": 650,
        "debt_ratio": 0.4,
        "delinquency_count": 1,
        "collateral_value": 200000,
        "exposure": 250000,
        "current_balance": 50000,
        "credit_limit": 100000
    }
    """
    try:
        data = request.get_json()
        
        # Calculate PD
        pd = credit_calc.calculate_pd(
            credit_score=data.get('credit_score', 700),
            debt_ratio=data.get('debt_ratio', 0.3),
            delinquency_count=data.get('delinquency_count', 0)
        )
        
        # Calculate LGD
        lgd = credit_calc.calculate_lgd(
            collateral_value=data.get('collateral_value', 0),
            exposure=data.get('exposure', 100000)
        )
        
        # Calculate EAD
        ead = credit_calc.calculate_ead(
            current_balance=data.get('current_balance', 50000),
            credit_limit=data.get('credit_limit', 100000)
        )
        
        # Calculate Expected Loss
        el = credit_calc.calculate_expected_loss(pd, lgd, ead)
        
        return jsonify({
            'success': True,
            'metrics': {
                'probability_of_default': round(pd, 4),
                'loss_given_default': round(lgd, 4),
                'exposure_at_default': round(ead, 2),
                'expected_loss': round(el, 2)
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error calculating credit risk: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/market-risk/var', methods=['POST'])
def calculate_var():
    """
    Calculate Value at Risk (VaR)
    
    Request body:
    {
        "returns": [-0.02, 0.01, -0.015, ...],
        "confidence_level": 0.95,
        "method": "historical"
    }
    """
    try:
        data = request.get_json()
        returns = np.array(data.get('returns', []))
        
        if len(returns) == 0:
            return jsonify({
                'success': False,
                'error': 'No returns data provided'
            }), 400
        
        confidence_level = data.get('confidence_level', 0.95)
        method = data.get('method', 'historical')
        
        market_calc_custom = MarketRiskCalculator(confidence_level=confidence_level)
        var = market_calc_custom.calculate_var(returns, method=method)
        cvar = market_calc_custom.calculate_cvar(returns)
        
        return jsonify({
            'success': True,
            'metrics': {
                'var': round(float(var), 6),
                'cvar': round(float(cvar), 6),
                'confidence_level': confidence_level,
                'method': method,
                'sample_size': len(returns)
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error calculating VaR: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/operational-risk/calculate', methods=['POST'])
def calculate_operational_risk():
    """
    Calculate operational risk capital
    
    Request body:
    {
        "loss_events": [
            {"amount": 50000, "date": "2024-01-15"},
            {"amount": 75000, "date": "2024-02-20"}
        ]
    }
    """
    try:
        data = request.get_json()
        loss_events = data.get('loss_events', [])
        
        if not loss_events:
            return jsonify({
                'success': False,
                'error': 'No loss events provided'
            }), 400
        
        metrics = op_risk_calc.calculate_operational_risk_capital(loss_events)
        
        return jsonify({
            'success': True,
            'metrics': {
                'expected_loss': round(metrics.get('expected_loss', 0), 2),
                'std_dev': round(metrics.get('std_dev', 0), 2),
                'max_loss': round(metrics.get('max_loss', 0), 2),
                'capital_requirement': round(metrics.get('capital_requirement', 0), 2),
                'loss_count': metrics.get('loss_count', 0)
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error calculating operational risk: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/regulatory/rwa', methods=['POST'])
def calculate_rwa():
    """
    Calculate Risk-Weighted Assets (RWA)
    
    Request body:
    {
        "exposures": [
            {"exposure_type": "corporate", "amount": 1000000, "pd": 0.02, "lgd": 0.45},
            {"exposure_type": "retail", "amount": 500000, "pd": 0.03, "lgd": 0.50}
        ]
    }
    """
    try:
        data = request.get_json()
        exposures_data = data.get('exposures', [])
        
        if not exposures_data:
            return jsonify({
                'success': False,
                'error': 'No exposures provided'
            }), 400
        
        exposures_df = pd.DataFrame(exposures_data)
        rwa_df = reg_report.calculate_rwa(exposures_df)
        
        total_rwa = rwa_df['rwa'].sum()
        total_exposure = rwa_df['amount'].sum()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_exposure': round(total_exposure, 2),
                'total_rwa': round(total_rwa, 2),
                'average_risk_weight': round(total_rwa / total_exposure if total_exposure > 0 else 0, 4)
            },
            'details': rwa_df.to_dict(orient='records'),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error calculating RWA: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/regulatory/capital-ratios', methods=['POST'])
def calculate_capital_ratios():
    """
    Calculate Basel III capital ratios
    
    Request body:
    {
        "tier1_capital": 1000000,
        "tier2_capital": 500000,
        "total_rwa": 10000000
    }
    """
    try:
        data = request.get_json()
        
        tier1_capital = data.get('tier1_capital', 0)
        tier2_capital = data.get('tier2_capital', 0)
        total_rwa = data.get('total_rwa', 0)
        
        ratios = reg_report.calculate_capital_ratios(
            tier1_capital, tier2_capital, total_rwa
        )
        
        # Basel III minimum requirements
        requirements = {
            'cet1_minimum': 0.045,
            'tier1_minimum': 0.06,
            'total_capital_minimum': 0.08
        }
        
        # Check compliance
        compliance = {
            'cet1_compliant': ratios.get('cet1_ratio', 0) >= requirements['cet1_minimum'],
            'tier1_compliant': ratios.get('tier1_ratio', 0) >= requirements['tier1_minimum'],
            'total_capital_compliant': ratios.get('total_capital_ratio', 0) >= requirements['total_capital_minimum']
        }
        
        return jsonify({
            'success': True,
            'ratios': {
                'cet1_ratio': round(ratios.get('cet1_ratio', 0), 4),
                'tier1_ratio': round(ratios.get('tier1_ratio', 0), 4),
                'total_capital_ratio': round(ratios.get('total_capital_ratio', 0), 4),
                'leverage_ratio': round(ratios.get('leverage_ratio', 0), 4)
            },
            'requirements': requirements,
            'compliance': compliance,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error calculating capital ratios: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/stress-test/run', methods=['POST'])
def run_stress_test_api():
    """
    Run stress testing scenario
    
    Request body:
    {
        "portfolio": [
            {"asset_class": "equity", "value": 1000000, "duration": 0},
            {"asset_class": "fixed_income", "value": 2000000, "duration": 5}
        ],
        "scenario": {
            "equity_shock": -0.30,
            "interest_rate_shock": 0.02,
            "credit_spread_shock": 0.01
        }
    }
    """
    try:
        data = request.get_json()
        
        portfolio_data = data.get('portfolio', [])
        scenario = data.get('scenario', {})
        
        if not portfolio_data:
            return jsonify({
                'success': False,
                'error': 'No portfolio data provided'
            }), 400
        
        portfolio_df = pd.DataFrame(portfolio_data)
        stressed_df = run_stress_test(portfolio_df, scenario)
        
        total_loss = stressed_df['loss'].sum()
        total_value = portfolio_df['value'].sum()
        loss_pct = (total_loss / total_value * 100) if total_value > 0 else 0
        
        return jsonify({
            'success': True,
            'summary': {
                'total_portfolio_value': round(total_value, 2),
                'total_loss': round(total_loss, 2),
                'loss_percentage': round(loss_pct, 2)
            },
            'scenario': scenario,
            'details': stressed_df.to_dict(orient='records'),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error running stress test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/reports/risk-summary', methods=['GET'])
def get_risk_summary():
    """Get overall risk summary dashboard"""
    try:
        # This would typically query from database
        # For demo, return sample data
        summary = {
            'credit_risk': {
                'total_exposure': 50000000,
                'expected_loss': 250000,
                'high_risk_accounts': 45
            },
            'market_risk': {
                'var_95': -1250000,
                'cvar_95': -1800000,
                'stressed_var': -2500000
            },
            'operational_risk': {
                'capital_requirement': 500000,
                'loss_events_ytd': 12,
                'total_losses_ytd': 350000
            },
            'capital_adequacy': {
                'cet1_ratio': 0.095,
                'tier1_ratio': 0.11,
                'total_capital_ratio': 0.14,
                'compliant': True
            }
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error generating risk summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
