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

    def setCurrentEndpoint(self, newEndpoint):
        self._current_endpoint = newEndpoint

    def getUrlsDict(self):
        return self._urlsDict

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

    # def getAllObjects(self, label):
    #     results = []
    #     endpoint = self.getLabelUrl(label)
    #     r = requests.get(endpoint, headers=self.getHeaders(), verify=False)
    #     resp_jason = r.json()
    #     results = r.json()['results']
    #
    #     while resp_jason['next'] != None:
    #         endpoint = correctEndpointFormat(resp_jason['next'])
    #         print(endpoint)
    #         r = requests.get(endpoint, headers=self.getHeaders(), verify=False)
    #         results.extend(r.json()['results'])
    #         resp_jason = r.json()
    #
    #     return results
    #
    # def getAllDetailedObjects(self, label):
    #     results = []
    #     detailed_endpoint = self.getDetailedLabelUrl(label)
    #     if detailed_endpoint:
    #         r = requests.get(detailed_endpoint, headers=self.getHeaders(), verify=False)
    #         resp_jason = r.json()
    #         results = r.json()['results']
    #
    #         while resp_jason['next'] != None:
    #             detailed_endpoint = correctEndpointFormat(resp_jason['next'])
    #             print(detailed_endpoint)
    #             r = requests.get(detailed_endpoint, headers=self.getHeaders(), verify=False)
    #             results.extend(r.json()['results'])
    #             resp_jason = r.json()
    #
    #     return results

    # Method from Smartscope API
    # def get_from_API(self, route: str, filters: dict) -> list[dict]:
    #     request_hole = f'{self.getMainEndpoint()}{route}/?'
    #     for i, j in filters.items():
    #         request_hole += f'{i}={j}&'
    #     print(f'Requested url: {request_hole}')
    #     resp = requests.get(request_hole, headers=self.getHeaders(), verify=False)
    #     return json.loads(resp.content)['results']


    def getFromSmartScopeAPI(self, route: str, filters: dict):
        response = []
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

    def getDetailedFromSmartScopeAPI(self, route: str, filters: dict):
        response = []
        request_hole = f'{self.getMainEndpoint()}{route}/{DETAILED}/?'
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
            #print(page_response)
            response.extend(page_response)

        return response

    def getholeBasicFromSmartScopeAPI(self, route: str, filter: str):
        response = []
        request_hole = f'{self.getMainEndpoint()}{route}/{filter}'
        print(f'Requested url: {request_hole}')
        resp = requests.get(request_hole, headers=self.getHeaders(), verify=False)
        resp_jason = resp.json()
        print(resp_jason)

    def putHoleAPI(self, route: str, filter: str, put: str):
        put_hole = f'{self.getMainEndpoint()}{route}/{filter}/{put}'
        str2Put = {'hole_id': 'autoloader_square52_hVo2oU8n7A', 'id': 'autoloader_square52_hVo2oU8n7A', 'name': 'autoloader_square52_hole76', 'number': 76, 'pixel_size': None, 'shape_x': None, 'shape_y': None, 'selected': True, 'status': 'completed', 'completion_time': None, 'radius': 65, 'area': 13478.217882063609, 'bis_group': '52_76', 'bis_type': 'center', 'grid_id': '1autoloadermdll0XaKyIC5XYWo86D', 'square_id': 'autoloader_square52s56Y8DKiaVw'}
        print(put_hole)
        r = requests.put(put_hole, data={'status': 'null'}, verify=False)
        print(r, '\n', r.content)


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
    # Query the holes from a specific square that were not selected or acquired
    # print(pyClient.get_from_API('holes', filters=dict(square_id='grid1_square35sxLmmo6CmPOTPkAB')))#, status='null'))))

    # response = pyClient.getFromSmartScopeAPI('holes', filters=dict(square_id='grid1_square35sxLmmo6CmPOTPkAB'))
    #response = pyClient.getDetailedFromSmartScopeAPI('squares', filters=dict(square_id='grid1_square35sxLmmo6CmPOTPkAB'))
    #response = pyClient.getDetailedFromSmartScopeAPI('holes', filters=dict(hole_id='autoloader_square52_6dy9ZW54ty'))
    #response = pyClient.getDetailedFromSmartScopeAPI('squares', filters=dict(square_id='autoloader_square52s56Y8DKiaVw'))
    response = pyClient.getholeBasicFromSmartScopeAPI('holes', filter='autoloader_square52_hVo2oU8n7A')
    print(response)
    put = pyClient.putHoleAPI('holes', filter='autoloader_square52_hVo2oU8n7A', put='?format=api')

    #print(response)
    #https://dev.smartscope.org/api/holes/?square_id=grid1_square35sxLmmo6CmPOTPkAB&