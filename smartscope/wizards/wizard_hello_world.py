from pyworkflow.gui import ListTreeProviderString, dialog
from pyworkflow.object import String
from pyworkflow.wizard import Wizard
from smartscope.protocols import smartscopeConnection

class smartscopeWizard(Wizard):
    # Dictionary to target protocol parameters
    _targets = [(smartscopeConnection, ['sessionId'])]

    def show(self, form, *params):
        protocol = form.protocol
        sessionList = protocol.sessionListCollection() # COJO LO QUE QUIERO

        # Set the chosen value back to the form
        form.setVar('sessionId','') #elemento de la lista seleccionado)
