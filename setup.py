from setuptools import setup, find_packages
setup(
    name='mcqgenerator',
    version='0.0.1', 
    author='Mah-Rukh Fida',
    author_email='mrukh@glos.ac.uk',   
    install_requires=['openai','langchain','streamlit','python-dotenv','PyPDF2'],                      
    packages=find_packages()
)