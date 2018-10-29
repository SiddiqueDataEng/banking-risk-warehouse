# Banking Risk Analytics Warehouse

## Overview
Enterprise-grade risk and compliance reporting platform for banking operations using Azure Synapse Analytics. Implements Basel III regulatory requirements, credit risk modeling (PD, LGD, EAD), market risk analytics (VaR, CVaR), and operational risk assessment with comprehensive stress testing capabilities.

## Technologies
- **Cloud Platform**: Azure Synapse Analytics, Azure Data Factory
- **Database**: SQL Server 2019+, Azure SQL Pool
- **Programming**: Python 3.9+, SQL
- **Risk Analytics**: NumPy, SciPy, Pandas
- **API**: Flask, REST
- **Infrastructure**: Terraform, Docker
- **Monitoring**: Azure Application Insights, Log Analytics
- **Visualization**: Power BI, HTML/JavaScript

## Architecture
```
Core Banking Systems ──┐
Trading Platforms ─────┼──> Azure Data Factory ──> Synapse Analytics
Market Data Feeds ─────┘                                    │
                                                             ├──> SQL Pool (Risk DW)
                                                             ├──> Spark Pool (Calculations)
                                                             ├──> REST API
                                                             └──> Power BI / Dashboard
```

## Features

### Credit Risk Analytics
- **PD Calculation**: Probability of Default using logistic regression
- **LGD Modeling**: Loss Given Default with collateral consideration
- **EAD Estimation**: Exposure at Default with credit conversion factors
- **Expected Loss**: EL = PD × LGD × EAD
- **Risk Ratings**: AAA to CCC rating assignments
- **Portfolio Analytics**: Concentration risk, vintage analysis

### Market Risk Management
- **Value at Risk (VaR)**: Historical, Parametric, Monte Carlo methods
- **Conditional VaR (CVaR)**: Expected Shortfall calculations
- **Stress Testing**: Multiple scenario analysis
- **Greeks Calculation**: Delta, Gamma, Vega for derivatives
- **Backtesting**: VaR model validation

### Operational Risk
- **Loss Distribution Approach**: Capital calculation using historical losses
- **Basel Event Types**: 7 standardized categories
- **Business Line Allocation**: Risk capital by business unit
- **Key Risk Indicators**: Real-time monitoring

### Regulatory Compliance
- **Basel III**: CET1, Tier 1, Total Capital ratios
- **Risk-Weighted Assets**: Standardized and IRB approaches
- **CCAR Reporting**: Comprehensive Capital Analysis and Review
- **Stress Testing**: Baseline, Adverse, Severely Adverse scenarios
- **Liquidity Ratios**: LCR, NSFR calculations

### Real-Time Monitoring
- **Risk Dashboard**: Interactive HTML5 dashboard
- **Alerts**: Threshold-based notifications
- **Audit Trail**: Complete data lineage
- **Data Quality**: Automated validation checks

## Project Structure
```
banking-risk-warehouse/
├── src/
│   └── risk_calculator.py          # Core risk calculation engine
├── api/
│   └── risk_api.py                 # REST API endpoints
├── sql/
│   └── create_risk_schema.sql      # Database schema (Synapse)
├── terraform/
│   ├── main.tf                     # Azure infrastructure
│   └── variables.tf                # Configuration variables
├── ui/
│   └── risk_dashboard.html         # Risk monitoring dashboard
├── tests/
│   └── test_risk_calculator.py     # Unit tests
├── config/
│   └── config.yaml                 # Application configuration
├── Dockerfile                      # Container definition
├── requirements.txt                # Python dependencies
└── README.md
```

## Quick Start

### Prerequisites
- Azure subscription
- Terraform 1.0+
- Python 3.9+
- Docker (optional)

### 1. Deploy Infrastructure
```bash
cd terraform
terraform init
terraform plan -var="sql_admin_password=YourSecurePassword123!"
terraform apply
```

### 2. Create Database Schema
```bash
# Connect to Synapse SQL Pool
sqlcmd -S <synapse-workspace>.sql.azuresynapse.net -d RiskAnalyticsPool -U sqladmin -P <password>

# Run schema creation
:r sql/create_risk_schema.sql
GO
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Application
```bash
# Set environment variables
export SYNAPSE_SERVER="<workspace>.sql.azuresynapse.net"
export SQL_USERNAME="sqladmin"
export SQL_PASSWORD="<password>"
export APPINSIGHTS_INSTRUMENTATIONKEY="<key>"
```

### 5. Run API Server
```bash
python api/risk_api.py
```

### 6. Access Dashboard
Open `ui/risk_dashboard.html` in browser or deploy to Azure App Service.

## API Endpoints

### Credit Risk
```bash
# Calculate credit risk metrics
POST /api/v1/credit-risk/calculate
{
  "credit_score": 650,
  "debt_ratio": 0.4,
  "delinquency_count": 1,
  "collateral_value": 200000,
  "exposure": 250000,
  "current_balance": 50000,
  "credit_limit": 100000
}
```

### Market Risk
```bash
# Calculate VaR
POST /api/v1/market-risk/var
{
  "returns": [-0.02, 0.01, -0.015, ...],
  "confidence_level": 0.95,
  "method": "historical"
}
```

### Regulatory Reporting
```bash
# Calculate capital ratios
POST /api/v1/regulatory/capital-ratios
{
  "tier1_capital": 1000000,
  "tier2_capital": 500000,
  "total_rwa": 10000000
}
```

### Stress Testing
```bash
# Run stress test
POST /api/v1/stress-test/run
{
  "portfolio": [...],
  "scenario": {
    "equity_shock": -0.30,
    "interest_rate_shock": 0.02
  }
}
```

## Testing
```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Docker Deployment
```bash
# Build image
docker build -t banking-risk-api .

# Run container
docker run -p 5000:5000 \
  -e SYNAPSE_SERVER="<server>" \
  -e SQL_USERNAME="sqladmin" \
  -e SQL_PASSWORD="<password>" \
  banking-risk-api
```

## Regulatory Compliance

### Basel III Requirements
- **CET1 Minimum**: 4.5%
- **Tier 1 Minimum**: 6.0%
- **Total Capital Minimum**: 8.0%
- **Capital Conservation Buffer**: 2.5%
- **Countercyclical Buffer**: 0-2.5%

### Risk-Weighted Assets
- Sovereign: 0%
- Bank: 20%
- Corporate: 100%
- Retail: 75%
- Residential Mortgage: 35%

## Performance Optimization
- Columnstore indexes on fact tables
- Partitioning by date_key
- Materialized views for aggregations
- Caching for frequently accessed data
- Parallel query execution

## Security
- Azure Key Vault for secrets
- Managed identities for authentication
- Data encryption at rest and in transit
- Row-level security for sensitive data
- Audit logging enabled

## Monitoring
- Application Insights for API metrics
- Log Analytics for query performance
- Custom alerts for risk thresholds
- Data quality dashboards

## License
MIT License

## Support
For issues and questions, please open a GitHub issue.
