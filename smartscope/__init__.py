# **************************************************************************
# *
# * Authors: Daniel Marchan (da.marchan@cnb.csic.es)
#            Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)
# *
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

"""
This modules contains protocols useful for Smartscope framework integration
"""

import pwem
from .constants import *

__version__ = "3.0.0"
_logo = "icon.png"
_references = ['Bouvette2022']


class Plugin(pwem.Plugin):
    pass
    @classmethod
    def getEnviron(cls, xmippFirst=True):
        pass

    @classmethod
    def _defineVariables(cls):
        cls._defineVar(SMARTSCOPE_LOCALHOST, 'http://localhost:48000/api/')
        cls._defineVar(SMARTSCOPE_TOKEN, 'Read Smartscope documentation to get the token...')
        cls._defineVar(SMARTSCOPE_DATA_SESSION_PATH, 'Path assigned to the data in the Smartscope installation')

        #https://docs.smartscope.org/getting_started/installation/docker/docker/#6-the-installation-is-done

    #conda create --name smartscopeenv python==3.9

