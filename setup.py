import re
import setuptools

with open('requirements.txt') as f:
    # clean from comments empty lines and -r local_requirements.txt
    INSTALL_REQUIRES = list(filter(
        lambda x: x != "" and not re.match("-r requirements.txt|#", x), f.read().splitlines()))

setuptools.setup(
    name="surfQuake",
    version="0.0.1",
    author="Roberto Cabieces Díaz and Thiago C. Junqueira, ",
    description="GUI of surfQuake.",
    long_description="Package for digitalization",
    long_description_content_type="text/markdown",
    url="https://projectisp.github.io/surfquaketutorial.github.io/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        'License :: OSI Approved :: GNU Library or ' +
                'Lesser General Public License (LGPL)',
        "Operating System :: OS Independent",
    ],
    install_requires=INSTALL_REQUIRES,
    python_requires='>=3.9',
)
