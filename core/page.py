#
# Class for build new index page
#

# libs
import os, json
from time import sleep
import core.lib_bs4 as lib_bs4
import core.lib_request as lib_request
import core.mysql as mysql


class Page:

    # constructor
    def __init__(self, file_name:str, link:str, tag:str, item_class:str, is_json:bool = False, link_processing = True) -> None:
        # file name
        self.file_name = file_name

        # link
        self.link = link

        # tag name from list
        self.tag = tag

        # class name from list
        self.item_class = item_class

        # variable json
        self.is_json = is_json

        # init page browser
        self.browser = lib_request.Browser(True)

        # init mysql connection
        self.mysql = mysql.Mysql_Connect("server", "root", "dbnmjr031193", "pricerunner")

        # cpu library (optimization)
        self.cpu_library_single = {}
        self.cpu_library_multi = {}

        # Load JSON data
        if is_json:

            # process link
            if link_processing:
                self.Url_Processing(link)

            # load page and decoding json
            self.json_data = json.loads(self.browser.Load(self.link))

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
            
    # write to file
    def To_File(self, data_to_file, dest_file = ""):
        if dest_file:
            self.file = open(dest_file, "a")
            self.file.write(data_to_file)
            self.file.close()
        else:
            self.file = open(self.file_name, "a")
            self.file.write(data_to_file)
            self.file.close()
    
    

    # search all items and create new list
    def Search_All_Items(self):

        # rename old file if exist
        if os.path.exists(self.file_name):
            os.rename(self.file_name,self.file_name + ".old.html")

        # create browser session
        browser = lib_request.Browser()

        # delete all old data from mysql database
        self.mysql.I("delete from laptops")

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
        item_points_one = self.Get_Geekbench_Points(browser, item_cpu, 1)
        item_points_two = self.Get_Geekbench_Points(browser, item_cpu,2)
        item_points_three = self.Get_Geekbench_Points(browser, item_cpu,3)
        item_points_four = self.Get_Geekbench_Points(browser, item_cpu,4)

        # results
        item_points_single = (item_points_one[0] + item_points_two[0] + item_points_three[0] + item_points_four[0]) / 4
        item_points_multi = (item_points_one[1] + item_points_two[1] + item_points_three[1] + item_points_four[0]) / 4

        # image
        item_img =  self.Get_Image_Src(item_root.Search_One_Tag("img", "_1eCHgH5-ru css-1shbqcj"))

        # old price
        item_old_price = self.Get_Content(item_root.Search_One_Tag("span", "_1hXG0xPrK5 _3GiEsJk2wF _3JJc-cEjsi yNAlNXLNAJ css-2tmqko"))

        # new price
        item_new_price = self.Get_Content(item_link_root.Search_One_Tag("span", "_1j6NocjLHg _1hXG0xPrK5 _3GiEsJk2wF _3JJc-cEjsi css-2tmqko"))

        # write to file
        # html
        # self.To_File("<div><a href='%s'><h3>%s</h3><img width=300 src='%s'><p>%s</p><p>CPU - %s</p><p>GeekBench3 single - %d</p><p>GeekBench3 multi - %d</p><p>Battery time %s</p><p>Resolution %s</p><p>Old Price %s</p><p>New price %s kr.</p><p>Price power raiting index (less better) %.2f points.</p></div>\n" % (item_link, item_title, item_img ,item_desc,item_cpu, item_points_single, item_points_multi, item_battery_time, item_resolution, item_old_price, item_new_price, int(item_new_price) / item_points_multi ))
        #csv
        # self.To_File("table.csv", "%s,%s,%s,%s,%s,%s\n" % (item_title, item_desc, item_cpu, item_old_price, item_new_price, item_link))
    
    # make JSON list item
    def Make_Json_List_Item(self, browser, item):

        # getting info
        item_title = item['name']
        item_desc = item['description']
        item_link = "https://www.pricerunner.dk" + item['url']
        item_price = item['lowestPrice']['amount']
        item_image ="https://www.pricerunner.dk" + item['image']['path']

        # open link and parse data
        item_link_root = lib_bs4.Selector_Serch(browser.Load(item_link))

        # CPU
        item_cpu = self.Get_Cpu_Model(item_link_root)

        # Battery 
        item_battery_time = self.Get_Battery_Time(item_link_root)

        # Resolution
        item_resolution = self.Get_Screen_Resolution(item_link_root)

        # geekbench points getting from 4 pages and get avarage number
        item_points_one = self.Get_Geekbench_Points(browser,item_cpu,1)
        item_points_two = self.Get_Geekbench_Points(browser,item_cpu,2)
        item_points_three = self.Get_Geekbench_Points(browser,item_cpu,3)
        item_points_four = self.Get_Geekbench_Points(browser,item_cpu,4)

        # results
        item_points_single = (item_points_one[0] + item_points_two[0] + item_points_three[0] + item_points_four[0]) / 4
        item_points_multi = (item_points_one[1] + item_points_two[1] + item_points_three[1] + item_points_four[0]) / 4

        # mysql request
        self.mysql.I("insert into laptops values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);" , (item_title, item_desc, item_link, item_price, item_image, item_cpu, item_battery_time, item_resolution, item_points_single, item_points_multi))
        # self.mysql.I("insert into table values ('data');")

        # write to file
        # self.To_File("<div><a href='%s'><h3>%s</h3><img width=300 src='%s'><p>%s</p><p>CPU - %s</p><p>GeekBench3 single - %d</p><p>GeekBench3 multi - %d</p><p>Battery time %s</p><p>Resolution %s</p><p>Price %s kr.</p><p>Price power raiting index (less better) %.2f points.</p></div>\n" % (item_link, item_title, item_image ,item_desc,item_cpu, item_points_single, item_points_multi, item_battery_time, item_resolution, item_price, float(item_price) / item_points_multi ))
        #csv
        # self.To_File("%s,'%s',%s,%s,%.2f,%.2f,%.2f,%s\n" % (item_title, item_battery_time.replace(".",","), item_cpu, item_price, item_points_single, item_points_multi,float(item_price) / item_points_multi, item_link), self.file_name + ".csv",)

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
    def Get_Geekbench_Points(self, browser, cpu_model, page = 1):

        try:
            return self.cpu_library_single[cpu_model],self.cpu_library_multi[cpu_model]
        except:

            # link root
            root = lib_bs4.Selector_Serch(browser.Load("https://browser.geekbench.com/v5/cpu/search?page=%d&q=%s" % (page,cpu_model)))

            # search list items
            list_items = root.Search_Tags("div","col-12 list-col")

            # results
            single_core = 0
            multi_core = 0

            #loop for processing data
            for item in list_items:

                # item root
                item_root = lib_bs4.Selector_Serch(item, True)

                # add to result
                single_core += int(self.Get_Content(item_root.Search_Tags("span","list-col-text-score")[0]))
                multi_core += int(self.Get_Content(item_root.Search_Tags("span","list-col-text-score")[1]))
            
            # add to library
            self.cpu_library_single[cpu_model] = single_core / len(list_items) if len(list_items) > 0 else 1
            self.cpu_library_multi[cpu_model] = multi_core / len(list_items) if len(list_items) > 0 else 1
            
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





