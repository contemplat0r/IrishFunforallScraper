# -*- coding: utf8 -*- 

from lxml import etree
from StringIO import StringIO
import requests
import pickle
import codecs
import json
import os
import re
import csv
import time
import multiprocessing
from utility import get_html, img_download, site_subdir_creator

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

root_site_url = 'http://www.menupages.ie/'
site_layers_description_list = list()
user_agent_header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0'}
parser = etree.HTMLParser()
#img_dir = 'download/menupages/img'
img_dir = 'menupages'
processes_num = 8

except_log_file = None

def create_dirs(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as e:
            print 'Error: ', e

def space_drop(string):
    result = ''
    for s in string:
        if not s.isspace():
            result = result + s
    return

def save_html(html, filename):
    success = True
    f = codecs.open(filename, 'w', encoding='utf-8')
    f.write(html)
    f.close()
    return success

def get_saved_html(filename):
    f = codecs.open(filename, 'r', encoding='utf-8')
    #f = open(filename, 'r')
    html = f.read()
    f.close()
    ## print html
    return html

def save_data(data, filename):
    out = open(filename, 'w')
    pickle.dump(data, out)
    out.close()

def get_saved_data(filename):
    saved_data = None
    if os.stat(filename)[6] > 0:
        finput = open(filename, 'r')
        saved_data = pickle.load(finput)
        finput.close()
    return saved_data


def first_layer_processor(layer_description, exceptions_log_file):
    next_layer_url_list = list()
    for url in layer_description['url_list']:
        html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html), parser)

        info_container = tree.xpath(layer_description['info_container_xpath'])
        info_items = info_container[0].xpath(layer_description['info_tag_xpath'])
        for info_item in info_items:
           next_layer_url_list.append(info_item.attrib['href'])
    print 'From first layer processor: next_url_list length %s, next_url_list %s' % (len(next_layer_url_list), next_layer_url_list)
    return next_layer_url_list

site_layers_description_list.append(
    {
        'url_list' : ['http://www.menupages.ie/'],
        'info_container_xpath' : '//body[@class="f_col_3"]/div[@class="container"]/div[@class="content"]/div[@class="col_1"]/div[@id="home_tabs"]/div[@class="tab-content"]/div[@id="search_tab"]/div[@class="content_tab"]/div[@class="ireland_map"]/ul[@id="national-map"]',
        'info_tag_xpath' : 'li/a',
        'process_this_layer_func' : first_layer_processor
    }
)


def second_layer_processor(layer_description, exceptions_log_file):
    next_layer_url_list = list()
    for url in layer_description['url_list']:
        info_items = list()
        html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
        tree = etree.parse(StringIO(html), parser)
        info_container = tree.xpath(layer_description['info_container_all_xpath'])
        if info_container != []:
            info_items = info_container[0].xpath(layer_description['info_tag_xpath'])
        else:
            info_container = tree.xpath(layer_description['info_container_xpath'])
            if info_container != []:
                info_items = info_container[0].xpath(layer_description['info_tag_xpath'])
        if info_items != []:
            for info_item in info_items:
                next_layer_url_list.append(info_item.attrib['href'])
    print 'From second layer processor: next_url_list length %s' % len(next_layer_url_list)
    for url in next_layer_url_list:
        print url
    return next_layer_url_list

site_layers_description_list.append(
    {
        'url_list' : [],
        'info_container_xpath' : '//body[@class="f_col_3"]/div[@class="container"]/div[@class="content"]/div[@class="col_1"]/div[@id="home_tabs"]/div[@class="tab-content"]/div[@id="search_tab"]/div[@id="main_map"]/div[@class="ireland_county"]/ul',
        'info_container_all_xpath' : '//body[@class="f_col_3"]/div[@class="container"]/div[@class="content"]/div[@class="col_1"]/div[@id="home_tabs"]/div[@class="tab-content"]/div[@id="search_tab"]/div[@id="all_areas"]/div[@class="ireland_county"]/ul',
        'info_tag_xpath' : 'li/a',
        'process_this_layer_func' : second_layer_processor
    }
)


def third_layer_processor(layer_description, exceptions_log_file):
    next_layer_url_list = list()
    i = 0
    for url in layer_description['url_list']:
        print 'Third layer outer cycle iteration: %s' % str(i)
        i = i + 1
        current_page_url = url
        j = 0
        is_next_button = True
        while is_next_button:
            print 'Third layer inner cycle iteration: %s' % str(j)
            j = j + 1
            print 'Current page url: ' + current_page_url
            html = get_html(current_page_url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
            print 'Third layer html', html
            tree = etree.parse(StringIO(html), parser)
            info_container = tree.xpath(layer_description['info_container_xpath'])
            info_items = info_container[0].xpath(layer_description['info_tag_xpath'])
            for info_item in info_items:
                next_layer_url_list.append(info_item.attrib['href'])
                print info_item.attrib['href']
            print 'Third layer, next layer url list len: %s' % str(len(next_layer_url_list))
            next_page_item = info_container[0].xpath(layer_description['next_button_xpath'])
            if next_page_item != []:
                print 'Next page item list not empty'
                print 'Next page button id ' + next_page_item[0].attrib['id']
                if next_page_item[0].attrib['id'] == 'ctl00_cphMain_btnNext':
                    is_next_button = True
                    current_page_url = next_page_item[0].attrib['href']
                    print 'Next button url:' + current_page_url
                else:
                    print 'None next button'
                    is_next_button = False
            else:
                is_next_button = False
                print 'Next page item list empty'
    return next_layer_url_list

site_layers_description_list.append(
    {
        'url_list' : [],
        'info_container_xpath' : '//body[@class="f_col_2"]/div[@class="container"]/div[@class="content"]/div[@class="col_1"]/div[@class="row listing"]',
        'info_tag_xpath' : 'div[@class="media low_det"]/div[@class="media-body"]/div[@class="details_group"]/h4[@class="media-heading"]/a',
        'next_button_xpath' : 'div[@class="pagination"]/ul/li/a',
        'process_this_layer_func' : third_layer_processor
    }
)

def fourth_layer_media_processor(url, img_xpath, venue_id, exceptions_log_file):
    media_url = '%s/media' % url
    html = get_html(media_url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
    tree = etree.parse(StringIO(html), parser)
    img_container = tree.xpath(img_xpath)
    img_url_list = [img_tag.attrib['src'] for img_tag in img_container]
    img_num = 0
    for img_url in img_url_list:
        img_file_name = '%s_%s' % (str(venue_id), str(img_num))
        img_num = img_num + 1
        img_download(img_url, img_file_name, img_dir, exceptions_log_file)
    return img_url_list

def fourth_layer_location_processor(url, jscript_xpaths, exceptions_log_file):
    location_coordinates = list()
    coordinates_str_marker = 'LatLng('
    marker_len = len(coordinates_str_marker)
    coordinates_str_end_marker = ')'
    location_url = '%s/location/' % url
    html = get_html(location_url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
    tree = etree.parse(StringIO(html), parser)
    jscript_container = tree.xpath(jscript_xpaths)
    jscript_texts = [jscript.text for jscript in jscript_container]
    
    if len(jscript_texts) == 2:
        coordinates_jscript_text = jscript_texts[1]
        coordinates_substr_begin = coordinates_jscript_text.find(coordinates_str_marker)
        if coordinates_substr_begin != -1:
            coordinates_jscript_text = coordinates_jscript_text[coordinates_substr_begin + marker_len:]
            coordinates_substr_end = coordinates_jscript_text.find(coordinates_str_end_marker)
            if coordinates_substr_end != -1:
                location_coordinates = coordinates_jscript_text[:coordinates_substr_end].split(',')
    return location_coordinates


#def fourth_layer_data_slice_processor(layer_description, venue_list, urls_list_slice, start_venue_id, exceptions_log_file):
def fourth_layer_data_slice_processor(args):
    layer_description, urls_list_slice, start_venue_id, exceptions_log_file = args
    venue_list = list()
    venue_id = start_venue_id
    for url in urls_list_slice:
        venue_description = dict()
        venue_description['id'] = venue_id
        
        info_items = list()
        html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)

        tree = etree.parse(StringIO(html), parser)
        info_container = tree.xpath(layer_description['info_container_xpath'])
        if info_container != []:
            contacts_items = info_container[0].xpath(layer_description['contacts_info_xpath'])
            contact_item = contacts_items[0]
            print contact_item.attrib['href']

            name_container = tree.xpath(layer_description['data_venue_name_xpath'])
            print name_container[0].text
            venue_description['name'] = name_container[0].text
            venue_description['category'] = 'food'
            data_items = info_container[0].xpath(layer_description['data_xpath'])
            for item in data_items:
                data_keyword_list = item.xpath(layer_description['data_keyword_xpath'])
                if data_keyword_list != []:
                    if data_keyword_list[0].text == 'CUISINES':
                        data_text_list = item.xpath(layer_description['data_text_xpath'])
                        print data_keyword_list[0].text
                        print data_text_list[0].tail
                        venue_description['cuisines'] = data_text_list[0].tail.strip().encode('utf-8').replace('\n', ' ')
                        cuisines_list = venue_description['cuisines'].split(',') 
                        venue_description['cuisines_main'] = cuisines_list[0]
                        venue_description['cuisines_rest'] = cuisines_list[1:]
                    if data_keyword_list[0].text == 'WEBSITE':
                        web_text_list = item.xpath(layer_description['data_web_xpath'])
                        print data_keyword_list[0].text
                        print web_text_list[0].attrib['href']
                        venue_description['website'] = web_text_list[0].attrib['href']
            
            contacts_page_xpaths = layer_description['contacts_page_xpaths']
            contacts_page_html = get_html(root_site_url + contact_item.attrib['href'], user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
            contacts_page_tree = etree.parse(StringIO(contacts_page_html), parser)
            contacts_page_info_container_list = contacts_page_tree.xpath(contacts_page_xpaths['info_container_xpath'])

            if contacts_page_info_container_list != []:
                contacts_page_info_subcontainers_list = contacts_page_info_container_list[0].xpath(contacts_page_xpaths['info_subcontainer_xpath'])
                for subcontainer in contacts_page_info_subcontainers_list:
                    subcontainer_name = subcontainer.xpath(contacts_page_xpaths['subcontainer_name_xpath'])[0].text
                    subcontainer_data = subcontainer.xpath(contacts_page_xpaths['subcontainer_data_xpath'])[0].text
                    if subcontainer_name == 'Address':
                        print 'Address: ', subcontainer_data
                        venue_description['address'] = subcontainer_data
                        venue_description['address_components'] = subcontainer_data.split(', ')
                        for address_component in venue_description['address_components']:
                            print address_component
                    if subcontainer_name == 'Telephone':
                        print 'Phone: ', subcontainer_data
                        venue_description['phone'] = subcontainer_data
            media_url_list = fourth_layer_media_processor(url, layer_description['img_xpath'], venue_id, exceptions_log_file)
            venue_description['media_url_list'] = media_url_list
            for media_url in venue_description['media_url_list']:
                print media_url
            venue_advert_text_container = tree.xpath(layer_description['venue_advert_text_xpath'])
            if venue_advert_text_container != []:
                venue_description['venue_advert_text'] = venue_advert_text_container[0].text
                print venue_description['venue_advert_text']
            location_coordinates = fourth_layer_location_processor(url, layer_description['location_xpath'], exceptions_log_file)
            venue_description['location_coordinates'] = location_coordinates
            print location_coordinates
            venue_list.append(venue_description)
            if len(venue_list) != 0:
                print venue_list[-1]
            else:
                print 'venue_list empty'
        else:
            print 'Fourth layer info container is empty list', 'url: ' + url
        venue_id = venue_id + 1
    return venue_list

def fourth_layer_processor(layer_description, exceptions_log_file):
    pool = multiprocessing.Pool(processes_num)
    venues_list = list()
    urls_list = layer_description['url_list']
    urls_list_len = len(urls_list)
    urls_list_slice_len = urls_list_len / processes_num
    jobs = []
    arg_list = list()
    for slice_num in range(0, processes_num - 1):
        arg_list.append((layer_description, urls_list[slice_num * urls_list_slice_len : (slice_num + 1) * urls_list_slice_len], slice_num * urls_list_slice_len, exceptions_log_file))
    
    arg_list.append((layer_description, urls_list[(processes_num - 1) * urls_list_slice_len :], (processes_num - 1) * urls_list_slice_len, exceptions_log_file))
    result_list = pool.map(fourth_layer_data_slice_processor, arg_list)
    for result_item in result_list:
        venues_list.extend(result_item)

    return venues_list

site_layers_description_list.append(
    {
        'url_list' : [],
        'info_container_xpath' : '//body[@class="f_col_2"]/div[@class="container"]/div[@class="content"]/div[@class="col_1"]/div[@class="row"]/div[@class="col_inner_2"]',
        'contacts_info_xpath' : 'p/a[@class="btn-phone email_show"]',
        'data_xpath' : 'div[@class="block border"]/p',
        'data_keyword_xpath' : 'strong',
        'data_text_xpath' : 'br',
        'data_web_xpath' : 'a',
        #'data_venue_name_xpath' : '//body[@class="f_col_2"]/div[@class="container"]/div[@class="content"]/div[@class="col_1"]/div[@class="row title_restaurant"]/div[@class="rest_name col_inner_1"]/h1',
        #'data_venue_name_xpath' : '//body/div/div/div/div/div/address/p/span',
        'data_venue_name_xpath' : '//body/div/div/div/div/div/h1/span',
        'contacts_page_xpaths' :
        {
            'info_container_xpath' : '//body/div[@class="form_email"]',
            'info_subcontainer_xpath' : 'div[@class="control-group"]',
            'subcontainer_name_xpath' : 'label[@class="control-label"]',
            'subcontainer_data_xpath' : 'p',
        },
        'img_xpath' : '//div[@id="container"]/div[@id="example"]/div[@id="slides"]/div[@class="slides_container"]/img',
        'location_xpath' : '//body[@class="f_col_2"]/div[@class="container"]/div[@class="content"]/div[@class="col_1"]/script[@type="text/javascript"]',
        'venue_advert_text_xpath' : '/html/body[@class="f_col_2"]/div[@class="container"]/div[@class="content"]/div[@class="col_1"]/div[@class="row"]/div[@class="col_inner_1"]/div[@class="descrition"]/span[@class="read_more"]',
        'process_this_layer_func' : fourth_layer_processor
    }
)


def process_site_layers(layers_description_list, exceptions_log_file):
    if len(layers_description_list) > 1:
        current_layer_description = layers_description_list.pop(0)
        next_layer_url_list = current_layer_description['process_this_layer_func'](current_layer_description, exceptions_log_file)
        layers_description_list[0]['url_list'] = next_layer_url_list
        return process_site_layers(layers_description_list, exceptions_log_file)
    elif len(layers_description_list) == 1:
        current_layer_description = layers_description_list.pop(0)
        return current_layer_description['process_this_layer_func'](current_layer_description, exceptions_log_file)


def clear_phone_number(phonenumber):
    return phonenumber.replace(' ', '').replace('(', '').replace(')', '')

def to_csv(menupages_data):
    with codecs.open('menupages.csv', 'w') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Name', 'Address', 'Phone', 'Web', 'Cuisines main', 'Cuisines rest', 'Advert text', 'Location coordinates', 'Images id'])
        for item in menupages_data:
            if item['name'] != None:
                name = item['name'].strip().encode('utf-8')
            else:
                name = 'None'
            address_str = ''
            #raw_address_str = item.get('address')
            raw_address_str = item['address']
            '''
            if raw_address_str != None:
                address_parts = raw_address_str.split(' ')

                for address_part in address_parts:
                    if address_part != '':
                        address_str = address_str + address_part + ' '
                address_str = address_str.replace('\n', ' ').replace('  ', ' ').strip().encode('utf-8')
                '''
            address_parts = raw_address_str.split(' ')

            for address_part in address_parts:
                if address_part != '':
                    address_str = address_str + address_part + ' '
            address_str = address_str.replace('\n', ' ').replace('  ', ' ').strip().encode('utf-8')

            #print address_str
            
            telephone = ''
            if item['phone'] != None:
                telephone = item['phone'].strip().encode('utf-8')
            site = item['website'].strip().encode('utf-8')
            cuisines_main = item.get('cuisines_main')
            if cuisines_main == None:
                cuisines_main = ''
            cuisines_rest_str = ''
            cuisines_rest = item.get('cuisines_rest')
            if cuisines_rest != None:
                for cuisine in cuisines_rest:
                    cuisines_rest_str = cuisines_rest_str + cuisine
            print cuisines_main
            cuisines_rest_str = cuisines_rest_str.strip()
            print cuisines_rest_str, '\n'*2
            advert_text = item.get('venue_advert_text')
            if advert_text == None:
                advert_text = '';
            print advert_text
            advert_text = advert_text.encode('utf-8')
            location_str = '(0, 0)'
            location = item.get('location_coordinates')
            #print location
            if location != None and location != [] and len(location) == 2:
                location_str = '(%s, %s)' % (location[0], location[1])
            print location_str
            img_id = item.get('id')
            if img_id == None:
                img_id = ''
            print img_id
            row = [name, address_str, telephone, site, cuisines_main, cuisines_rest_str, advert_text, location_str, img_id]
            writer.writerow(row)

def do_scrape(download_dir='download', download_processes_num=8, except_log_file_name='request_exceptions_menupages.log'):
    global img_dir
    global processes_num
    processes_num = download_processes_num
    img_dir = site_subdir_creator(img_dir)(download_dir)
    except_log_file = open(except_log_file_name, 'w')
    start_time = time.time()
    menupages_data =  process_site_layers(site_layers_description_list, except_log_file)
    except_log_file.close()
    print 'menupages.ie scrapping time: ', str(time.time() - start_time)
    save_data(menupages_data, 'menupages.dat')
    menupages_data = get_saved_data('menupages.dat')
    to_csv(menupages_data)


if __name__ == '__main__':
    
    create_dirs(img_dir)
    
    except_log_file = open('menupages_exceptions.log', 'w')
    start_time = time.time()
    venues =  process_site_layers(site_layers_description_list, except_log_file)
    print 'menupages.ie scrapping time: ', str(time.time() - start_time)
    except_log_file.close()

    menupages_data = get_saved_data('menupages.dat')
    to_csv(menupages_data)
    print len(menupages_data)
