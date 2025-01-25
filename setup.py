from setuptools import setup, find_packages

setup(
    name="darwinex_portfolio_optimization",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "requests",
        "python-dotenv",
        "scipy",
        "matplotlib",
        "seaborn"
    ],
    description="A CLI for Darwinex portfolio optimization, with preprocessed fees in data/processed.",
    author="Charly López",
    author_email="clriesco@gmail.com",
    url="https://github.com/clriesco/darwinex_portfolio_optimizator",
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "darwinex-cli=src.cli.main:main",
        ],
    },
)
