import requests
import json
from requests.auth import HTTPBasicAuth

DETAILED = 'detailed'

class MainPyClient():

    def __init__(self):
        self._headers = {'Authorization': 'Token 2aacc9f9fceb89117ae61b9dc0b5ad84901e28e3'}
        self._main_endpoint = 'https://dev.smartscope.org/api/'
        self._current_endpoint = self._main_endpoint # No se si me convence esto
        self._urlsDict = self._getAllEndpoints()
        self._keys = self._urlsDict.keys()

    def getHeaders(self):
        return self._headers

    def getMainEndpoint(self):
        return self._main_endpoint

    def getCurrentEndpoint(self):
        return self._current_endpoint

    def getUrlsDict(self):
        return self._urlsDict

    def setCurrentEndpoint(self, newEndpoint):
        self._current_endpoint = newEndpoint

    def setUrlsDict(self, dictUrls):
        self._urlsDict.set(dictUrls)

    def _getAllEndpoints(self):
        try:
            r = requests.get(self.getMainEndpoint(), headers=self.getHeaders(), verify=False)
            r.raise_for_status()
            urlsDict = r.json()
            correctDict = correctEndpointsDictFormat(urlsDict)
            return correctDict
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)

        return None

    def getLabelUrl(self, label):
        if label in self._keys:
            url = self._urlsDict[label]
            self.setCurrentEndpoint(url)
            return url
        else:
            print('The label is not found in the APIs endpoints')
            return None

    def getDetailedLabelUrl(self, label):
        if self.getLabelUrl(label):
            detailed_endpoint = self._urlsDict[label] + DETAILED + '/'
            try:
                r = requests.get(detailed_endpoint, headers=self.getHeaders(), verify=False)
                r.raise_for_status()
                return detailed_endpoint
            except requests.exceptions.HTTPError as errh:
                print("Http Error:", errh)
                return None
            except requests.exceptions.ConnectionError as errc:
                print("Error Connecting:", errc)
                return None
            except requests.exceptions.Timeout as errt:
                print("Timeout Error:", errt)
                return None
            except requests.exceptions.RequestException as err:
                print("OOps: Something Else", err)
                return None

        else:
            print('The label is not found in the APIs endpoints')
            return None


##COMMUNICATION
    def getSessions(self):
        route = 'sessions'
        request = f'{self.getMainEndpoint()}{route}/?'
        print(f'Requested url: {request}')
        resp = requests.get(request, headers=self.getHeaders(), verify=False)
        return resp.json()

    def getGrids(self):
        route = 'grids'
        request = f'{self.getMainEndpoint()}{route}/?'
        print(f'Requested url: {request}')
        resp = requests.get(request, headers=self.getHeaders(), verify=False)
        return resp.json()

    def getAtlas(self):
        route = 'atlas'
        request = f'{self.getMainEndpoint()}{route}/?'
        print(f'Requested url: {request}')
        resp = requests.get(request, headers=self.getHeaders(), verify=False)

        return resp.json()

    def getSquaresDetail(self):
        route = 'squares'
        response = []
        request_hole = f'{self.getMainEndpoint()}{route}/{DETAILED}/?'
        print(f'Requested url: {request_hole}')
        resp = requests.get(request_hole, headers=self.getHeaders(), verify=False)
        resp_jason = resp.json()
        page_response = resp_jason['results']
        response.extend(page_response)

        while resp_jason['next'] != None:
            corrected_endpoint = correctEndpointFormat(resp_jason['next'])
            print(corrected_endpoint)
            r = requests.get(corrected_endpoint, headers=self.getHeaders(), verify=False)
            resp_jason = r.json()
            page_response = resp_jason['results']
            #print(page_response)
            response.extend(page_response)

        return response

    def getHolesFromSquare(self, filters: dict):
        response = []
        route = 'holes'
        request_hole = f'{self.getMainEndpoint()}{route}/?'
        for i, j in filters.items():
            request_hole += f'{i}={j}&'
        print(f'Requested url: {request_hole}')
        resp = requests.get(request_hole, headers=self.getHeaders(), verify=False)
        resp_jason = resp.json()
        page_response = resp_jason['results']
        response.extend(page_response)

        while resp_jason['next'] != None:
            corrected_endpoint = correctEndpointFormat(resp_jason['next'])
            r = requests.get(corrected_endpoint, headers=self.getHeaders(), verify=False)
            resp_jason = r.json()
            page_response = resp_jason['results']
            response.extend(page_response)

        return response

    def getHighMagFromHole(self, filters: dict): #this are micrographs in png and the CTF and dates
        response = []
        route = 'highmag'
        request_hole = f'{self.getMainEndpoint()}{route}/?'
        for i, j in filters.items():
            request_hole += f'{i}={j}&'
        print(f'Requested url: {request_hole}')
        resp = requests.get(request_hole, headers=self.getHeaders(), verify=False)
        resp_jason = resp.json()
        page_response = resp_jason['results']
        response.extend(page_response)

        while resp_jason['next'] != None:
            corrected_endpoint = correctEndpointFormat(resp_jason['next'])
            r = requests.get(corrected_endpoint, headers=self.getHeaders(), verify=False)
            resp_jason = r.json()
            page_response = resp_jason['results']
            response.extend(page_response)

        return response

    def putHoleAPI(self, holeID: str):
        #https://linuxhint.com/python-requests-put-method/
        #https://stackoverflow.com/questions/31089221/what-is-the-difference-between-put-post-and-patch
        holes = 'holes'
        url = f'{self.getMainEndpoint()}{holes}/{holeID}/'
        print(url)
        r = requests.patch(url, verify=False, headers=self.getHeaders(), data={"selected": 'false'})
        if r.status_code == 200:
            print('hole status updated')
        else:
            print('Error code: {}'.format(r.status_code))

    def putSquareAPI(self, squareID: str):
        #https://linuxhint.com/python-requests-put-method/
        #https://stackoverflow.com/questions/31089221/what-is-the-difference-between-put-post-and-patch
        squares = 'squares'
        url = f'{self.getMainEndpoint()}{squares}/{squareID}/'
        print(url)
        r = requests.patch(url, verify=False, headers=self.getHeaders(), data={"selected": 'false'})
        if r.status_code == 200:
            print('Square status updated')
        else:
            print('Error code: {}'.format(r.status_code))


def correctEndpointsDictFormat(urlsDict):
    newDict = {}
    for key, value in urlsDict.items():
        newDict[key] = correctEndpointFormat(value)

    return newDict

def correctEndpointFormat(url):
    newUrl = url.replace("http", "https")
    return newUrl


if __name__ == "__main__":
    pyClient = MainPyClient()
    #print(pyClient.getUrlsDict())
    # print(pyclient.getLabelUrl('users'))
    # print(pyClient.getDetailedLabelUrl('squares'))
    #print(pyClient.getAllDetailedObject('squares')[1])

    response = pyClient.getSessions()
    response = pyClient.getGrids()
    response = pyClient.getAtlas()

    #response = pyClient.getSquaresDetail()
    #response = pyClient.getHolesFromSquare( filters=dict(square_id='grid1_square35sxLmmo6CmPOTPkAB'))
    #pyClient.putHoleAPI(holeID='autoloader_square52_hVo2oU8n7A')
    #pyClient.putSquareAPI(squareID='grid1_square35sxLmmo6CmPOTPkAB')

    print(response)
