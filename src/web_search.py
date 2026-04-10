import requests

class DuckDuckGo:
    def search(self, query):
        url = 'https://api.duckduckgo.com/'
        params = {'q': query, 'format': 'json'}
        response = requests.get(url, params=params)
        return response.json()


def search_web(query):
    ddg = DuckDuckGo()
    results = ddg.search(query)
    return results['RelatedTopics'] if 'RelatedTopics' in results else []


def web_search_tool():
    query = input('Enter your search query: ')
    results = search_web(query)
    for result in results:
        print(f"Title: {result['Text']}, URL: {result['FirstURL']}")
