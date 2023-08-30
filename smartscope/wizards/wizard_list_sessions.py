from pyworkflow.wizard import Wizard
from smartscope.protocols import smartscopeConnection
import datetime
from pyworkflow.gui import ListTreeProviderString, dialog
from pyworkflow.object import String

class smartscopeWizard(Wizard):
    _targets = [(smartscopeConnection, ['sessionName'])]

    def show(self, form, *params):
        protocol = form.protocol
        sessionList = protocol.sessionListCollection()
        sessionOpen = protocol.sessionOpen()
        sList = []
        live = ''
        lastFound = False

        for s in reversed(sessionList):
            if sessionOpen:
                if sessionOpen == s.getSessionId() and lastFound == False:
                    live = '*last session started*'
                    lastFound = True
            date = datetime.datetime.strptime(s.getDate(),'%Y%M%d')
            sList.append(['{}  \tDate: {}-{}-{}\t{}'.format(s.getSession(),
                                            date.strftime("%Y"),
                                            date.strftime("%M"),
                                            date.strftime("%d"), live),
                         s.getSession()])
            live = ''

        finalList = []
        for i in sList:
            finalList.append(String(i[0]))
        provider = ListTreeProviderString(finalList)
        dlg = dialog.ListDialog(form.root, "Sessions available", provider,
        "Select the session")
        name = dlg.values[0].get()[:dlg.values[0].get().find('\t')]
        for s in sList:
            if name in s[1]:
                form.setVar('sessionName', name)
