Scipion-em-smarscope
=======================

Plugin to manage the interaction with the SmartScope framework.

Installation
------------
You will need to install SmartScope previous the plugin installation
https://docs.smartscope.org/ 
Follow the steps to install it with Docker
https://docs.smartscope.org/installation.html
(Installation with Anaconda/Miniconda is not abailable yet)



Developer's version

   * download repository

   .. code-block::

      git clone -b devel https://github.com/scipion-em/scipion-em-smartscope.git

   * install

   .. code-block::

      scipion installp -p /path/to/scipion-em-smartscope --devel

* Smartscope provide a token when the installation finish and you are logged, visit  https://docs.smartscope.org/api/rest/prog_api/#obtaining-an-api-token for more details. Please add the token in the scipion.conf file as **SMARTSCOPE_TOKEN** = ...XXXfeb270a1bc4120b1XXXX...
* Smartscope will save the data (not the acquisition managed by SerialEM) in the path you decided in the installation procedure https://docs.smartscope.org/getting_started/installation/docker/docker/#1-download-the-minimal-configuration-files. Please, provide that information on the scipion.conf as **SMARTSCOPE_DATA_SESSION_PATH** = path/smartscope/save/data
* Add the url to acces to the Smartscope web, by default is http://localhost:48000/ but if you change the url or the port please add the new url in the scipion.conf as **SMARTSCOPE_LOCALHOST** = http://localhost:48000/

Once you edit the scipion.conf please save it and run *scipion config*


Protocols
---------
* smartscope connection
* Provide calculations
* Smartscope feedback
