# -*- coding: utf8 -*- 

from lxml import etree
from StringIO import StringIO
import json
import os
import re
import csv
import time
import requests
import pickle
import codecs
import multiprocessing
from utility import get_html, img_download, site_subdir_creator
from htmlutils import get_saved_content


root_site_url = 'http://test.fundays.ie'
site_layers_description_list = list()
user_agent_header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0'}
parser = etree.HTMLParser()
#img_dir = 'download/fundays/img'
img_dir = 'fundays'
processes_num = 4

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

def get_xpath_to_root(node):
    if node != None:
        xpath_to_root = get_xpath_to_root(node.getparent())
        xpath_to_root = xpath_to_root + '/' + node.tag
        if node.items() != []:
            attribs_string = '['
            for attrib, value in node.items():
                attribs_string = attribs_string + '@%s=\"%s\" ' % (attrib, value)
            xpath_to_root = xpath_to_root + attribs_string[0:len(attribs_string) - 1] + ']'
        return xpath_to_root
    else:
        return ''

def get_description_item(description, item_name):
    item = description.get(item_name)
    if item == None:
        item = ''
    return item.strip().encode('utf-8')

def first_layer_processor(layer_description, exceptions_log_file):
    next_layer_url_dict = dict()
    for url in layer_description['items_urls_and_descriptions'].keys():
        #html = get_html(url, user_agent_header)
        html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html), parser)

        info_container = tree.xpath(layer_description['info_container_xpath'])
        #print info_container
        #print(etree.tostring(info_container[0], pretty_print=True))
        
        info_items = info_container[0].xpath(layer_description['info_tag_xpath'])
        for info_item in info_items:
            #next_layer_url_list.append(info_item.attrib['href'])
            #next_layer_url_list.append(info_item.attrib['href'])
            next_layer_url_dict[info_item.attrib['href']] = info_item.attrib['title']
        print 'From first layer processor: next_url_list length %s, next_url_list %s' % (len(next_layer_url_dict), next_layer_url_dict)
    return next_layer_url_dict

site_layers_description_list.append(
    {
        'items_urls_and_descriptions' : {'http://test.fundays.ie' : []},
        'info_container_xpath' : '//body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td/table/tr/td[@class="catlist"]/ul',
        'info_tag_xpath' : 'li/a',
        'process_this_layer_func' : first_layer_processor
    }
)

def second_layer_single_page_processor(url, info_container_xpath, info_tag_xpath, exceptions_log_file):
    print 'Entry in second_layer_single_page_processor'
    urls_list = list()
    print 'second layer single page url: ', url
    html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
    #html = get_saved_content('fundays_second_layer_requests.txt')
    #print 'second_layer_single_page_processor, html: ', html.encode('utf-8')
    tree = etree.parse(StringIO(html), parser)
    #info_container_xpath = '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/tr/td/table'
    #info_tag_xpath = 'tr/td/div/table/tr/td/a'

    info_container = tree.xpath(info_container_xpath)
    #print(etree.tostring(info_container[0], pretty_print=True))
    print 'second_layer_single_page_processor, info_container: ', info_container
    if info_container != []:
        pass
        info_items = info_container[0].xpath(info_tag_xpath)[::2]
        #info_items = info_container[0].xpath(info_tag_xpath)
        for info_item in info_items:
            print 'second_layer_single_page_processor, info_item.attrib[\'href\']: ', info_item.attrib['href']
            #urls_set.add(info_item.attrib['href'])
            urls_list.append(info_item.attrib['href'])
    print 'second_layer_single_page_processor, urls_list: ', urls_list
    return urls_list

def second_layer_processor(layer_description, exceptions_log_file):
    next_layer_url_dict = dict()
    print 'From second_layer_processor, layer_description: ', layer_description
    info_container_xpath = layer_description['info_container_xpath']
    info_tag_xpath = layer_description['info_tag_xpath']
    for category_url, category_name in layer_description['items_urls_and_descriptions'].items():
    #for category_url in layer_description['items_urls_and_descriptions']:
        url = '%s%s' % (root_site_url, category_url)
        print 'second_layer_processor, root_site_url/category_url: ', url
        #info_items_set = set() 
        #html = get_html(url, user_agent_header)
        html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
        tree = etree.parse(StringIO(html), parser)
        info_container = tree.xpath(info_container_xpath)
        #tree.write('fundays_second_layer_pretty.html', pretty_print=True)

        if info_container != []:
            print 'second_layer_processor, info_container != []'
            info_items = info_container[0].xpath(info_tag_xpath)[::2]
            for info_item in info_items:
                print 'second_layer_processor, info_item.attrib[href]: ',  info_item.attrib['href']
                #info_items_set.add(info_item.attrib['href'])
                if next_layer_url_dict.has_key(info_item.attrib['href']):
                    next_layer_url_dict[info_item.attrib['href']]['categories'].append(category_name)
                else:
                    next_layer_url_dict[info_item.attrib['href']] = {'categories' : [category_name]}
            else:
                print 'second_layer_processor, info_container == []'
            print 'second_layer_processor, next_layer_url_dict: ', next_layer_url_dict
            other_pages_list_container = info_container[0].xpath(layer_description['other_category_pages_xpath'])
            print 'second_layer_processor, other_pages_list_container: ', other_pages_list_container
            for page_container in other_pages_list_container:
                print 'second_layer_processor, page_container: ', page_container 
                if page_container.text != None and page_container.text.strip() == 'Go to Page:':
                    print 'second_layer_processor, page_container.text.strip(): ',  page_container.text.strip()
                    print 'second_layer_processor, len(page_container.getchildren())', len(page_container.getchildren())
                    next_page_index = 2
                    print 'second_layer_processor, next_page_index: ', next_page_index
                    for child in page_container.getchildren()[1:]:
                        print 'second_layer_processor, next page url: %s-%s' % (url, str(next_page_index))
                        urls_from_next_page = second_layer_single_page_processor('%s-%s' % (url, str(next_page_index)), info_container_xpath, info_tag_xpath, exceptions_log_file)
                        print 'second_layer_processor, urls_from_next_page: ', urls_from_next_page
                        for url_from_next_page in urls_from_next_page:
                            print 'second_layer_processor, url_from_next_page: ', url_from_next_page
                            if next_layer_url_dict.has_key(url_from_next_page):
                                #next_layer_url_dict[url_from_next_page].append(category_name)
                                next_layer_url_dict[url_from_next_page]['categories'].append(category_name)
                            else:
                                #next_layer_url_dict[url_from_next_page] = [category_name]
                                next_layer_url_dict[url_from_next_page] = {'categories' : [category_name]}

                        #next_layer_url_set = next_layer_url_set.union(second_layer_single_page_processor('%s-%s' % (url, str(next_page_index)), info_container_xpath, info_tag_xpath))
                        next_page_index = next_page_index + 1
        else:
            print 'info_container == []'
    return next_layer_url_dict

site_layers_description_list.append(
    {
        'items_urls_and_descriptions' : {},
        #'info_container_xpath' : '//body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/tr/td/table/tr/td/div/table[@class="Example_H"]/tr/td/a',
        #'info_container_xpath' : '//body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/tr/td/table',
        'info_container_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/tr/td/table',
        #'info_container_xpath' : '//body/div/div/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody',
        #'info_tag_xpath' : 'tr/td/div/table[@class="Example_H"]/tr/td/a',
        #'info_tag_xpath' : 'tr/td/div/table/tbody/tr/td/a/h2/cufon/canvas',
        #'info_tag_xpath' : 'tr/td/div/table/tbody/tr/td/a',
        'info_tag_xpath' : 'tr/td/div/table/tr/td/a',
        'other_category_pages_xpath' : 'tr/td/table/tr/td',
        #'other_category_pages_xpath' : 'tr/td/table/tbody/tr/td/a',
        'process_this_layer_func' : second_layer_processor
    }
)

def get_certain_parent(node, attrib_name, attrib_value):
    if node != None:
        print node
        node_keys = node.keys()
        if attrib_name in node_keys and node.attrib[attrib_name] == attrib_value:
            print 'Certain parent found'
        else:
            get_certain_parent(node.getparent(), attrib_name, attrib_value)
    else:
        return
    
def get_next_text(element):
    text = None
    next_element = element.getnext()
    if next_element != None:
        text = next_element.text
    return text

def get_next_href(element):
    href = None
    next_element = element.getnext()
    if next_element != None:
        href = next_element.attrib['href']
    return href

#def third_layer_data_slice_processor(layer_description, items_urls_and_descriptions,  urls_list_slice, start_venue_id, exceptions_log_file):
def third_layer_data_slice_processor(args):
    layer_description, items_urls_and_descriptions, urls_list_slice, start_venue_id, exceptions_log_file = args
    result_dict = dict()
    venue_id = start_venue_id
    for url_local_part in urls_list_slice:
        url = root_site_url + '/' + url_local_part
        venue_description = dict()
        venue_description['id'] = venue_id

        html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
        #html = get_saved_content('fundays_third_layer_requests.txt')
        parser = etree.HTMLParser(remove_blank_text=True, strip_cdata=False)
        tree = etree.parse(StringIO(html), parser)
        #tree.write('fundays_third_layer_pretty.html', pretty_print=True)

        info_container_list = tree.xpath(layer_description['info_container_xpath'])
        #print info_container_list
        
        #address_node = info_container_list[0].xpath('//div[@itemprop="address"]')[0]
        #print get_xpath_to_root(address_node)

        print 'info_container_list: ', info_container_list
        if info_container_list != []:
            info_container = info_container_list[0]
            address_node_container = info_container.xpath(layer_description['address_node_xpath'])
            advert_text = ''
            if address_node_container != []:
                address_node = address_node_container[0]
                #print address_node
                if address_node.tail != None:
                    advert_text = advert_text + address_node.tail + ' '
                current_advert_node = address_node.getnext()
                while(current_advert_node != None and current_advert_node.tag != 'h3'):
                    if current_advert_node.text != None:
                        advert_text = advert_text + current_advert_node.text + ' '
                    if current_advert_node.tail != None:
                        advert_text = advert_text + current_advert_node.tail + ' '
                    strong_subnode_container = current_advert_node.xpath('strong')
                    if strong_subnode_container != []:
                        for strong_subnode in strong_subnode_container:
                            if strong_subnode.text != None:
                                advert_text = advert_text + strong_subnode.text + ' '
                            if strong_subnode.tail != None:
                                advert_text = advert_text + strong_subnode.tail + ' '
                    current_advert_node = current_advert_node.getnext()

                #print advert_text

                venue_description['advert_text'] = advert_text
                        
            contacts_header_list = info_container.xpath(layer_description['contacts_header_xpath'])
            for contacts_header in contacts_header_list:
                if 'Contact' in contacts_header.text:
                    #print contacts_header.text[len('Contact') + 1:]
                    venue_description['name'] = contacts_header.text[len('Contact') + 1:]
            phone_container = info_container.xpath(layer_description['phone_xpath'])
            if phone_container != []:
                phone = phone_container[0].text
                #print phone
                venue_description['phone'] = phone
            info_header_tags = info_container.xpath(layer_description['info_header_tag_xpath'])
            for info_header_tag in info_header_tags:
                header_text = info_header_tag.text.strip()
                if header_text == 'International:':
                    international_phone = info_header_tag.tail.strip()
                    #print international_phone
                    venue_description['international_phone'] = international_phone
                if header_text == 'Email:':
                    email = get_next_text(info_header_tag)
                    #print email
                    venue_description['email'] = email
                if header_text == 'Website:':
                    site = get_next_href(info_header_tag)
                    #print site
                    venue_description['site'] = site
                if header_text == 'Location Map:':
                    location_link = get_next_href(info_header_tag)
                    if location_link != None:
                        location_coordinates = location_link[location_link.find('=') + 1:].split(',')
                        #print location_coordinates
                        venue_description['location_coordinates'] = location_coordinates
            region_container = info_container.xpath(layer_description['region_address_xpath'])
            if region_container != []:
                venue_description['region'] = ''
                if region_container[0].text != None:
                    region = region_container[0].text.strip()
                    venue_description['region'] = region
                    #print region
            street_address_container = info_container.xpath(layer_description['street_address_xpath'])
            if street_address_container != []:
                street_address = ''
                if street_address_container[0].text != None:
                    street_address = street_address_container[0].text.strip()
                    #print street_address
                    venue_description['street_address'] = street_address

        list_detail_container = tree.xpath(layer_description['list_detail_xpath'])

        img_container_list = tree.xpath(layer_description['img_xpath'])
        print 'img_container_list: ', img_container_list
        img_num = 0
        img_list = list()
        for img_container in img_container_list:
            print 'img_container: ', img_container
            if img_container != None:
                img_url = img_container.attrib.get('src')
                #print img_url
                if img_url != None and img_url != '':
                    img_list.append(img_url)
                    img_file_name = '%s_%s' % (str(venue_id), str(img_num))
                    img_num = img_num + 1
                    img_download(root_site_url + img_url, img_file_name, img_dir, exceptions_log_file)
        venue_description['img_urls'] = img_list
        #items_urls_and_descriptions[url_local_part]['description'] = venue_description

        categories = items_urls_and_descriptions[url_local_part]['categories']
        #categories = {}

        #items_urls_and_descriptions[url_local_part].update({'description' : venue_description})
        #items_urls_and_descriptions[url_local_part] = {'categories' : categories, 'description' : venue_description}
        result_dict[url_local_part] = {'categories' : categories, 'description' : venue_description}
        #print venue_description
        venue_id = venue_id + 1
        print start_venue_id
        print result_dict[url_local_part]
    #return items_urls_and_descriptions
    #queue.put(result_dict)
    return result_dict

def third_layer_processor(layer_description, exceptions_log_file):
    result_dict = dict()
    pool = multiprocessing.Pool(processes_num)
    items_urls_and_descriptions = layer_description['items_urls_and_descriptions']
    urls_list = items_urls_and_descriptions.keys()
    urls_list_len = len(urls_list)
    urls_list_slice_len = urls_list_len / processes_num
    jobs = []
    arg_list = list()
    for slice_num in range(0, processes_num - 1):
        arg_list.append((layer_description, items_urls_and_descriptions, urls_list[slice_num * urls_list_slice_len : (slice_num + 1) * urls_list_slice_len], slice_num * urls_list_slice_len, exceptions_log_file))
    
    arg_list.append((layer_description, items_urls_and_descriptions, urls_list[(processes_num - 1) * urls_list_slice_len :], (processes_num - 1) * urls_list_slice_len, exceptions_log_file))
    result_list = pool.map(third_layer_data_slice_processor, arg_list)
    for result_item in result_list:
        result_dict.update(result_item)
    #pool.close()
    #pool.join()
    return result_dict


site_layers_description_list.append(
    {
        'items_urls_and_descriptions' : {},
        #'info_container_xpath' : '//body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]',
        #'info_container_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/table/tr/td/table/tr/td/div/h3',
        #'info_container_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/table/tr/td/table/tr/td/div',
        'info_container_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/div[@class="details"]/table/tr/td/table/tr/td/div',
        'list_detail_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]',
        #'img_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/table/tr/td/table/tr/td/div/table/tr/td/img',
        'img_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/div[@class="details"]/table/tr/td/table/tr/td/div/table/tr/td/img[@class="watermark"]',
        'address_node_xpath' : '/html/body/div/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td[@valign="top"]/table/tr/td/table/tr/td/div/div[@itemprop="address"]',
        'contacts_header_xpath' : 'h3',
        'phone_xpath' : 'span[@itemprop="telephone"]',
        'info_header_tag_xpath' : 'b',
        'location_coordinates_xpath' : '',
        'region_address_xpath' : 'span[@itemprop="addressRegion"]',
        'street_address_xpath' : 'span[@itemprop="streetAddress"]',
        'process_this_layer_func' : third_layer_processor
    }
)


def process_site_layers(layers_description_list, except_log_file):
    if len(layers_description_list) > 1:
        current_layer_description = layers_description_list.pop(0)
        next_layer_url_list = current_layer_description['process_this_layer_func'](current_layer_description, except_log_file)
        print '\n'*2, 'Next layer url list: ', next_layer_url_list, '\n'*2
        layers_description_list[0]['items_urls_and_descriptions'] = next_layer_url_list
        return process_site_layers(layers_description_list, except_log_file)
    elif len(layers_description_list) == 1:
        current_layer_description = layers_description_list.pop(0)
        return current_layer_description['process_this_layer_func'](current_layer_description, except_log_file)


def to_csv(fundays_data):
    with codecs.open('fundays.csv', 'w') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Name', 'Categories', 'Region', 'Street address', 'Telephone', 'Telephone international', 'Web', 'Email', 'Advert text', 'Location coordinates', 'Image id'])
    
        for venue in fundays_data.values():
            categories_list = venue['categories']
            categories = ''
            for category in categories_list:
                categories = categories + category + ' '
            
            full_description = venue['description']
            venue_id = full_description['id']
            name = get_description_item(full_description, 'name')
            region = get_description_item(full_description, 'region')
            street_address = get_description_item(full_description, 'street_address')
            site = get_description_item(full_description, 'site')
            email = get_description_item(full_description, 'email')
            phone = get_description_item(full_description, 'phone')
            international_phone = get_description_item(full_description, 'international_phone')
            advert_text = get_description_item(full_description, 'advert_text')
            location = '(0, 0)'
            location_coordinates_list = full_description.get('location_coordinates')
            if location_coordinates_list != None and location_coordinates_list != [] and len(location_coordinates_list) == 2:
                location = '(%s, %s)' % (location_coordinates_list[0], location_coordinates_list[1])
            writer.writerow([name, categories, region, street_address, phone, international_phone, site, email, advert_text, location, venue_id])

def do_scrape(download_dir='download', download_processes_num=4, except_log_file_name='request_exceptions_fundays.log'):
    global img_dir
    global processes_num
    processes_num = download_processes_num
    img_dir = site_subdir_creator(img_dir)(download_dir)
    except_log_file = open(except_log_file_name, 'w')
    start_time = time.time()
    venues =  process_site_layers(site_layers_description_list, except_log_file)
    except_log_file.close()
    print 'test.fundays.ie scrapping time: ', str(time.time() - start_time)
    save_data(venues, 'fundays.dat')
    fundays_data = get_saved_data('fundays.dat')
    to_csv(fundays_data)

if __name__ == '__main__':
    
     
    create_dirs(img_dir)
    
    except_log_file = open('request_exceptions_fundays.log', 'w')
    start_time = time.time()
    venues =  process_site_layers(site_layers_description_list, except_log_file)
    print 'test.fundays.ie scrapping time: ', str(time.time() - start_time)
    save_data(venues, 'fundays.dat')
    except_log_file.close()
    fundays_data = get_saved_data('fundays.dat')
    to_csv(fundays_data)
    

    #urls = second_layer_single_page_processor('', '', '', '')


    description = {
            'items_urls_and_descriptions' : {},
            #'info_container_xpath' : '//body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]',
            #'info_container_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/table/tr/td/table/tr/td/div/h3',
            #'info_container_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/table/tr/td/table/tr/td/div',
            'info_container_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/div[@class="details"]/table/tr/td/table/tr/td/div',
            'list_detail_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]',
            #'img_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/table/tr/td/table/tr/td/div/table/tr/td/img',
            'img_xpath' : '/html/body/div[@class="container"]/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td/div[@class="details"]/table/tr/td/table/tr/td/div/table/tr/td/img[@class="watermark"]',
            'address_node_xpath' : '/html/body/div/div[@class="wrapper"]/table/tr/td[@class="pagebg"]/table/tr/td[@class="mid_pad"]/table[@class="list_detail"]/td[@valign="top"]/table/tr/td/table/tr/td/div/div[@itemprop="address"]',
            'contacts_header_xpath' : 'h3',
            'phone_xpath' : 'span[@itemprop="telephone"]',
            'info_header_tag_xpath' : 'b',
            'location_coordinates_xpath' : '',
            'region_address_xpath' : 'span[@itemprop="addressRegion"]',
            'street_address_xpath' : 'span[@itemprop="streetAddress"]',
            'process_this_layer_func' : third_layer_processor
            }
    
    args = (description, {}, [''], 1, '')

    #layer_description, items_urls_and_descriptions, urls_list_slice, start_venue_id, exceptions_log_file = args

    #third_layer_data_slice_processor(args)
