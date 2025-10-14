"""Setup configuration for FLRTS Extensions Frappe app."""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="flrts_extensions",
    version="0.1.0",
    description="Custom Field Service Management extensions for BigSir FLRTS",
    author="10NetZero",
    author_email="ops@10nz.tools",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
    python_requires=">=3.10",
)
