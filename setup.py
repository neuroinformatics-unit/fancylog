from setuptools import setup, find_packages


setup(
    name="fancylog",
    version="0.2.2",
    description="Fancier logging in Python",
    install_requires=["packaging", "rich"],
    extras_require={
        "dev": [
            "black",
            "pytest-cov",
            "pytest",
            "coverage",
            "bump2version",
            "pre-commit",
            "flake8",
        ]
    },
    python_requires=">=3.6",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/adamltyson/fancylog",
    author="Adam Tyson",
    author_email="adam.tyson@ucl.ac.uk",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Intended Audience :: Developers",
    ],
)
