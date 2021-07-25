#
# Class for build new index page
#

# libs
import json
from re import split
import core.lib_bs4 as lib_bs4
import core.lib_request as lib_request
import core.mysql as mysql


class Page:

    # constructor
    def __init__(self, link:str, is_json:bool = False, link_processing = True) -> None:

        # link
        self.link = link

        # tag and class name from list
        self.tag = "div"
        self.item_class = "_2Vdwcz_zWR _1bgVr-M90D"

        # variable json
        self.is_json = is_json

        # init page browser
        self.browser = lib_request.Browser(True)

        # init mysql connection
        self.mysql = mysql.Mysql_Connect("server", "root", "dbnmjr031193", "pricerunner")

        # cpu library (optimization)
        self.cpu_library_single = {}
        self.cpu_library_multi = {}

        # mysql request optimization
        self.mysql_data = []

        # Load JSON data
        if is_json:

            # process link
            if link_processing:
                self.Url_Processing(link)

            # load page and decoding json
            self.json_data = json.loads(self.browser.Fast_Load(self.link))

        # load usually page
        else:
            # load page and init parser
            self.html = lib_bs4.Selector_Serch(self.browser.Load(self.link, 10), "https://www.pricerunner.dk")
        
        # create items
        self.Search_All_Items()



    # function for string processing (create link to request and get json)
    def Url_Processing(self, link):
        # get attributes from current link
        old_link_attributs = link.split("?")[1].split("&")
        # new link base
        new_link = "https://www.pricerunner.dk/public/search/category/products/v2/dk/27?size=1000"

        # variables for prices
        price_min = 0
        price_max = 0

        # add attributs to link
        for attribut in old_link_attributs:

            if "attr_" in attribut:
                value = attribut[5:].split("#")[0]
                new_link += "&af_%s" % value
            
            # laptop producent
            elif "man_id=" in attribut:
                value = attribut.split("=")[1]
                new_link += "&af_BRAND=%s" % value

            # screen size
            elif "s_" in attribut:
                value = attribut[2:]
                new_link += "&af_%s" % value
            # min price
            elif "price_min=" in attribut:
                price_min = attribut.split("=")[1]
            
            # max price
            elif "price_max=" in attribut:
                price_max = attribut.split("=")[1]
        
        # add prices
        if price_max != 0:
            new_link += "&af_PRICE=%s_%s" % (price_min, price_max)

        # set new link
        self.link = new_link    

    # update data in db
    def Send_To_Db(self):
        # delete all old data from mysql database
        self.mysql.I("DELETE FROM laptops")

        # write all records to db
        for record in self.mysql_data:
            self.mysql.I(record)

        
    # search all items and create new list
    def Search_All_Items(self):

        # create browser session
        browser = lib_request.Browser()

        # element number for log
        item_number = 1

        # if json
        if self.is_json:
            # search all items
            items = self.json_data['products']
            

            # loop for create one item
            for item in items:
                # get data and create one laptop
                self.Make_Json_List_Item(browser, item)

                # show load log
                print("Load %d from %d" % (item_number,len(items)))
                item_number += 1

                # reset browser
                if item_number % 20 == 0:
                    browser.Reset()


        # not json
        else:
            # search all items
            items = self.html.Search_Tags(self.tag, self.item_class)

            # loop for create one item
            for item in items:

                # get data and create one laptop
                self.Make_List_Item(browser, item)

                # show load log
                print("Load %d from %d" % (item_number,len(items)))
                item_number += 1

                # reset browser
                if item_number % 20 == 0:
                    browser.Reset()

        # update data in db
        self.Send_To_Db()
    

    # create one list item
    def Make_List_Item(self, browser, raw_data):
        # root item
        item_root = lib_bs4.Selector_Serch(raw_data, True)

        # link
        item_link = item_root.Search_One_Tag("a")['href']

        # link root open link and parse data
        item_link_root = lib_bs4.Selector_Serch(browser.Load(item_link))

        # title
        item_title = self.Get_Content(item_link_root.Search_One_Tag("h1", "_3EQkAqQ5yG _3AYzQcQVQY _1jJki9B9cm N6r6b1Dj9p _2a-Fh6PJxl _1xjlAtQYnE"))

        # desc
        item_desc = self.Get_Content(item_link_root.Search_One_Tag("p", "_2YSuzxkhlv _1qzdPtfx_v CzvSmP0Lzl _3iEqpBbRO7 css-2tmqko"))

        # cpu model (get list with properties)
        item_cpu = self.Get_Cpu_Model(item_link_root)

        # Battery 
        item_battery_time = self.Get_Battery_Time(item_link_root)

        # Resolution
        item_resolution = self.Get_Screen_Resolution(item_link_root)

        # geekbench points getting from 4 pages and get avarage number
        item_points_single , item_points_multi = self.Get_Geekbench_Points(browser, item_cpu, 4)

        # image
        item_image =  self.Get_Image_Src(item_root.Search_One_Tag("img", "_1eCHgH5-ru css-1shbqcj"))

        # current price
        price_buffer = self.Get_Content(item_link_root.Search_One_Tag("span", "_1j6NocjLHg _1hXG0xPrK5 _3GiEsJk2wF _3JJc-cEjsi css-2tmqko"))
        item_price = price_buffer if price_buffer != "" else 0

        # old price
        price_buffer = self.Get_Content(item_root.Search_One_Tag("span", "_1hXG0xPrK5 _3GiEsJk2wF _3JJc-cEjsi yNAlNXLNAJ css-2tmqko"))
        item_price_old = price_buffer if price_buffer != "" else item_price

         # add to buffer
        self.mysql_data.append("INSERT INTO laptops VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % (item_title, item_desc, item_link, item_price, item_price_old, item_image, item_cpu, item_battery_time, item_resolution, item_points_single, item_points_multi))
    
    # make JSON list item
    def Make_Json_List_Item(self, browser, item):

        # getting info
        item_title = item['name']
        item_desc = item['description']
        item_link = "https://www.pricerunner.dk" + item['url']
        item_price = item['lowestPrice']['amount']
        item_image ="https://www.pricerunner.dk" + item['image']['path']

        # get old price
        try:
            item_price_old = item['priceDrop']['oldPrice']['amount']
        except:
            item_price_old = item_price

        # open link and parse data
        item_link_root = lib_bs4.Selector_Serch(browser.Load(item_link))

        # CPU
        item_cpu = self.Get_Cpu_Model(item_link_root)

        # Battery 
        item_battery_time = self.Get_Battery_Time(item_link_root)

        # Resolution
        item_resolution = self.Get_Screen_Resolution(item_link_root)

        # geekbench points getting from 4 pages and get avarage number
        item_points_single , item_points_multi = self.Get_Geekbench_Points(browser, item_cpu, 4)

        # add to buffer
        self.mysql_data.append("INSERT INTO laptops VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % (item_title, item_desc, item_link, item_price, item_price_old, item_image, item_cpu, item_battery_time, item_resolution, item_points_single, item_points_multi))

    # get text content
    def Get_Content(self, item):
            # desc
            try:
                return item.contents[0]
            except:
                return ""
    
    # get image src
    def Get_Image_Src(self, item):
            # desc
            try:
                return item['src']
            except:
                return ""

    # Load geekbench points
    def Get_Geekbench_Points(self, browser, cpu_model, pages = 1):

        try:
            return self.cpu_library_single[cpu_model],self.cpu_library_multi[cpu_model]
        except:

            # varible for results
            single = 0
            multi = 0

            # main loop
            for page in range(pages):

                # link root
                root = lib_bs4.Selector_Serch(browser.Fast_Load("https://browser.geekbench.com/v5/cpu/search?page=%d&q=%s" % (page + 1,cpu_model)))

                # search list items
                list_items = root.Search_Tags("div","col-12 list-col")

                #loop for processing data
                for item in list_items:

                    # item root
                    item_root = lib_bs4.Selector_Serch(item, True)

                    # add to result
                    search_result = item_root.Search_Tags("span","list-col-text-score")

                    # logick
                    if int(self.Get_Content(search_result[0])) > single:
                        single = int(self.Get_Content(search_result[0]))
                    
                    if int(self.Get_Content(search_result[1])) > multi:
                        multi = int(self.Get_Content(search_result[1]))

                # add to main
                single = 0 if len(list_items) < 0 else single
                multi = 0 if len(list_items) < 0 else multi
                
            # add to library
            self.cpu_library_single[cpu_model] = single
            self.cpu_library_multi[cpu_model] = multi
            
            # return result
            return self.cpu_library_single[cpu_model],self.cpu_library_multi[cpu_model]
    
    # Getting CPU model
    def Get_Cpu_Model(self, item_link_root):

        # result (CPU model)
        result = ""

        # cpu model (get list with properties)
        item_cpu_root_list = item_link_root.Search_Tags("div", "_2-yxmKbU7A _1wAkY2JWCe VKqGJ23WgZ")

        # check all properties search CPU model
        for cpu_item in item_cpu_root_list:

            # bs init
            cpu_item_root = lib_bs4.Selector_Serch(cpu_item, True)

            # property name
            name = self.Get_Content(cpu_item_root.Search_One_Tag("span", "_11CuNfeGpE"))

            # value
            value = self.Get_Content(cpu_item_root.Search_One_Tag("div", "_3K8xflTCMj _2-DdMjlREV"))

            # logick
            if name == "Processor-serie":
                result += "%s " % value
                continue

            if name == "Processor-model":
                result += value
                break;
        
        # result
        return result
        # Getting CPU model

    def Get_Battery_Time(self, item_link_root):

        # result (time of life)
        result = "0"

        # battery time (get list with properties)
        item_cpu_root_list = item_link_root.Search_Tags("div", "_2-yxmKbU7A _1wAkY2JWCe VKqGJ23WgZ")

        # check all properties search battery time
        for cpu_item in item_cpu_root_list:

            # bs init
            cpu_item_root = lib_bs4.Selector_Serch(cpu_item, True)

            # property name
            name = self.Get_Content(cpu_item_root.Search_One_Tag("span", "_11CuNfeGpE"))

            # value
            value = self.Get_Content(cpu_item_root.Search_One_Tag("div", "_3K8xflTCMj _2-DdMjlREV"))

            # logick

            if name == "Batteritid":
                result += value
                break;
        
        # result
        return float(result.split(" ")[0])
    
    def Get_Screen_Resolution(self, item_link_root):

        # result (resolution)
        result = ""

        # resolution (get list with properties)
        item_cpu_root_list = item_link_root.Search_Tags("div", "_2-yxmKbU7A _1wAkY2JWCe VKqGJ23WgZ")

        # check all properties search resolution
        for cpu_item in item_cpu_root_list:

            # bs init
            cpu_item_root = lib_bs4.Selector_Serch(cpu_item, True)

            # property name
            name = self.Get_Content(cpu_item_root.Search_One_Tag("span", "_11CuNfeGpE"))

            # value
            value = self.Get_Content(cpu_item_root.Search_One_Tag("div", "_3K8xflTCMj _2-DdMjlREV"))

            # logick

            if name == "Skærmopløsning":
                result += value
                break;
        
        # result
        return result





