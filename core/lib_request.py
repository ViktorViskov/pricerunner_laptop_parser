# 
# class for load page
# 

# libs
import requests

# async class for load data
class Browser:
    
    # constructor
    def __init__(self, url, load_counter = 30):
        # max count
        self.load_counter =load_counter

        # load page
        self.data = self.Load(url)
    
    # fast load using requests
    def Load(self, url):
        # variable to result
        result = ""

        # try to load page
        count_number = 1
        
        # loop counter 
        while count_number <= self.load_counter:
            # open link and parse data
            try:
                result = requests.request("GET", url).content.decode()
                break;
            except:
                print("Link %s not response. Retry number %d" % (url, count_number))
                count_number += 1
        
        # return result
        return result
        