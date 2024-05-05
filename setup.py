import os
import ast
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist
import glob

pyamares_init_file = os.path.join(os.path.dirname(__file__), "pyAMARES", "__init__.py")


def get_version(init_file_path, *variables):
    with open(init_file_path, "r") as file:
        file_content = file.read()
    tree = ast.parse(file_content)
    vars_dict = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in variables:
                    value = eval(
                        compile(ast.Expression(node.value), init_file_path, "eval")
                    )
                    vars_dict[target.id] = value
    return vars_dict


vars_dict = get_version(pyamares_init_file, "__version__", "__author__")
__version__ = vars_dict.get("__version__")
__author__ = vars_dict.get("__author__")


# __version__ = "0.2"
# __author__ = "Jia Xu"
# from pyAMARES import __author__, __version__
class CustomSDist(_sdist):
    user_options = _sdist.user_options + [
        ("include-docs", None, "Include documentation in the distribution")
    ]

    def initialize_options(self):
        _sdist.initialize_options(self)
        self.include_docs = False

    def finalize_options(self):
        _sdist.finalize_options(self)

    def run(self):
        if self.include_docs:
            self.distribution.data_files.extend(
                [
                    ("docs", glob.glob("docs/source/**", recursive=True)),
                    ("docs", glob.glob("docs/*.*")),
                    ("docs", ["docs/Makefile"]),
                ]
            )
        _sdist.run(self)


jupyter_requirements = [
    "ipykernel",
    "notebook",
]

doc_requirements = [
    "sphinx",
    "nbsphinx",
    "sphinx_tabs",
    "sphinx_rtd_theme",
    "Pygments",
    "ipywidgets",
]


setup(
    name="pyAMARES",
    version=__version__,
    author=__author__,
    author_email="jia-xu-1@uiowa.edu",
    description="pyAMARES, an Open-Source Python Library for Fitting Magnetic Resonance Spectroscopy Data",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    url="https://github.com/hawkMRS/pyAMARES",  # Optional project URL
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",  # Minimum Python version requirement
    install_requires=[
        "pandas>=1.1.0",
        "matplotlib>=3.1.3",
        "lmfit",
        "numpy>=1.18.1",
        "scipy>=1.2.1",
        "hlsvdpro>=2.0.0",
        "sympy",
        "nmrglue",
        "xlrd",
        "jinja2",
        "tqdm",
        "mat73",
        "ipython",
        "ipykernel",
    ],
    extras_require={
        "docs": doc_requirements,
        "jupyter": jupyter_requirements,
    },
    cmdclass={
        "sdist": CustomSDist,
    },
    data_files=[],
    zip_safe=False,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "amaresFit=pyAMARES.script.amaresfit:main",
        ],
    },
)
