#
# Class for build new index page
#

# libs
import json, multiprocessing, time, dryscrape, psutil
import core.lib_bs4 as lib_bs4
from core.lib_request import Browser
import core.mysql as mysql

# main class page
class Page:

    # constructor
    def __init__(self, link:str) -> None:

        # init x server session
        dryscrape.start_xvfb()

        # link
        self.link = link

        # init mysql connection
        self.mysql = mysql.Mysql_Connect("192.168.111.37", "root", "dbnmjr031193", "flask_test")

        # variable for define pages (1000 per 1 page)
        json_page = 0

        # items array for processing
        self.items = []

        # Selecting all items
        while True:

            # process link
            self.Url_Processing(link, json_page * 1000)

            # load page and decoding json
            self.json_data = json.loads(Browser(self.link, True).data)

            # check for page is available
            if int(self.json_data['totalHits']) - json_page * 1000 < 0:
                break

            # Pring page number
            print("Page nr. %d" % (json_page + 1))

            # # add items to array
            self.items += self.json_data['products']

            # # next page
            json_page += 1           

        # create items
        self.Search_All_Items()

    # function for string processing (create link to request and get json)
    def Url_Processing(self, link, offset = 0):
        # get attributes from current link
        old_link_attributs = link.split("?")[1].split("&")
        # new link base
        new_link = "https://www.pricerunner.dk/public/search/category/products/v2/dk/27?size=1000&offset=%d" % offset

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
    def Send_To_Db(self, data_dict):
        # delete all old data from mysql database
        self.mysql.I("DELETE FROM laptops")

        # write all records to db
        for key in data_dict:
            self.mysql.I(data_dict[key])

        
    # search all items and create new list
    def Search_All_Items(self):
        # create multiprocessing manages
        manager = multiprocessing.Manager()

        # threads
        threads = []
        max_threads = 1

        # data storages
        data_buffer = manager.dict()
        cpu_buffer_single = manager.dict()
        cpu_buffer_multy = manager.dict()

        # element number for log
        item_number = 1
        
        # loop for create one item
        for item in self.items:

            # create and start task
            task = multiprocessing.Process(target=self.Make_Json_List_Item,args=(item,item_number,data_buffer, cpu_buffer_single, cpu_buffer_multy,))
            task.start()

            # show load log
            print("Loading... %d from %d. Amount of threads is %d." % (item_number,len(self.items), max_threads))
            
            # add task to quene
            threads.append(task)

            # increment number of task
            item_number += 1

            # check all tasks and delete if is ready
            while len(threads) >= max_threads:

                # delete task from quene
                for task in threads:
                    if (task.is_alive() == False):
                        threads.remove(task)
                
                # getting info about cpu usage and wait
                cpu_usage = psutil.cpu_percent(2)

                # check for ram and cpu usage
                if psutil.virtual_memory()[2] < 65 and cpu_usage < 90:
                    print("Quene incrementing. Quene size %s. CPU usage %f. Ram usage %f" % (max_threads, cpu_usage, psutil.virtual_memory()[2]))
                    max_threads += 1
                
                elif max_threads != 0 and psutil.virtual_memory()[2] > 85 or max_threads != 0 and cpu_usage > 99:
                    print("Quene decrementing. Quene size %s. CPU usage %f. Ram usage %f" % (max_threads, cpu_usage, psutil.virtual_memory()[2]))
                    max_threads -= 1

        # wait for threads
        while len(threads) > 0:

            # delete task from quene
            for task in threads:
                if (task.is_alive() == False):
                    threads.remove(task)
                    print("Task in quene %d" % len(threads))
            
            # wait
            time.sleep(1)

        # update data in db
        self.Send_To_Db(data_buffer)

    # make JSON list item
    def Make_Json_List_Item(self, item, number, data_buffer, cpu_buffer_single, cpu_buffer_multy):
        
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
        item_link_root = lib_bs4.Selector_Serch(Browser(item_link).data)

        # CPU
        item_cpu = self.Get_Cpu_Model(item_link_root)

        # Battery 
        item_battery_time = self.Get_Battery_Time(item_link_root)

        # Resolution
        item_resolution = self.Get_Screen_Resolution(item_link_root)

        # geekbench points getting from 4 pages and get avarage number
        item_points_single , item_points_multi = self.Get_Geekbench_Points(cpu_buffer_single, cpu_buffer_multy, item_cpu, 4)

        # add data to shared array
        data_buffer[number] = ("INSERT INTO laptops VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % (item_title, item_desc, item_link, item_price, item_price_old, item_image, item_cpu, item_battery_time, item_resolution, item_points_single, item_points_multi))

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
    def Get_Geekbench_Points(self, cpu_buffer_single, cpu_buffer_multy, cpu_model, pages = 1):

        try:
            return cpu_buffer_single[cpu_model],cpu_buffer_multy[cpu_model]
        except:

            # varible for results
            single = 0
            multi = 0

            # main loop
            for page in range(pages):

                # link root
                root = lib_bs4.Selector_Serch(Browser("https://browser.geekbench.com/v5/cpu/search?page=%d&q=%s" % (page + 1,cpu_model),True).data)

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
            cpu_buffer_single[cpu_model] = single
            cpu_buffer_multy[cpu_model] = multi
            
            # return result
            return cpu_buffer_single[cpu_model],cpu_buffer_multy[cpu_model]
    
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





