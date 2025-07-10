#!/usr/bin/env python3
"""
Simple launcher script for the Personal Finance Analyzer web app
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit app"""
    
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🚀 Starting Personal Finance Analyzer Web App...")
    print("📁 Working directory:", script_dir)
    
    # Run the Streamlit app
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--theme.primaryColor", "#1f77b4",
            "--theme.backgroundColor", "#ffffff",
            "--theme.secondaryBackgroundColor", "#f0f2f6"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 App stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running app: {e}")
        print("\n💡 Make sure you have installed the requirements:")
        print("   pip install -r requirements.txt")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install requirements:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main() 