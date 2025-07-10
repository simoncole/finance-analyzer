#!/usr/bin/env python3
"""
Simple test script to verify the web app structure is working
"""

import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit import successful")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        print("✅ Plotly import successful")
    except ImportError as e:
        print(f"❌ Plotly import failed: {e}")
        return False
    
    try:
        from data_processor import (
            process_discover_data,
            process_venmo_data,
            combine_datasets,
            calculate_basic_metrics
        )
        print("✅ Data processor import successful")
    except ImportError as e:
        print(f"❌ Data processor import failed: {e}")
        return False
    
    try:
        from finance_analyzer import enhanced_categorization
        print("✅ Finance analyzer import successful")
    except ImportError as e:
        print(f"❌ Finance analyzer import failed: {e}")
        return False
    
    return True

def test_data_processing():
    """Test basic data processing functionality"""
    print("\n🧪 Testing data processing...")
    
    try:
        from data_processor import process_discover_data, calculate_basic_metrics
        
        # Create sample data
        sample_discover_data = pd.DataFrame({
            'Trans. Date': ['2025-06-01', '2025-06-02', '2025-06-03'],
            'Description': ['GROCERY STORE', 'GAS STATION', 'COFFEE SHOP'],
            'Amount': [45.67, 28.50, 5.99],
            'Category': ['Groceries', 'Gas', 'Restaurants']
        })
        
        # Test processing
        processed = process_discover_data(sample_discover_data)
        
        if processed is not None and len(processed) > 0:
            print("✅ Data processing successful")
            
            # Test metrics calculation
            metrics = calculate_basic_metrics(processed)
            if metrics is not None:
                print("✅ Metrics calculation successful")
                print(f"   Total transactions: {metrics['total_transactions']}")
                print(f"   Total expenses: ${metrics['total_expenses']:.2f}")
            else:
                print("❌ Metrics calculation failed")
                return False
        else:
            print("❌ Data processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Data processing test failed: {e}")
        return False
    
    return True

def test_app_structure():
    """Test that the main app file can be imported"""
    print("\n🧪 Testing app structure...")
    
    try:
        # Try to import the main app functions
        from app import (
            init_session_state,
            show_home_page,
            show_upload_page,
            show_analysis_page
        )
        print("✅ App structure import successful")
        return True
    except ImportError as e:
        print(f"❌ App structure import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ App structure test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running Web App Tests\n")
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test data processing
    if not test_data_processing():
        all_passed = False
    
    # Test app structure
    if not test_app_structure():
        all_passed = False
    
    # Summary
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! The web app structure is ready.")
        print("\n💡 To run the app:")
        print("   streamlit run app.py")
        print("   or")
        print("   python run_app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n💡 Make sure you have installed the requirements:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main() 