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
        started, complete = protocol.sessionOpen()
        sList = []
        live = ''
        lastSFound = False
        lastCFound = False
        for s in reversed(sessionList):
            if started:
                if started == s.getSessionId() and lastSFound == False:
                    live = '  *last started*'
                    lastSFound = True
            if complete:
                if complete == s.getSessionId() and lastCFound == False:
                    live = '  *last complete*'
                    lastCFound = True
            date = datetime.datetime.strptime(s.getDate(),'%Y%M%d')

            sList.append(['{}-{}-{}\t{}{}'.format(
                                            date.strftime("%Y"),
                                            date.strftime("%M"),
                                            date.strftime("%d"),s.getSession(),
                                            live), s.getSession()])
            live = ''

        finalList = []
        for i in sList:
            finalList.append(String(i[0]))
        provider = ListTreeProviderString(finalList)
        dlg = dialog.ListDialog(form.root, "Sessions available", provider,
        "Select the session (sorted by date)")
        try:
            OutStr = dlg.values[0].get()
            OutStr = OutStr.replace('  *last session started*', '')
            name = OutStr[OutStr.find('\t')+1:]
            for s in sList:
                if name in s[0]:
                    form.setVar('sessionName', name)
        except IndexError:#Nos selection
            pass
