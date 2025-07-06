#!/usr/bin/env python3
"""
QXChain Setup Script
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="qxchain",
    version="1.0.0",
    author="QXChain Development Team",
    author_email="dev@qxchain.org",
    description="Quantum-Resistant Blockchain Protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/qxchain/qxchain",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "qxchain-node=node:main",
            "qxchain-init=scripts.init_blockchain:main",
            "qxchain-demo=scripts.demo:main",
            "qxchain-test=scripts.test_network:main",
            "qxchain-multi=scripts.run_multi_node:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["dashboard/*.html", "dashboard/*.css", "dashboard/*.js"],
    },
)