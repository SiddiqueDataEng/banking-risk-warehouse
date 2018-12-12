-- Banking Risk Analytics Warehouse - Database Schema
-- Azure Synapse Analytics / SQL Server 2019+

-- Create database
CREATE DATABASE BankingRiskWarehouse;
GO

USE BankingRiskWarehouse;
GO

-- =====================================================
-- STAGING TABLES
-- =====================================================

CREATE SCHEMA staging;
GO

-- Staging: Customer data
CREATE TABLE staging.customers (
    customer_id VARCHAR(50),
    credit_score INT,
    debt_ratio DECIMAL(10,4),
    annual_income DECIMAL(18,2),
    employment_status VARCHAR(50),
    delinquency_count INT,
    load_date DATETIME2 DEFAULT GETDATE()
);

-- Staging: Loan exposures
CREATE TABLE staging.loan_exposures (
    loan_id VARCHAR(50),
    customer_id VARCHAR(50),
    loan_type VARCHAR(50),
    current_balance DECIMAL(18,2),
    credit_limit DECIMAL(18,2),
    collateral_value DECIMAL(18,2),
    origination_date DATE,
    maturity_date DATE,
    load_date DATETIME2 DEFAULT GETDATE()
);

-- Staging: Market positions
CREATE TABLE staging.market_positions (
    position_id VARCHAR(50),
    asset_class VARCHAR(50),
    instrument_type VARCHAR(50),
    market_value DECIMAL(18,2),
    notional_value DECIMAL(18,2),
    duration DECIMAL(10,4),
    position_date DATE,
    load_date DATETIME2 DEFAULT GETDATE()
);

-- Staging: Operational loss events
CREATE TABLE staging.operational_losses (
    event_id VARCHAR(50),
    event_date DATE,
    loss_amount DECIMAL(18,2),
    event_type VARCHAR(100),
    business_line VARCHAR(100),
    description VARCHAR(500),
    load_date DATETIME2 DEFAULT GETDATE()
);

-- =====================================================
-- DIMENSION TABLES
-- =====================================================

CREATE SCHEMA dim;
GO

-- Dimension: Customer
CREATE TABLE dim.customer (
    customer_key INT IDENTITY(1,1) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    credit_score INT,
    debt_ratio DECIMAL(10,4),
    annual_income DECIMAL(18,2),
    employment_status VARCHAR(50),
    delinquency_count INT,
    risk_rating VARCHAR(20),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_current BIT DEFAULT 1,
    created_date DATETIME2 DEFAULT GETDATE(),
    updated_date DATETIME2 DEFAULT GETDATE()
);

CREATE INDEX idx_customer_id ON dim.customer(customer_id);
CREATE INDEX idx_customer_current ON dim.customer(is_current);

-- Dimension: Loan Product
CREATE TABLE dim.loan_product (
    loan_product_key INT IDENTITY(1,1) PRIMARY KEY,
    loan_type VARCHAR(50) NOT NULL,
    product_name VARCHAR(100),
    basel_exposure_type VARCHAR(50),
    risk_weight DECIMAL(10,4),
    created_date DATETIME2 DEFAULT GETDATE()
);

-- Dimension: Asset Class
CREATE TABLE dim.asset_class (
    asset_class_key INT IDENTITY(1,1) PRIMARY KEY,
    asset_class VARCHAR(50) NOT NULL,
    asset_category VARCHAR(50),
    risk_category VARCHAR(50),
    created_date DATETIME2 DEFAULT GETDATE()
);

-- Dimension: Date
CREATE TABLE dim.date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    day INT,
    day_of_week INT,
    day_name VARCHAR(20),
    is_weekend BIT,
    is_holiday BIT,
    fiscal_year INT,
    fiscal_quarter INT
);

-- Dimension: Risk Scenario
CREATE TABLE dim.risk_scenario (
    scenario_key INT IDENTITY(1,1) PRIMARY KEY,
    scenario_name VARCHAR(100) NOT NULL,
    scenario_type VARCHAR(50),
    description VARCHAR(500),
    equity_shock DECIMAL(10,4),
    interest_rate_shock DECIMAL(10,4),
    credit_spread_shock DECIMAL(10,4),
    fx_shock DECIMAL(10,4),
    created_date DATETIME2 DEFAULT GETDATE()
);

-- =====================================================
-- FACT TABLES
-- =====================================================

CREATE SCHEMA fact;
GO

-- Fact: Credit Risk
CREATE TABLE fact.credit_risk (
    credit_risk_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    date_key INT NOT NULL,
    customer_key INT NOT NULL,
    loan_product_key INT NOT NULL,
    loan_id VARCHAR(50) NOT NULL,
    current_balance DECIMAL(18,2),
    credit_limit DECIMAL(18,2),
    collateral_value DECIMAL(18,2),
    exposure_at_default DECIMAL(18,2),
    probability_of_default DECIMAL(10,6),
    loss_given_default DECIMAL(10,6),
    expected_loss DECIMAL(18,2),
    risk_weighted_assets DECIMAL(18,2),
    days_past_due INT,
    created_date DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (date_key) REFERENCES dim.date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim.customer(customer_key),
    FOREIGN KEY (loan_product_key) REFERENCES dim.loan_product(loan_product_key)
);

CREATE INDEX idx_credit_risk_date ON fact.credit_risk(date_key);
CREATE INDEX idx_credit_risk_customer ON fact.credit_risk(customer_key);

-- Fact: Market Risk
CREATE TABLE fact.market_risk (
    market_risk_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    date_key INT NOT NULL,
    asset_class_key INT NOT NULL,
    position_id VARCHAR(50) NOT NULL,
    market_value DECIMAL(18,2),
    notional_value DECIMAL(18,2),
    var_95 DECIMAL(18,2),
    var_99 DECIMAL(18,2),
    cvar_95 DECIMAL(18,2),
    stressed_var DECIMAL(18,2),
    duration DECIMAL(10,4),
    delta DECIMAL(18,6),
    gamma DECIMAL(18,6),
    vega DECIMAL(18,6),
    created_date DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (date_key) REFERENCES dim.date(date_key),
    FOREIGN KEY (asset_class_key) REFERENCES dim.asset_class(asset_class_key)
);

CREATE INDEX idx_market_risk_date ON fact.market_risk(date_key);
CREATE INDEX idx_market_risk_asset ON fact.market_risk(asset_class_key);

-- Fact: Operational Risk
CREATE TABLE fact.operational_risk (
    operational_risk_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    date_key INT NOT NULL,
    event_id VARCHAR(50) NOT NULL,
    event_date DATE NOT NULL,
    loss_amount DECIMAL(18,2),
    event_type VARCHAR(100),
    business_line VARCHAR(100),
    basel_event_type VARCHAR(50),
    recovery_amount DECIMAL(18,2),
    net_loss DECIMAL(18,2),
    created_date DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (date_key) REFERENCES dim.date(date_key)
);

CREATE INDEX idx_operational_risk_date ON fact.operational_risk(date_key);
CREATE INDEX idx_operational_risk_event ON fact.operational_risk(event_type);

-- Fact: Capital Adequacy
CREATE TABLE fact.capital_adequacy (
    capital_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    date_key INT NOT NULL,
    cet1_capital DECIMAL(18,2),
    tier1_capital DECIMAL(18,2),
    tier2_capital DECIMAL(18,2),
    total_capital DECIMAL(18,2),
    total_rwa DECIMAL(18,2),
    credit_rwa DECIMAL(18,2),
    market_rwa DECIMAL(18,2),
    operational_rwa DECIMAL(18,2),
    cet1_ratio DECIMAL(10,6),
    tier1_ratio DECIMAL(10,6),
    total_capital_ratio DECIMAL(10,6),
    leverage_ratio DECIMAL(10,6),
    created_date DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (date_key) REFERENCES dim.date(date_key)
);

CREATE INDEX idx_capital_date ON fact.capital_adequacy(date_key);

-- Fact: Stress Test Results
CREATE TABLE fact.stress_test_results (
    stress_test_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    date_key INT NOT NULL,
    scenario_key INT NOT NULL,
    portfolio_value DECIMAL(18,2),
    stressed_value DECIMAL(18,2),
    loss_amount DECIMAL(18,2),
    loss_percentage DECIMAL(10,4),
    post_stress_cet1_ratio DECIMAL(10,6),
    post_stress_tier1_ratio DECIMAL(10,6),
    created_date DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (date_key) REFERENCES dim.date(date_key),
    FOREIGN KEY (scenario_key) REFERENCES dim.risk_scenario(scenario_key)
);

CREATE INDEX idx_stress_test_date ON fact.stress_test_results(date_key);
CREATE INDEX idx_stress_test_scenario ON fact.stress_test_results(scenario_key);

-- =====================================================
-- AGGREGATE TABLES
-- =====================================================

CREATE SCHEMA agg;
GO

-- Aggregate: Daily Risk Summary
CREATE TABLE agg.daily_risk_summary (
    summary_date DATE PRIMARY KEY,
    total_credit_exposure DECIMAL(18,2),
    total_expected_loss DECIMAL(18,2),
    total_rwa DECIMAL(18,2),
    market_var_95 DECIMAL(18,2),
    operational_capital_req DECIMAL(18,2),
    cet1_ratio DECIMAL(10,6),
    total_capital_ratio DECIMAL(10,6),
    high_risk_accounts INT,
    created_date DATETIME2 DEFAULT GETDATE()
);

-- Aggregate: Monthly Regulatory Report
CREATE TABLE agg.monthly_regulatory_report (
    report_month DATE PRIMARY KEY,
    total_assets DECIMAL(18,2),
    total_rwa DECIMAL(18,2),
    tier1_capital DECIMAL(18,2),
    total_capital DECIMAL(18,2),
    cet1_ratio DECIMAL(10,6),
    tier1_ratio DECIMAL(10,6),
    total_capital_ratio DECIMAL(10,6),
    leverage_ratio DECIMAL(10,6),
    liquidity_coverage_ratio DECIMAL(10,6),
    net_stable_funding_ratio DECIMAL(10,6),
    created_date DATETIME2 DEFAULT GETDATE()
);

-- =====================================================
-- AUDIT AND METADATA
-- =====================================================

CREATE SCHEMA meta;
GO

-- ETL Audit Log
CREATE TABLE meta.etl_audit_log (
    audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    pipeline_name VARCHAR(100),
    start_time DATETIME2,
    end_time DATETIME2,
    status VARCHAR(20),
    rows_processed INT,
    error_message VARCHAR(MAX),
    created_date DATETIME2 DEFAULT GETDATE()
);

-- Data Quality Checks
CREATE TABLE meta.data_quality_checks (
    check_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    check_date DATE,
    table_name VARCHAR(100),
    check_type VARCHAR(50),
    check_result VARCHAR(20),
    records_checked INT,
    records_failed INT,
    details VARCHAR(MAX),
    created_date DATETIME2 DEFAULT GETDATE()
);

GO

-- =====================================================
-- SAMPLE DATA POPULATION
-- =====================================================

-- Populate date dimension (2020-2030)
DECLARE @StartDate DATE = '2020-01-01';
DECLARE @EndDate DATE = '2030-12-31';

WHILE @StartDate <= @EndDate
BEGIN
    INSERT INTO dim.date (
        date_key, full_date, year, quarter, month, month_name,
        day, day_of_week, day_name, is_weekend, fiscal_year, fiscal_quarter
    )
    VALUES (
        CAST(FORMAT(@StartDate, 'yyyyMMdd') AS INT),
        @StartDate,
        YEAR(@StartDate),
        DATEPART(QUARTER, @StartDate),
        MONTH(@StartDate),
        DATENAME(MONTH, @StartDate),
        DAY(@StartDate),
        DATEPART(WEEKDAY, @StartDate),
        DATENAME(WEEKDAY, @StartDate),
        CASE WHEN DATEPART(WEEKDAY, @StartDate) IN (1, 7) THEN 1 ELSE 0 END,
        YEAR(@StartDate),
        DATEPART(QUARTER, @StartDate)
    );
    
    SET @StartDate = DATEADD(DAY, 1, @StartDate);
END;

-- Populate loan products
INSERT INTO dim.loan_product (loan_type, product_name, basel_exposure_type, risk_weight)
VALUES
    ('MORTGAGE', 'Residential Mortgage', 'residential_mortgage', 0.35),
    ('AUTO', 'Auto Loan', 'retail', 0.75),
    ('PERSONAL', 'Personal Loan', 'retail', 0.75),
    ('CREDIT_CARD', 'Credit Card', 'retail', 0.75),
    ('COMMERCIAL', 'Commercial Loan', 'corporate', 1.00),
    ('SME', 'Small Business Loan', 'corporate', 1.00);

-- Populate asset classes
INSERT INTO dim.asset_class (asset_class, asset_category, risk_category)
VALUES
    ('EQUITY', 'Equity', 'High'),
    ('FIXED_INCOME', 'Fixed Income', 'Medium'),
    ('CORPORATE_BOND', 'Fixed Income', 'Medium'),
    ('GOVERNMENT_BOND', 'Fixed Income', 'Low'),
    ('DERIVATIVES', 'Derivatives', 'High'),
    ('FX', 'Foreign Exchange', 'Medium'),
    ('COMMODITY', 'Commodity', 'High');

-- Populate stress scenarios
INSERT INTO dim.risk_scenario (scenario_name, scenario_type, description, equity_shock, interest_rate_shock, credit_spread_shock)
VALUES
    ('Baseline', 'BASELINE', 'Normal market conditions', 0.00, 0.00, 0.00),
    ('Adverse', 'ADVERSE', 'Moderate economic downturn', -0.15, 0.01, 0.005),
    ('Severely Adverse', 'SEVERE', 'Severe recession scenario', -0.30, 0.02, 0.01),
    ('Market Crash', 'SEVERE', 'Extreme market stress', -0.40, 0.03, 0.015),
    ('Interest Rate Spike', 'ADVERSE', 'Rapid rate increase', 0.00, 0.05, 0.002);

GO

PRINT 'Banking Risk Analytics Warehouse schema created successfully';
