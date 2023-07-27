from pyworkflow.wizard import Wizard
from smartscope.protocols import smartscopeConnection
import datetime

class smartscopeWizard(Wizard):
    # Dictionary to target protocol parameters
    _targets = [(smartscopeConnection, ['sessionName'])]

    def show(self, form, *params):
        protocol = form.protocol
        sessionList = protocol.sessionListCollection()
        sList = []
        dateList = []

        for s in sessionList:
            sList.append([s.getDate(), #yearMonthDay 20231215
                          s.getSessionId(),
                          s.getSession()])
            dateList.append(s.getDate())
        print(dateList)
        sorted_lst = sorted(dateList, key=lambda x: datetime.datetime.strptime(x, '%Y%M%d'))
        print(sorted_lst)
        for s in sList:
            if s[0] == sorted_lst[-1]:
                form.setVar('sessionName', s[2])

