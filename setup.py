#!/usr/bin/env python3
"""
GitBridge Trust Graph Engine (GBP23) Setup
MAS Lite Protocol v2.1 Compliant
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gitbridge-trust-graph",
    version="23.0.0",
    author="GitBridge Development Team",
    author_email="dev@gitbridge.com",
    description="High-performance trust relationship management system for GitBridge SmartRepo ecosystem",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ZachLark/GitBridgev1",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.13",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "pytest-asyncio>=0.23.5",
            "black>=24.1.1",
            "pylint>=3.0.3",
            "mypy>=1.8.0",
        ],
        "test": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "pytest-asyncio>=0.23.5",
            "fakeredis>=2.29.0",
            "orjson>=3.10.18",
            "prometheus-client>=0.19.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gitbridge-trust=trust_graph:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.md"],
    },
    keywords="gitbridge, trust, graph, mas, multi-agent, protocol, performance",
    project_urls={
        "Bug Reports": "https://github.com/ZachLark/GitBridgev1/issues",
        "Source": "https://github.com/ZachLark/GitBridgev1",
        "Documentation": "https://github.com/ZachLark/GitBridgev1/tree/main/docs",
    },
    # MAS Lite Protocol v2.1 compliance metadata
    metadata_version="2.1",
    platforms=["any"],
    license="MIT",
    zip_safe=False,
) 