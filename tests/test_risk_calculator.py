"""
Unit tests for Banking Risk Calculator
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.risk_calculator import (
    CreditRiskCalculator, MarketRiskCalculator,
    OperationalRiskCalculator, RegulatoryReporting, run_stress_test
)


class TestCreditRiskCalculator(unittest.TestCase):
    """Test credit risk calculations"""
    
    def setUp(self):
        self.calc = CreditRiskCalculator()
    
    def test_calculate_pd_basic(self):
        """Test basic PD calculation"""
        pd = self.calc.calculate_pd(
            credit_score=700,
            debt_ratio=0.3,
            delinquency_count=0
        )
        
        self.assertGreater(pd, 0.0)
        self.assertLess(pd, 1.0)
        self.assertIsInstance(pd, float)
    
    def test_calculate_pd_high_risk(self):
        """Test PD for high-risk customer"""
        pd_high = self.calc.calculate_pd(
            credit_score=550,
            debt_ratio=0.8,
            delinquency_count=3
        )
        
        pd_low = self.calc.calculate_pd(
            credit_score=800,
            debt_ratio=0.2,
            delinquency_count=0
        )
        
        self.assertGreater(pd_high, pd_low)
    
    def test_calculate_lgd_fully_secured(self):
        """Test LGD with full collateral"""
        lgd = self.calc.calculate_lgd(
            collateral_value=300000,
            exposure=250000
        )
        
        self.assertGreaterEqual(lgd, 0.0)
        self.assertLessEqual(lgd, 1.0)
        self.assertLess(lgd, 0.5)  # Should be low with full collateral
    
    def test_calculate_lgd_unsecured(self):
        """Test LGD with no collateral"""
        lgd = self.calc.calculate_lgd(
            collateral_value=0,
            exposure=100000
        )
        
        self.assertGreater(lgd, 0.5)  # Should be high without collateral
    
    def test_calculate_ead(self):
        """Test EAD calculation"""
        ead = self.calc.calculate_ead(
            current_balance=50000,
            credit_limit=100000
        )
        
        self.assertGreater(ead, 50000)  # Should include expected drawdown
        self.assertLessEqual(ead, 100000)
    
    def test_calculate_expected_loss(self):
        """Test expected loss calculation"""
        pd = 0.05
        lgd = 0.45
        ead = 100000
        
        el = self.calc.calculate_expected_loss(pd, lgd, ead)
        
        expected_el = pd * lgd * ead
        self.assertAlmostEqual(el, expected_el, places=2)


class TestMarketRiskCalculator(unittest.TestCase):
    """Test market risk calculations"""
    
    def setUp(self):
        self.calc = MarketRiskCalculator(confidence_level=0.95)
        # Generate sample returns
        np.random.seed(42)
        self.returns = np.random.normal(-0.001, 0.02, 1000)
    
    def test_calculate_var_historical(self):
        """Test historical VaR calculation"""
        var = self.calc.calculate_var(self.returns, method='historical')
        
        self.assertLess(var, 0)  # VaR should be negative (loss)
        self.assertIsInstance(var, (float, np.floating))
    
    def test_calculate_var_parametric(self):
        """Test parametric VaR calculation"""
        var = self.calc.calculate_var(self.returns, method='parametric')
        
        self.assertLess(var, 0)
        self.assertIsInstance(var, (float, np.floating))
    
    def test_calculate_var_monte_carlo(self):
        """Test Monte Carlo VaR calculation"""
        var = self.calc.calculate_var(self.returns, method='monte_carlo')
        
        self.assertLess(var, 0)
        self.assertIsInstance(var, (float, np.floating))
    
    def test_calculate_cvar(self):
        """Test CVaR calculation"""
        cvar = self.calc.calculate_cvar(self.returns)
        var = self.calc.calculate_var(self.returns, method='historical')
        
        # CVaR should be more negative (worse) than VaR
        self.assertLess(cvar, var)
    
    def test_var_confidence_levels(self):
        """Test VaR at different confidence levels"""
        calc_95 = MarketRiskCalculator(confidence_level=0.95)
        calc_99 = MarketRiskCalculator(confidence_level=0.99)
        
        var_95 = calc_95.calculate_var(self.returns, method='historical')
        var_99 = calc_99.calculate_var(self.returns, method='historical')
        
        # 99% VaR should be more negative than 95% VaR
        self.assertLess(var_99, var_95)


class TestOperationalRiskCalculator(unittest.TestCase):
    """Test operational risk calculations"""
    
    def setUp(self):
        self.calc = OperationalRiskCalculator()
        self.loss_events = [
            {'amount': 50000, 'date': '2024-01-15'},
            {'amount': 75000, 'date': '2024-02-20'},
            {'amount': 30000, 'date': '2024-03-10'},
            {'amount': 100000, 'date': '2024-04-05'}
        ]
    
    def test_calculate_operational_risk_capital(self):
        """Test operational risk capital calculation"""
        result = self.calc.calculate_operational_risk_capital(self.loss_events)
        
        self.assertIn('expected_loss', result)
        self.assertIn('capital_requirement', result)
        self.assertIn('max_loss', result)
        
        self.assertGreater(result['capital_requirement'], result['expected_loss'])
        self.assertEqual(result['loss_count'], len(self.loss_events))
    
    def test_empty_loss_events(self):
        """Test with no loss events"""
        result = self.calc.calculate_operational_risk_capital([])
        
        self.assertEqual(result['capital_requirement'], 0.0)
        self.assertEqual(result['expected_loss'], 0.0)


class TestRegulatoryReporting(unittest.TestCase):
    """Test regulatory reporting calculations"""
    
    def setUp(self):
        self.reporter = RegulatoryReporting()
    
    def test_calculate_rwa(self):
        """Test RWA calculation"""
        exposures = pd.DataFrame({
            'exposure_type': ['corporate', 'retail', 'residential_mortgage'],
            'amount': [1000000, 500000, 300000],
            'pd': [0.02, 0.03, 0.01],
            'lgd': [0.45, 0.50, 0.35]
        })
        
        result = self.reporter.calculate_rwa(exposures)
        
        self.assertIn('rwa', result.columns)
        self.assertIn('risk_weight', result.columns)
        self.assertEqual(len(result), 3)
        
        # Check that RWA is calculated
        self.assertTrue((result['rwa'] > 0).all())
    
    def test_calculate_capital_ratios(self):
        """Test capital ratios calculation"""
        ratios = self.reporter.calculate_capital_ratios(
            tier1_capital=1000000,
            tier2_capital=500000,
            total_rwa=10000000
        )
        
        self.assertIn('cet1_ratio', ratios)
        self.assertIn('tier1_ratio', ratios)
        self.assertIn('total_capital_ratio', ratios)
        
        # Check ratio values are reasonable
        self.assertGreater(ratios['tier1_ratio'], 0)
        self.assertLess(ratios['tier1_ratio'], 1)
        
        # Total capital ratio should be highest
        self.assertGreater(ratios['total_capital_ratio'], ratios['tier1_ratio'])
    
    def test_capital_ratios_zero_rwa(self):
        """Test capital ratios with zero RWA"""
        ratios = self.reporter.calculate_capital_ratios(
            tier1_capital=1000000,
            tier2_capital=500000,
            total_rwa=0
        )
        
        self.assertEqual(ratios['cet1_ratio'], 0.0)
        self.assertEqual(ratios['tier1_ratio'], 0.0)


class TestStressTest(unittest.TestCase):
    """Test stress testing functionality"""
    
    def setUp(self):
        self.portfolio = pd.DataFrame({
            'asset_class': ['equity', 'fixed_income', 'corporate_bond'],
            'value': [1000000, 2000000, 1500000],
            'duration': [0, 5, 3]
        })
    
    def test_stress_test_equity_shock(self):
        """Test stress test with equity shock"""
        scenario = {'equity_shock': -0.30}
        
        result = run_stress_test(self.portfolio, scenario)
        
        self.assertIn('loss', result.columns)
        self.assertIn('loss_pct', result.columns)
        
        # Equity position should have loss
        equity_loss = result[result['asset_class'] == 'equity']['loss'].iloc[0]
        self.assertGreater(equity_loss, 0)
    
    def test_stress_test_interest_rate_shock(self):
        """Test stress test with interest rate shock"""
        scenario = {'interest_rate_shock': 0.02}
        
        result = run_stress_test(self.portfolio, scenario)
        
        # Fixed income should have loss due to duration
        fi_loss = result[result['asset_class'] == 'fixed_income']['loss'].iloc[0]
        self.assertGreater(fi_loss, 0)
    
    def test_stress_test_combined_shocks(self):
        """Test stress test with multiple shocks"""
        scenario = {
            'equity_shock': -0.30,
            'interest_rate_shock': 0.02,
            'credit_spread_shock': 0.01
        }
        
        result = run_stress_test(self.portfolio, scenario)
        
        total_loss = result['loss'].sum()
        self.assertGreater(total_loss, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_end_to_end_credit_risk(self):
        """Test complete credit risk workflow"""
        calc = CreditRiskCalculator()
        
        # Calculate all metrics
        pd = calc.calculate_pd(650, 0.4, 1)
        lgd = calc.calculate_lgd(200000, 250000)
        ead = calc.calculate_ead(50000, 100000)
        el = calc.calculate_expected_loss(pd, lgd, ead)
        
        # Verify all calculations completed
        self.assertIsNotNone(pd)
        self.assertIsNotNone(lgd)
        self.assertIsNotNone(ead)
        self.assertIsNotNone(el)
        
        # Verify expected loss is reasonable
        self.assertGreater(el, 0)
        self.assertLess(el, ead)
    
    def test_end_to_end_regulatory_reporting(self):
        """Test complete regulatory reporting workflow"""
        reporter = RegulatoryReporting()
        
        # Create sample exposures
        exposures = pd.DataFrame({
            'exposure_type': ['corporate', 'retail'],
            'amount': [1000000, 500000],
            'pd': [0.02, 0.03],
            'lgd': [0.45, 0.50]
        })
        
        # Calculate RWA
        rwa_df = reporter.calculate_rwa(exposures)
        total_rwa = rwa_df['rwa'].sum()
        
        # Calculate capital ratios
        ratios = reporter.calculate_capital_ratios(
            tier1_capital=150000,
            tier2_capital=75000,
            total_rwa=total_rwa
        )
        
        # Verify complete workflow
        self.assertGreater(total_rwa, 0)
        self.assertIn('cet1_ratio', ratios)
        self.assertGreater(ratios['total_capital_ratio'], 0)


if __name__ == '__main__':
    unittest.main()
