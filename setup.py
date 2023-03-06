import re

import setuptools

with open('requirements.txt') as f:
    # clean from comments empty lines and -r local_requirements.txt
    INSTALL_REQUIRES = list(filter(
        lambda x: x != "" and not re.match("-r local_requirements.txt|#", x), f.read().splitlines()))

setuptools.setup(
    name="loc_flow_tools",
    version="0.0.1",
    author="Thiago C. Junqueira, Cristina, Roberto Cadias",
    description="Package for Earthquake Location.",
    long_description="Package for digitalization.",
    long_description_content_type="text/markdown",
    url="https://github.com/cpalalo/loc-flow-isp.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        'License :: OSI Approved :: GNU Library or ' +
                'Lesser General Public License (LGPL)',
        "Operating System :: OS Independent",
    ],
    install_requires=INSTALL_REQUIRES,
    python_requires='>=3.8',
)
