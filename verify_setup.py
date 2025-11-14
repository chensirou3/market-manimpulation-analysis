"""
Setup verification script.

Run this script to verify that the project is correctly set up.
"""

import sys
import importlib.util
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("=" * 60)
    print("Checking Python version...")
    print("=" * 60)
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ ERROR: Python 3.10+ required")
        return False
    else:
        print("✓ Python version OK")
        return True


def check_dependencies():
    """Check if required packages are installed."""
    print("\n" + "=" * 60)
    print("Checking dependencies...")
    print("=" * 60)
    
    required = [
        'numpy',
        'pandas',
        'matplotlib',
        'yaml',
        'scipy',
        'sklearn',
        'statsmodels'
    ]
    
    missing = []
    
    for package in required:
        # Handle special cases
        module_name = 'yaml' if package == 'yaml' else package
        module_name = 'sklearn' if package == 'sklearn' else module_name
        
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
        else:
            print(f"✓ {package} - installed")
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All dependencies installed")
        return True


def check_project_structure():
    """Check project structure."""
    print("\n" + "=" * 60)
    print("Checking project structure...")
    print("=" * 60)
    
    required_dirs = [
        'src',
        'src/config',
        'src/data_prep',
        'src/baseline_sim',
        'src/anomaly',
        'src/factors',
        'src/backtest',
        'src/utils',
        'data',
        'docs',
        'notebooks',
        'tests'
    ]
    
    required_files = [
        'README.md',
        'requirements.txt',
        '.gitignore',
        'src/config/config.yaml',
        'docs/progress_log.md',
        'docs/design_notes.md'
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - MISSING")
            all_ok = False
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_ok = False
    
    if all_ok:
        print("\n✓ Project structure OK")
    else:
        print("\n❌ Some files/directories are missing")
    
    return all_ok


def check_imports():
    """Check if project modules can be imported."""
    print("\n" + "=" * 60)
    print("Checking module imports...")
    print("=" * 60)
    
    modules = [
        'src.utils.paths',
        'src.utils.logging_utils',
        'src.data_prep.tick_loader',
        'src.data_prep.bar_aggregator',
        'src.baseline_sim.fair_market_sim',
        'src.anomaly.price_volume_anomaly',
        'src.factors.manipulation_score',
        'src.backtest.pipeline'
    ]
    
    all_ok = True
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"❌ {module} - ERROR: {e}")
            all_ok = False
    
    if all_ok:
        print("\n✓ All modules can be imported")
    else:
        print("\n❌ Some modules failed to import")
    
    return all_ok


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("MARKET MANIPULATION DETECTION TOOLKIT")
    print("Setup Verification")
    print("=" * 60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Dependencies", check_dependencies),
        ("Module Imports", check_imports)
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "=" * 60)
        print("✓ ALL CHECKS PASSED!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Run simulations: python -m src.baseline_sim.fair_market_sim")
        print("2. Run tests: pytest tests/")
        print("3. Open notebooks: jupyter notebook")
        print()
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        print("\nPlease fix the issues above before proceeding.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

