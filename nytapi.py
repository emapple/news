import numpy as np
import requests
import re
import time


class nytAPI:
    def __init__(self, api_key):
        """Initialize the API class"""
        self.api_key = api_key
        self.last_url = None
        self.last_search = None
    
    def _encode_fq(self, opt_dict):
        """Encode the filter query"""
        encoded_strings = []
        for key in opt_dict.keys():
            option = np.array(opt_dict[key])
            option = np.char.add(np.char.add('"', option), '"')
            try:
                option = ' '.join(option)
            except TypeError:  # isn't a list
                pass
            option = f'{key}:({option})'
            encoded_strings.append(option)
        return ' AND '.join(encoded_strings)
    
    def _encode_options(self, **kwargs):
        """Encode all passed options"""
        encoded_strings = []
        for key in kwargs.keys():
            if isinstance(kwargs[key], dict):
                encoded_strings.append(self._encode_fq(kwargs[key]))
            else:
                encoded_strings.append(kwargs[key])
        return '&'.join([f'{key}={encoded_string}' 
                         for key, encoded_string in
                         zip(kwargs.keys(), encoded_strings)])
            
    def search(self, **kwargs):
        """Search the NYT API with given keywords"""
        
        url = 'https://api.nytimes.com/svc/search/v2/articlesearch.json' + '?'
        url += self._encode_options(**kwargs)
        url += '&api-key=' + self.api_key
        
        # make sure booleans are lower case
        for val in ['True', 'False']:
            url = url.replace(val, val.lower())
        
        req = requests.get(url)
        req.raise_for_status()
        
        self.last_url = re.sub('api-key=.*$', 'api-key="API-KEY"', req.url)
        self.last_search = re.sub('api-key=.*$', 'api-key="API-KEY"', url)
        
        return req.json()
    
    def search_iterative(self, **kwargs):
        """Searches all pages until reaching end of list, given query"""
        if 'page' in kwargs:
            raise ValueError('Cannot specify page if iterating over all pages')
        page0 = self.search(**kwargs)
        time.sleep(6)
        num_hits = page0['response']['meta']['hits']
        max_page = int(np.ceil(num_hits / 10) - 1)
        new_dict = page0['response']['docs']
        for i in range(1, max_page + 1):
            new_page = self.search(page=i, **kwargs)
            new_dict += new_page['response']['docs']
            time.sleep(6)  # avoiding the rate limit

        test_headlines = [res['headline']['main'] for res in new_dict]
        # removing duplicates
        if len(set(test_headlines)) != len(test_headlines):
        	print('Removing duplicate entries')
        	clean_dict = []
        	for i in range(len(test_headlines)):
        		if new_dict[i]['headline']['main'] not in test_headlines[:i]:
        			clean_dict.append(new_dict[i])
        
        return new_dict
