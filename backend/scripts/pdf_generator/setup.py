"""
Setup script for clima-scope-pdf-generator package.

This file is kept for backward compatibility.
For new installations, use: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Check if we're in the package directory (has __init__.py)
current_dir = Path(__file__).parent
is_package_dir = (current_dir / "__init__.py").exists()

if is_package_dir:
    # We're installing from within the package directory
    # Tell setuptools that pdf_generator package is in current directory
    packages = ["pdf_generator"]
    package_dir = {"pdf_generator": "."}
    package_data = {"pdf_generator": ["sample_data/*.json"]}
else:
    # Installing from parent directory
    packages = find_packages(exclude=["tests", "*.tests", "*.tests.*", "venv", "__pycache__"])
    package_dir = {}
    package_data = {"pdf_generator": ["sample_data/*.json"]}

setup(
    name="clima-scope-pdf-generator",
    version="0.2.0",
    description="AI-powered PDF report generator for Clima-scope weather reports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Clima-scope Team",
    python_requires=">=3.8",
    packages=packages,
    package_dir=package_dir,
    package_data=package_data,
    install_requires=[
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
        "pydantic>=2.9.0",
        "python-dateutil>=2.9.0",
        "openai>=1.0.0",
    ],
    extras_require={
        "anthropic": ["anthropic>=0.18.0"],
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "all": [
            "clima-scope-pdf-generator[anthropic,dev]",
        ],
    },
    entry_points={
        "console_scripts": [
            "clima-pdf-generate=pdf_generator.generate_sample:main",
            "clima-pdf-generate-ai=pdf_generator.generate_ai_sample:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
