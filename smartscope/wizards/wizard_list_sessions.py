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
        sList = []
        dateList = []

        for s in reversed(sessionList):
            date = datetime.datetime.strptime(s.getDate(),'%Y%M%d')
            sList.append(['{}\tDate: {}-{}-{}'.format(s.getSession(),
                                            date.strftime("%Y"),
                                            date.strftime("%M"),
                                            date.strftime("%d")),
                         s.getSession()])
        #     dateList.append(s.getDate())
        # sorted_lst = sorted(dateList, key=lambda x:
        #                         datetime.datetime.strptime(x, '%Y%M%d'))
        # for s in sList:
        #     if s[0] == sorted_lst[-1]:
        #         form.setVar('sessionName', s[2])



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
