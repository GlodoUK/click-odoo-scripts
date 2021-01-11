from setuptools import find_packages, setup

setup(
    name="click-odoo-scripts",
    description="click-odoo scripts collection",
    long_description="click-odoo scripts collection",
    version="12.0.1.0.0",
    packages=find_packages(),
    include_package_data=True,
    setup_requires=[],
    install_requires=["click-odoo>=1.3.0"],
    license="LGPLv3+",
    author="Glodo",
    author_email="techy@glodo.uk",
    url="http://github.com/glodouk/click-odoo-scripts",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: "
        "GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: Odoo",
    ],
    entry_points="""
        [console_scripts]
        click-odoo-fifo-vacuum=click_odoo_scripts.fifo_vacuum:main
        click-odoo-fix-quants=click_odoo_contrib.fix_quants:main
    """,
)
