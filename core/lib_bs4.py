#
# class bs4 for parce html code
#

#libs
import bs4

class Selector_Serch:

    # constructor
    def __init__(self, data, fixLinks = None):
        
        # init bs
        self.data = bs4.BeautifulSoup(str(data), "html.parser")

        # check and repair links
        if fixLinks:
            self.Fix_Links(fixLinks)
            
    
    # search tags
    def Search_Tags(self, tag_name, class_name):
        return self.data.find_all(tag_name, class_=class_name)
    
    #search one tag
    def Search_One_Tag(self, tag_name, class_name = None):

        if class_name:
            return self.data.find(tag_name, class_=class_name)
        else:
            return self.data.find(tag_name)

    #search by id
    def Search_By_Id(self, id:str):
        return self.data.find(id=id)
            
            

    #fix all links
    def Fix_Links(self, add_link):
        for link in self.data.find_all('a'):
            try:
                link['href'] = add_link + link['href']
            except:
                pass