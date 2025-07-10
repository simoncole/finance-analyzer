# Personal Finance Analyzer - Web App

A modern web application for analyzing personal financial data from Discover credit cards and Venmo transactions.

## Features

- **Multi-Source Data Integration**: Supports both Discover credit card and Venmo transaction data
- **Interactive Dashboard**: Beautiful, responsive interface with real-time data visualization
- **Advanced Analytics**: Spending insights, category breakdowns, and trend analysis
- **Internship Budget Tracking**: Specialized tools for tracking income vs expenses during internships
- **Export Capabilities**: Generate and download detailed financial reports

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Navigate to the web app directory:**
   ```bash
   cd web_app
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** and navigate to the URL shown in the terminal (typically `http://localhost:8501`)

## Usage

### 1. Data Upload

- **Discover Data**: Upload your Discover credit card CSV file downloaded from the Discover website
  - Required columns: `Trans. Date`, `Description`, `Amount`, `Category`
  
- **Venmo Data**: Upload your categorized Venmo transactions CSV file
  - Use the `venmo_categorizer.py` script first to categorize your Venmo transactions
  - Required columns: `Date`, `Description`, `Amount`, `Category`

### 2. Data Processing

- Set optional date ranges for analysis
- The app will automatically:
  - Clean and normalize transaction data
  - Apply enhanced categorization
  - Filter out credit card payments
  - Combine multiple data sources

### 3. Analysis

- **Financial Analysis**: View spending patterns, category breakdowns, and trends
- **Internship Analysis**: Track budget progress with burndown charts
- **Reports**: Generate and export detailed financial reports

## Data Format Requirements

### Discover CSV Format
```csv
Trans. Date,Post Date,Description,Amount,Category
2025-06-01,2025-06-01,"GROCERY STORE",-45.67,"Groceries"
```

### Venmo Categorized CSV Format
```csv
Date,Description,Amount,Category,Transaction_Type
2025-06-01,"Coffee shop",4.50,"Dining","Charge"
```

## App Structure

- **Home**: Dashboard with overview and quick stats
- **Data Upload**: File upload and data processing interface
- **Financial Analysis**: Interactive charts and spending insights
- **Internship Analysis**: Budget tracking and projections
- **Reports**: Export and reporting tools

## Phase 1 Features (Current)

✅ **Core Infrastructure**
- Multi-page Streamlit app with navigation
- File upload functionality for CSV files
- Data validation and error handling
- Basic data processing and combination
- Session state management
- Responsive UI with custom styling

🚧 **Coming in Phase 2**
- Interactive charts and visualizations
- Category management and editing
- Advanced filtering and date ranges

🚧 **Coming in Phase 3**
- Internship budget analysis
- Report generation and export
- Data persistence and user settings

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running the app from the correct directory and that the parent `finance_analyzer.py` file is accessible

2. **File upload errors**: Ensure your CSV files have the correct column names and format

3. **Data processing errors**: Check that your data doesn't have any corrupted rows or unusual characters

### Getting Help

If you encounter issues:
1. Check that all required columns are present in your CSV files
2. Verify that dates are in a recognizable format
3. Make sure all dependencies are installed correctly

## Development

### Project Structure
```
web_app/
├── app.py              # Main Streamlit application
├── data_processor.py   # Data processing utilities
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Next Steps

The app is currently in Phase 1 (Core Infrastructure). Future phases will add:
- Advanced visualization and analytics
- Internship-specific budget tracking
- Report generation and export features
- Data persistence and user settings 