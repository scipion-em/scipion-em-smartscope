import requests
import json
from requests.auth import HTTPBasicAuth

DETAILED = 'detailed'

class MainPyClient():

    def __init__(self,
                 Authorization='Token 136737181feb270a1bc4120b19d5440b2f697c94',
                 endpoint='http://localhost:48000/api/'):
        #self._headers = {'Authorization': 'Token 2aacc9f9fceb89117ae61b9dc0b5ad84901e28e3'}#Tocken de Servidor
        self._headers = {'Authorization': Authorization}#Token @pavlov (alberto)
        #self._main_endpoint = 'https://dev.smartscope.org/api/'
        self._main_endpoint = endpoint
        self._current_endpoint = self._main_endpoint # No se si me convence esto
        # self._urlsDict = self._getAllEndpoints()
        # self._keys = self._urlsDict.keys()

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

    # def _getAllEndpoints(self):
    #     try:
    #         r = requests.get(self.getMainEndpoint(), headers=self.getHeaders(), verify=False)
    #         r.raise_for_status()
    #         urlsDict = r.json()
    #         correctDict = correctEndpointsDictFormat(urlsDict)
    #         return correctDict
    #     except requests.exceptions.HTTPError as errh:
    #         print("Http Error:", errh)
    #     except requests.exceptions.ConnectionError as errc:
    #         print("Error Connecting:", errc)
    #     except requests.exceptions.Timeout as errt:
    #         print("Timeout Error:", errt)
    #     except requests.exceptions.RequestException as err:
    #         print("OOps: Something Else", err)
    #
    #     return None

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
    def getDetailsFromParameter(self, route):
        response = []
        request = f'{self.getMainEndpoint()}{route}/?'
        print(f'Requested url: {request}')
        resp = requests.get(request, headers=self.getHeaders(), verify=False)
        resp_jason = resp.json()
        page_response = resp_jason['results']
        response.extend(page_response)

        while resp_jason['next'] != None:
            corrected_endpoint = correctEndpointFormat(resp_jason['next'])
            r = requests.get(corrected_endpoint, headers=self.getHeaders(), verify=False)
            resp_jason = r.json()
            page_response = resp_jason['results']
            #print(page_response)
            response.extend(page_response)

        return response
    def getRouteFromID(self, route, from_id, id, detailed=False, selected=False, completed=False):
        '''
        route: element you request for
        from_id: father of the requested element (square is the father of hole)
        id: identification of the requested element
        detailed: True if ou want a detailed response
        selected: A filter for recieve just the selected elements

        return: the response, json format
        '''
        response = []
        roude_id = '{}_id='.format(from_id)
        if selected == True:
            selected = 'selected=true'
        else:
            selected = ''
        if detailed == True:
            detailed = '/detailed'
        else:
            detailed = ''
        if completed == True:
            completed = 'status=completed'
        else:
            completed = ''
        request_hole = f'{self.getMainEndpoint()}{route}{detailed}/?{roude_id}{id}&{selected}&{completed}'
        print(f'Requested url: {request_hole}')
        resp = requests.get(request_hole, headers=self.getHeaders(), verify=False)
        resp_jason = resp.json()
        page_response = resp_jason['results']
        response.extend(page_response)

        while resp_jason['next'] != None:
            corrected_endpoint = correctEndpointFormat(resp_jason['next'])
            #print(f'Requested next url: {corrected_endpoint}')
            r = requests.get(corrected_endpoint, verify=False, headers=self.getHeaders())
            resp_jason = r.json()
            page_response = resp_jason['results']
            #print(page_response)
            response.extend(page_response)

        return response

    def getRouteFromName(self, route, from_name, name, detailed=False, selected=False, completed=False):
        '''
        route: element you request for
        from_id: father of the requested element (square is the father of hole)
        id: identification of the requested element
        detailed: True if ou want a detailed response
        selected: A filter for recieve just the selected elements

        return: the response, json format
        '''
        response = []
        roude_name = '{}='.format(from_name)
        if selected == True:
            selected = 'selected=true'
        else:
            selected = ''
        if detailed == True:
            detailed = '/detailed'
        else:
            detailed = ''
        if completed == True:
            completed = 'status=completed'
        else:
            completed = ''
        request_hole = f'{self.getMainEndpoint()}{route}{detailed}/?{roude_name}{name}&{selected}&{completed}'
        print(f'Requested url: {request_hole}')
        resp = requests.get(request_hole, headers=self.getHeaders(), verify=False)
        resp_jason = resp.json()
        page_response = resp_jason['results']
        response.extend(page_response)

        while resp_jason['next'] != None:
            corrected_endpoint = correctEndpointFormat(resp_jason['next'])
            #print(f'Requested next url: {corrected_endpoint}')
            r = requests.get(corrected_endpoint, verify=False, headers=self.getHeaders())
            resp_jason = r.json()
            page_response = resp_jason['results']
            #print(page_response)
            response.extend(page_response)

        return response

    def putParameterFromID(self, route, ID, data=''):
        #https://linuxhint.com/python-requests-put-method/
        #https://stackoverflow.com/questions/31089221/what-is-the-difference-between-put-post-and-patch
        url = f'{self.getMainEndpoint()}{route}/{ID}/'
        print(url)
        r = requests.patch(url, verify=False, headers=self.getHeaders(), data=data)
        if r.status_code == 200:
            print('element status updated')
        else:
            print('Error code: {}'.format(r.status_code))


def correctEndpointsDictFormat(urlsDict):
    newDict = {}
    for key, value in urlsDict.items():
        newDict[key] = correctEndpointFormat(value)

    return newDict

def correctEndpointFormat(url):
    newUrl = url.replace("http", "http")
    #newUrl = url.replace("http", "https")
    return newUrl


if __name__ == "__main__":
    pyClient = MainPyClient()
    #print(pyClient.getUrlsDict())

    # metadataSession = {'microscopes': None,'detectors': None, 'sessions': None}
    # for key, value in metadataSession.items():
    #     metadataSession[key] = pyClient.getDetailsFromParameter(key)
    # print(metadataSession['sessions'])

    grid = pyClient.getRouteFromID('microscopes', 'microscope', 'h0PgRUjUq2K2Cr1CGZJq3q08il8i5n')

    grid = pyClient.getRouteFromID('sessions', 'session', '20230216sdddnzXCTGbuvlikPiKAQw')
    # atlas = pyClient.getRouteFromID('atlas', 'grid', '1autoloaderucI1Nd2F55R0OY5E18g')
    #square = pyClient.getRouteFromID('squares', 'atlas', 'aaa_atlas3eITQ1lfEplhiFI73tEGz',detailed=True, selected=True)
    #hole = pyClient.getRouteFromID('holes', 'square', 'aaa_square436wzJ6ZzSH6oq5Nnr0o')#selected does not work for holes
    #highmag = pyClient.getRouteFromID('highmag', 'hole', 'aaa_square43_hole612z66b3yBcw9',detailed=True)#selected does not work for holes

    #pyClient.putHoleAPI(holeID='autoloader_square52_hVo2oU8n7A')
    #pyClient.putSquareAPI(squareID='grid1_square35sxLmmo6CmPOTPkAB')
    #pyClient.putParameterFromID('squares', 'aaa_square436wzJ6ZzSH6oq5Nnr0o', data={"selected": 'true'})
    #pyClient.putParameterFromID('holes', 'aaa_square43_hole612z66b3yBcw9', data={"selected": 'true'})

    '''
    Sesion garciaa en servidor:
    
    session = 20230201IreneBSQl7vwE4YGYREBZW
    grid = 1autoloaderucI1Nd2F55R0OY5E18g
    atlas = autoloader_atlastk768KPue7nlAZ
    square = autoloader_square23JZQjerrJVd9
    hole = autoloader_square23_KKtfGVyhM6
    
    Session en local @pavlov:
    session = 20230216pruebaguenaQHCyjsBSSMq
    grid = 1aaaGuDtnwQ0lFlmGu0Tkjkplf8cJZ
    atlas = aaa_atlas3eITQ1lfEplhiFI73tEGz
    square = aaa_square436wzJ6ZzSH6oq5Nnr0o
    hole = aaa_square43_hole612z66b3yBcw9
    '''
