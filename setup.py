from setuptools import setup, find_packages

setup(name='tivel',
      version='0.1',
      description='Module to connect Checkout Cielo using Tivel ERP',
      url='http://github.com/mfagundes/tivel',
      author='Mauricio Fagundes',
      author_email='mauricio.fagundes@gmail.com',
      license='MIT',
      zip_safe=False,
      packages=find_packages(),
      package_dir={"tivel": "tivel"},
      include_package_data=True,
      )
