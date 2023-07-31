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

        for s in sessionList:
            date = datetime.datetime.strptime(s.getDate(),'%Y%M%d')
            sList.append('Name: {}\tDate: {}-{}-{}'.format(s.getSession(),
                                            date.strftime("%Y"),
                                            date.strftime("%m"),
                                            date.strftime("%d")))
        #     dateList.append(s.getDate())
        # sorted_lst = sorted(dateList, key=lambda x:
        #                         datetime.datetime.strptime(x, '%Y%M%d'))
        # for s in sList:
        #     if s[0] == sorted_lst[-1]:
        #         form.setVar('sessionName', s[2])



        finalList = []
        for i in sList:
            finalList.append(String(i))
        provider = ListTreeProviderString(finalList)
        dlg = dialog.ListDialog(form.root, "Sessions available", provider,
        "Select the session")
        form.setVar('sessionName', dlg.values[0].get())
