#!/usr/bin/env python3
"""
API Configuration Test Script

This script helps you test and validate your API configuration
for the AI Investment System.

Usage:
    python test_api_config.py                    # Test current .env configuration
    python test_api_config.py --provider openai  # Test specific provider
    python test_api_config.py --interactive      # Interactive setup
"""

import os
import sys
import argparse
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from src.tools.openrouter_config import (
        get_chat_completion, 
        setup_provider, 
        PROVIDER_CONFIGS,
        logger
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure you're running this from the project root directory")
    sys.exit(1)


def test_api_basic():
    """Test basic API functionality"""
    print("🧪 Testing basic API functionality...")
    
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant. Respond concisely."},
        {"role": "user", "content": "Please respond with exactly: 'API test successful'"}
    ]
    
    try:
        response = get_chat_completion(test_messages)
        
        if response:
            print(f"✅ API Response: {response}")
            
            if "API test successful" in response:
                print("✅ API configuration is working correctly!")
                return True
            else:
                print("⚠️  API responded but output format may be unexpected")
                return True
        else:
            print("❌ API returned no response")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False


def test_api_advanced():
    """Test advanced API functionality with parameters"""
    print("\n🔬 Testing advanced API functionality...")
    
    test_messages = [
        {"role": "user", "content": "Analyze the sentiment of this text: 'The stock market is performing well today with strong gains.'"}
    ]
    
    try:
        response = get_chat_completion(
            test_messages,
            temperature=0.7,
            max_tokens=100
        )
        
        if response:
            print(f"✅ Advanced API test successful")
            print(f"Response preview: {response[:100]}...")
            return True
        else:
            print("❌ Advanced API test failed")
            return False
            
    except Exception as e:
        print(f"❌ Advanced API test failed: {str(e)}")
        return False


def interactive_setup():
    """Interactive setup for API configuration"""
    print("\n🚀 Interactive API Setup")
    print("=" * 50)
    
    print("\nAvailable providers:")
    for i, (provider, config) in enumerate(PROVIDER_CONFIGS.items(), 1):
        print(f"{i}. {provider.upper()}")
        print(f"   Base URL: {config['base_url']}")
        print(f"   Models: {', '.join(config['models'][:3])}{'...' if len(config['models']) > 3 else ''}")
        print()
    
    while True:
        try:
            choice = input("Select provider (1-{}): ".format(len(PROVIDER_CONFIGS)))
            provider_idx = int(choice) - 1
            if 0 <= provider_idx < len(PROVIDER_CONFIGS):
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    provider_name = list(PROVIDER_CONFIGS.keys())[provider_idx]
    config = PROVIDER_CONFIGS[provider_name]
    
    print(f"\n📝 Setting up {provider_name.upper()}")
    print("-" * 30)
    
    # Get API key
    if provider_name == "ollama":
        api_key = "ollama"
        print("Using Ollama (no API key required)")
    else:
        api_key = input(f"Enter your {provider_name} API key: ").strip()
        if not api_key:
            print("❌ API key is required")
            return False
    
    # Select model
    print(f"\nAvailable models for {provider_name}:")
    for i, model in enumerate(config['models'], 1):
        default_marker = " (default)" if model == config['default_model'] else ""
        print(f"{i}. {model}{default_marker}")
    
    model_choice = input(f"\nSelect model (1-{len(config['models'])}) or press Enter for default: ").strip()
    
    if model_choice:
        try:
            model_idx = int(model_choice) - 1
            if 0 <= model_idx < len(config['models']):
                model = config['models'][model_idx]
            else:
                print("Invalid choice, using default model")
                model = config['default_model']
        except ValueError:
            print("Invalid input, using default model")
            model = config['default_model']
    else:
        model = config['default_model']
    
    print(f"\n🔧 Configuring {provider_name} with model {model}...")
    
    try:
        setup_provider(provider_name, api_key, model)
        print("✅ Provider setup complete!")
        
        # Test the configuration
        print("\n🧪 Testing configuration...")
        if test_api_basic():
            print("\n🎉 Setup successful! Your API is ready to use.")
            
            # Save to .env file
            save_choice = input("\nSave this configuration to .env file? (y/N): ").strip().lower()
            if save_choice in ['y', 'yes']:
                save_to_env(provider_name, api_key, model, config['base_url'])
            
            return True
        else:
            print("\n❌ Configuration test failed. Please check your API key and settings.")
            return False
            
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return False


def save_to_env(provider, api_key, model, base_url):
    """Save configuration to .env file"""
    env_content = f"""# AI Investment System API Configuration
# Generated by test_api_config.py

API_KEY={api_key}
API_BASE_URL={base_url}
MODEL_NAME={model}
API_PROVIDER={provider}

# Optional: Advanced settings
# API_TIMEOUT=30
# MAX_RETRIES=3
# DEBUG_LOGGING=false
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Configuration saved to .env file")
    except Exception as e:
        print(f"❌ Failed to save .env file: {str(e)}")


def check_env_file():
    """Check if .env file exists and has required variables"""
    print("📁 Checking .env file configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    # Check for required variables
    required_vars = ['API_KEY']
    missing_vars = []
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=your-" in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or invalid variables in .env: {', '.join(missing_vars)}")
        return False
    
    print("✅ .env file found and appears valid")
    return True


def show_current_config():
    """Show current API configuration"""
    print("\n📋 Current API Configuration:")
    print("-" * 40)
    
    config_vars = [
        ('API_KEY', '***hidden***'),
        ('API_BASE_URL', os.getenv('API_BASE_URL', 'Not set')),
        ('MODEL_NAME', os.getenv('MODEL_NAME', 'Not set')),
        ('API_PROVIDER', os.getenv('API_PROVIDER', 'Not set'))
    ]
    
    for var, value in config_vars:
        if var == 'API_KEY':
            api_key = os.getenv('API_KEY')
            if api_key:
                display_value = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***set***"
            else:
                display_value = "Not set"
        else:
            display_value = value
        
        print(f"{var:<15}: {display_value}")


def main():
    parser = argparse.ArgumentParser(description="Test AI Investment System API configuration")
    parser.add_argument('--provider', choices=list(PROVIDER_CONFIGS.keys()), 
                       help='Test specific provider')
    parser.add_argument('--interactive', action='store_true', 
                       help='Interactive setup mode')
    parser.add_argument('--advanced', action='store_true',
                       help='Run advanced API tests')
    parser.add_argument('--show-config', action='store_true',
                       help='Show current configuration')
    
    args = parser.parse_args()
    
    print("🤖 AI Investment System - API Configuration Test")
    print("=" * 60)
    
    if args.show_config:
        show_current_config()
        return
    
    if args.interactive:
        interactive_setup()
        return
    
    if args.provider:
        print(f"Testing with provider: {args.provider}")
        # You would need to implement provider-specific testing here
    
    # Check environment
    if not check_env_file():
        print("\n💡 Tip: Run with --interactive flag for guided setup")
        print("   python test_api_config.py --interactive")
        return
    
    show_current_config()
    
    # Run basic test
    success = test_api_basic()
    
    # Run advanced test if requested
    if args.advanced and success:
        test_api_advanced()
    
    if success:
        print("\n🎉 All tests passed! Your API configuration is ready.")
        print("\nNext steps:")
        print("1. Run a stock analysis: python src/main.py --ticker 600519")
        print("2. Try backtesting: python src/backtester.py --ticker 600519 --start-date 2024-01-01")
    else:
        print("\n❌ Tests failed. Please check your configuration.")
        print("\n💡 Troubleshooting tips:")
        print("1. Verify your API key is correct")
        print("2. Check your internet connection")
        print("3. Ensure the API endpoint is accessible")
        print("4. Run with --interactive for guided setup")


if __name__ == "__main__":
    main()