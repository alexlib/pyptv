# Notes about helping with Distributions.

pyptv uses Enthought's Chaco, which in turn uses other Enthought packages. These packages need to be compiled, and do not have accessible wheels. Whe you `pip install chaco` you need to have a compiler, Swig and a bunch of libraries. We don't want that.

The solution to this was to open our own private PyPI repository, compile the packages ourselves and upload the wheels there. We took care of Python 3.6 and 3.7 - only 64 bit. Now installying pyptv is as simple as telling pip to use our repository first, before PyPI.

Here is how you install pyptv, once you have Python 3.6 or 3.7 installed.

1. Create a virtual environment (optional)
2. Make sure you have the latest version of pip:
   
    `python -m pip install --upgrade pip`
3. Install numpy

    `pip install numpy`
4. Install pyptv:

    `pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple`


That's it. You can now run pyptv from the shell or command prompt:

    pyptv <directory>

# Settings up for each OS
## Windows
Setting up for Windows was easiest. It was just a matter of downloading the wheels for `chaco` and `enable` from the [Chrisoph Gohlke's excellent site](https://www.lfd.uci.edu/~gohlke/pythonlibs/).

## Linux
The following Entought packages had to be precompiled:

* chaco
* enable
* traits
* traitsui

For that we've created a Dockerfile that is based off the [manylinux2010 Dockerfile](https://discuss.python.org/t/manylinux2010-docker-image-now-available/1471).



