"""
AetherLang - A powerful DSL for AI Workflow Orchestration
"""
from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
setup(
    name="aetherlang",
    version="0.3.1",
    author="NeuroAether",
    author_email="echelonvoids@protonmail.com",
    description="A powerful Domain-Specific Language for AI Workflow Orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/contrario/aetherlang",
    project_urls={
        "Homepage": "https://neurodoc.app/aether-nexus-omega-dsl",
        "Bug Tracker": "https://github.com/contrario/aetherlang/issues",
        "Documentation": "https://github.com/contrario/aetherlang/tree/main/docs",
        "Source Code": "https://github.com/contrario/aetherlang",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "aetherlang=aetherlang.__main__:main",
        ],
    },
    keywords="dsl workflow orchestration ai llm gpt automation pipeline",
    include_package_data=True,
    zip_safe=False,
)
