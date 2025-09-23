#!/usr/bin/env python3
"""
Setup script for PingDaddyPro
"""

from setuptools import setup, find_packages
import os

# Read version from VERSION file
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            return f.read().strip()
    return "1.0.3"  # fallback

# Read README for long description
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "Professional Website Monitoring Application"

setup(
    name="pingdaddypro",
    version=get_version(),
    description="Professional Website Monitoring Application",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="svejedobro",
    author_email="svejedobro@example.com",
    url="https://github.com/zaja/pingdaddypro",
    packages=find_packages(),
    py_modules=["pingdaddypro"],
    install_requires=[
        "Flask==2.3.3",
        "Flask-SocketIO==5.3.6",
        "requests==2.31.0",
        "bcrypt==4.0.1",
        "pytz==2023.3",
        "tzlocal==4.3.1",
        "matplotlib==3.8.2",
        "Pillow==10.0.0",
        "dnspython==2.4.2",
        "numpy>=1.24.0,<2.0.0",
        "psycopg2-binary==2.9.7",
        "SQLAlchemy==2.0.23",
        "python-dateutil==2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pingdaddypro=pingdaddypro:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
    ],
    python_requires=">=3.11",
    keywords="monitoring website uptime ssl performance docker flask postgresql",
    project_urls={
        "Homepage": "https://github.com/zaja/pingdaddypro",
        "Documentation": "https://github.com/zaja/pingdaddypro#readme",
        "Repository": "https://github.com/zaja/pingdaddypro.git",
        "Bug Tracker": "https://github.com/zaja/pingdaddypro/issues",
    },
)
