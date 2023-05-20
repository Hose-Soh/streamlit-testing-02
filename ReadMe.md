# Omdena-Nitrolytics - MVP 2

## Setup Instructions
This section describes the steps require to install and configure the MVP 2 application.

### Pre-Requisites


### Installing Dependencies
The MVP 2 Application includes a __requirements.txt__ that will install all the dependencies for the application to run.
These can be installed via pip using

__pip install -r requirements.txt__

__Note:__ It is recommended that you use a virtual environment manager such as __conda__, __pipenv__, __virtualenv__ or __poetry__ to create a new environment install the dependencies and run the application

__Note for Windows Users:__ 
The Python dependencies for this application includes [GDAL](https://gdal.org/) which can be problematic to install on Windows machines.
The following instructions should be followed:

1. Download the GDAL Wheel file for your Windows version and Python version from <https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal?
2. Install the downloaded GDAL wheel using PIP
__pip install PATH_TO_GDAL_WHEEL__


## Configuring MVP2
The MVP2 application requires you to have a Google Earth Engine account and active project.
You can sign up for Google Earth Engine at <https://code.earthengine.google.com/register>
Once you have registered and created a Google Earth Engine project, you need to create a Service Account to enable the MVP 2 application to access Google EE.
Details of how to create a service account can be found at <https://developers.google.com/earth-engine/guides/service_account>
For the created service account download the Private key for the service account so that the information can be provided to the MVP2 application.

Once the Service Account has been created and the private key downloaded, we need to set up a Streamlit secrets file.
Information about Streamlit secrets files can be found at <https://blog.streamlit.io/secrets-in-sharing-apps/>
To do this create a file called __secrets.toml__ in the __mvp_2_streamlit/.streamlit__ folder.
This file needs two entries:

Property        | Content
----------------|----------
service_account | This is the name of your Google EE Service Account
json_data       | This is the content of your private key json file for your Google EE Service Account


## Running the application
The MVP 2 application is a streamlit application and can be run the MVP 2 application use the command:

__streamlit run Home.py__

