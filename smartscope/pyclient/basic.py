import requests
from requests.auth import HTTPBasicAuth

DETAILED = 'detailed/'

class MainPyClient():

    def __init__(self):
        self._headers = {'Authorization': 'Token 2aacc9f9fceb89117ae61b9dc0b5ad84901e28e3'}
        self._main_endpoint = 'https://dev.smartscope.org/api/'
        self._current_endpoint = self._main_endpoint
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
            detailed_endpoint = self._urlsDict[label] + DETAILED
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

    def getAllObject(self, label):
        results = []
        endpoint = self.getLabelUrl(label)
        r = requests.get(endpoint, headers=self.getHeaders(), verify=False)
        resp_jason = r.json()
        results = r.json()['results']

        while resp_jason['next'] != None:
            endpoint = correctEndpointFormat(resp_jason['next'])
            print(endpoint)
            r = requests.get(endpoint, headers=self.getHeaders(), verify=False)
            results.extend(r.json()['results'])
            resp_jason = r.json()

        return results

    def getAllDetailedObject(self, label):
        results = []
        detailed_endpoint = self.getDetailedLabelUrl(label)
        if detailed_endpoint:
            r = requests.get(detailed_endpoint, headers=self.getHeaders(), verify=False)
            resp_jason = r.json()
            results = r.json()['results']

            while resp_jason['next'] != None:
                detailed_endpoint = correctEndpointFormat(resp_jason['next'])
                print(detailed_endpoint)
                r = requests.get(detailed_endpoint, headers=self.getHeaders(), verify=False)
                results.extend(r.json()['results'])
                resp_jason = r.json()

        return results


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
    # print(pyclient.getUrlsDict())
    # print(pyclient.getLabelUrl('users'))
    # print(pyclient.getDetailedLabelUrl('squares'))
    print(pyClient.getAllDetailedObject('squares')[1])
