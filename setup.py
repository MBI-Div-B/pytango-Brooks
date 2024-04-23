from setuptools import setup, find_packages

setup(
    name="tangods_brookssla",
    version="0.0.1",
    description="Tango Device for Brooks",
    author="Marin Hennecke",
    author_email="hennecke@mbi-berlin.de",
    python_requires=">=3.6",
    entry_points={"console_scripts": ["BrooksSLA = tangods_brookssla:main"]},
    license="MIT",
    packages=["tangods_brookssla"],
    install_requires=[
        "pytango",
        "six",
    ],
    url="https://github.com/MBI-Div-b/pytango-BrooksSLA",
    keywords=[
        "tango device",
        "tango",
        "pytango",
    ],
)
