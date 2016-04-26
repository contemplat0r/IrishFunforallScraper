# -*- coding: utf8 -*-

import httplib
from lxml import etree
from StringIO import StringIO
from copy import deepcopy
import requests
import json
import codecs
import csv
import os
import time
import multiprocessing
from utility import create_dirs, space_drop, get_html, save_html, get_saved_html, get_saved_data, save_data, img_download, site_subdir_creator
from htmlutils import get_all_same_type_nodes, generate_attrib_getter, node_list_processor

root_site_url = 'http://www.discoverireland.ie'
site_layers_description_list = list()
user_agent_header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0'}
parser = etree.HTMLParser()
#img_dir = 'download/discoverireland/img'
img_dir = 'discoverireland'
page_size = 80
processes_num = 16

url_json = 'http://www.discoverireland.ie/cmswebservices/discoverirelandservice.asmx/GetTIOList'
headers_json = {
    'Host' : 'www.discoverireland.ie',
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0',
    'Accept' : 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language' : 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding' : 'gzip, deflate',
    'Content-Type' : 'application/json; charset=utf-8',
    'X-Requested-With' : 'XMLHttpRequest',
    'Referer' : '',
    'Connection' : 'keep-alive',
    'Pragma' : 'no-cache',
    'Cache-Control' : 'no-cache'
}

def get_content(url, headers={'User-Agent' : 'requests'}, post_data=None, exceptions_log_file=None):
    req = None
    content = None
    try: 
        if post_data == None:
            req = requests.get(url, headers=headers)
        elif post_data == {}:
            req = requests.post(url, headers=headers)
        else:
            req = requests.post(url, headers=headers, data=post_data)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError, httplib.IncompleteRead, requests.exceptions.MissingSchema) as e:
        print 'get_content: ' + url + '  Exception: ' + str(e) + '\n'
        if exceptions_log_file != None:
            exceptions_log_file.write('get_content: ' + url + ' Exception: ' + str(e) + '\n')
            exceptions_log_file.flush()
    if req != None:
        content = req.text

    return content


def get_description_item(description, item_name):
    item = description.get(item_name)
    if item == None:
        item = ''
    return item.strip().encode('utf-8')


def first_layer_processor(layer_description, exceptions_log_file):
    next_layer_url_list = list()
    url = root_site_url + layer_description['items_urls_and_descriptions']

    '''
    html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(html), parser)
    info_container = tree.xpath(layer_description['info_container_xpath'])
    if info_container != []:
        print 'first_layer_processor: info_container != [] ', info_container 
        urls_container = info_container[0].xpath(layer_description['info_tag_xpath'])
        for url_container in urls_container:
            next_layer_url_list.append(url_container.attrib['href'])
        next_layer_url_list = list(set([next_layer_url for next_layer_url in next_layer_url_list if next_layer_url != '#']))
        for item in next_layer_url_list:
            print item
    else:
        print 'first_layer_processor: info_container == []: ', info_container 

    ''' 
    content = get_content(url, headers_json, post_data={})

    json_dict = json.loads(content)
    html = json_dict['d']   
    
    all_same_type_nodes = get_all_same_type_nodes(html, layer_description['info_container_xpath'])

    #print all_same_type_nodes

    get_attrib = generate_attrib_getter('href')
    result_list = node_list_processor(all_same_type_nodes, get_attrib)
    result_list = [item for item in result_list if item.find('subcatid') != -1]
    for result in result_list:
        print '\n' * 2, '-' * 10
        print result
        next_layer_url_list.append(result)

    next_layer_url_list = list(set([next_layer_url for next_layer_url in next_layer_url_list if next_layer_url != '#']))
    return next_layer_url_list

site_layers_description_list.append(
    {
        #'items_urls_and_descriptions' : '/Places-To-Go',
        'items_urls_and_descriptions' : '/cmswebservices/discoverirelandservice.asmx/GetSimpleSearchWhatsOnHTML',
        #'info_container_xpath' : '/html/body/form[@id="form"]/div[@id="wrap-main"]/div[@class="column-narrow tl"]/div[@class="tc bc grey-box"]/div[@class="pad-10"]/map[@name="counties"]',
        'info_container_xpath' : '//a',
        'info_tag_xpath' : 'area',
        'process_this_layer_func' : first_layer_processor,
    }
)

def second_layer_info_container_processor(container_node, id_permanent_part, info_tag_xpathes_dict, tab_num):
    values_dict = {
        'localCategoryID' : '',
        'categoryIDs' : '',
        'countyIDs' : '',
        'areaIDs' : '',
        'locationIDs' : '',
        'marketingCompaignIDs' : '',
        'attributesIDs' : '',
        'attributestype' : '',
        'pageIndex' : '1',
        'pageSize' : '80',
        'sortOrder' : '1',
        'tabNumber' : str(tab_num),
        'sLocType' : '',
        'sLocIDs' : '',
        'sWebPartID' : ''
        }
    info_tag_xpathes_dict_copy = deepcopy(info_tag_xpathes_dict)
    values_dict['sWebPartID'] = second_layer_info_tag_processor(container_node, info_tag_xpathes_dict_copy.pop('sWebPartID') % id_permanent_part)
    for key, info_tag_xpath in info_tag_xpathes_dict_copy.items():
        values_dict[key] = second_layer_info_tag_processor(container_node, info_tag_xpath % (id_permanent_part, str(tab_num)))
    return values_dict

def second_layer_info_tag_processor(container_node, info_tag_xpath):
    value = ''
    print info_tag_xpath
    info_tag_list = container_node.xpath(info_tag_xpath)
    if info_tag_list != []:
        info_tag = info_tag_list[0]
        if 'value' in info_tag.keys():
        #if info_tag.has_key('value'):
            value = info_tag.attrib['value']
    return value

def second_layer_venue_description_processor(venue_div_node):
    description_dict = dict()
    a_href_nodes = venue_div_node.xpath('a')
    if a_href_nodes != []:
        description_dict['url'] = a_href_nodes[0].attrib['href']
        short_venue_description = dict()
        for b_node in venue_div_node.xpath('b'):
            short_venue_description[b_node.text] = b_node.tail
        #description_dict[a_href_nodes[0].attrib['href']] = short_venue_description
        for br_node in venue_div_node.xpath('br'):
            if br_node.tail != None:
                short_venue_description['Info'] = br_node.tail
        description_dict['short_description'] = short_venue_description

    return description_dict

def second_layer_get_json(url_json, headers_json, extra_data_dict):
    response = requests.post(url_json, headers=headers_json, data=json.dumps(extra_data_dict))
    response_json = response.json()
    #print response_json
    '''
    save_html(unicode(json.dumps(response_json, ensure_ascii=False)), json_file_name)

    json_str = get_saved_html(json_file_name)
    #print json_str
    
    json_dict = json.loads(json_str)
    '''
    return response_json

def second_layer_json_processor(json_dict):
    next_layer_description_dict = dict()
    #json_dict = json.loads(json_str)
    next_layer_info_container = json_dict.values()
    if next_layer_info_container != []:
        next_layer_info_string = next_layer_info_container[0]
        num_items_part = next_layer_info_string[0:next_layer_info_string.find('#')]
        next_layer_urls_part = next_layer_info_string[next_layer_info_string.find('~') + 1:]
        next_layer_urls_part = next_layer_urls_part[0:next_layer_urls_part.rfind('#~')]
        tree = etree.parse(StringIO(next_layer_urls_part), parser)

        body_lst = tree.xpath('/html/body')
        if body_lst != []:
            body = body_lst[0]
            info_nodes_lst = body.xpath('div[@class="google-maps-info"]')
            if info_nodes_lst != []:
                for info_node in info_nodes_lst:
                    description_dict = second_layer_venue_description_processor(info_node)
                    if next_layer_description_dict.has_key(description_dict['url']):
                        next_layer_description_dict[description_dict['url']].append(description_dict['short_description'])
                    else:
                        next_layer_description_dict[description_dict['url']] = [description_dict['short_description']]
        return int(num_items_part), next_layer_description_dict


def second_layer_processor(layer_description, exceptions_log_file):
    next_layer_urls_and_descriptions = dict()
    for place_url in layer_description['items_urls_and_descriptions']:
        url = root_site_url + place_url
        print '\n'*3,  url
        html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html), parser)
        for container_xpath in layer_description['info_containers_xpaths']:
            info_container = tree.xpath(container_xpath)
            if info_container != []:
                id_attrib = info_container[0].xpath('input')[0].attrib['id']
                variable_id_first_part = id_attrib[len(layer_description['info_tag_id_head']):id_attrib.find(layer_description['input_tag_id_permanent_component'])]
                input_field_id_permanent_part = layer_description['info_tag_id_head'] + variable_id_first_part + layer_description['input_tag_id_permanent_component']
                id_attrib_tail = id_attrib[len(input_field_id_permanent_part):]
                variable_id_second_part = id_attrib_tail[0:id_attrib_tail.find('_')]
                input_field_id_permanent_part = input_field_id_permanent_part + variable_id_second_part + '_'
                for tab_num in [1, 2, 3, 4]:
                #for tab_num in [1]:
                    values_dict = second_layer_info_container_processor(info_container[0], input_field_id_permanent_part, layer_description['info_tag_xpathes_dict'], tab_num)
                    #print values_dict
                    headers_json['Referer'] = url
                    response_json = second_layer_get_json(url_json, headers_json, values_dict)
                    total_items, urls_and_short_descriptions_dict = second_layer_json_processor(response_json)
                    #print urls_and_short_descriptions_dict
                    for url, short_descriptions_list in urls_and_short_descriptions_dict.items():
                        #print url
                        if next_layer_urls_and_descriptions.has_key(url):
                            next_layer_urls_and_descriptions[url]['short_description'].extend(short_descriptions_list)
                        else:
                            next_layer_urls_and_descriptions[url] = {'short_description' : short_descriptions_list, 'full_description' : {}}

                    pages_num = total_items / page_size
                    if total_items % page_size > 0:
                        pages_num = pages_num + 1
                    for page_num in range(2, pages_num + 1):
                        values_dict['pageIndex'] = str(page_num)
                        print values_dict
                        response_json = second_layer_get_json(url_json, headers_json, values_dict)
                        _, urls_and_short_descriptions_dict = second_layer_json_processor(response_json)
                        for url, short_descriptions_list in urls_and_short_descriptions_dict.items():
                            print url
                            if next_layer_urls_and_descriptions.has_key(url):
                                next_layer_urls_and_descriptions[url]['short_description'].extend(short_descriptions_list)
                            else:
                                next_layer_urls_and_descriptions[url] = {'short_description' : short_descriptions_list, 'full_description' : {}}
                            for description in short_descriptions_list:
                                print description
                    #print total_items
    for url, descript in next_layer_urls_and_descriptions.items():
        print url, descript
    print len(next_layer_urls_and_descriptions.items())
    return next_layer_urls_and_descriptions


site_layers_description_list.append(
    {
        'items_urls_and_descriptions' : [],
        'info_containers_xpaths' : [
                    '/html/body/form[@id="form"]/div[@id="wrap-main"]/div[@class="column-wide tr"]/div[@class="panes"]/div[@class="pane pane-one"]/div/div[@id="tio-container"]',
                    '/html/body/form[@id="form"]/div[@id="wrap-main"]/div[@class="column-wide tr"]/div[@class="panes"]/div[@class="pane pane-two"]/div/div[@id="tio-container"]',
            ],
        'info_tag_id_head' : 'p_lt_zoneMain_pphMain_p_lt_',
        'input_tag_id_permanent_component' : '_GenericListing_',
        'info_tag_xpathes_dict' :
            {
                'sWebPartID' : 'input[@id="%stxtWpID"]',
                'localCategoryID' : 'input[@id="%stxtObjectIDTab%s"]',
                'categoryIDs' : 'input[@id="%stxtCategoryIDTab%s"]',
                'sLocType' : 'input[@id="%stxtTab%s_LocType"]',
                'sLocIDs' :'input[@id="%stxtTab%s_LocIDs"]',
                'areaIDs' :'input[@id="%stxtAreaIDTab%s"]',
                'countyIDs' :'input[@id="%stxtCountyIDTab%s"]',
                'locationIDs' : 'input[@id="%stxtLocationIDTab%s"]',
                'marketingCompaignIDs' : 'input[@id="%stxtMarketingCampaignIDTab%s"]',
                'attributesIDs' : 'input[@id="%stxtAttributesIDTab%s"]',
                'attributestype' : 'input[@id="%stxtAttributesIDType%s"]',
            },

        'process_this_layer_func' : second_layer_processor
    }
)

#def third_layer_data_slice_processor(layer_description, items_urls_and_descriptions, urls_list_slice, start_venue_id, exceptions_log_file):
def third_layer_data_slice_processor(args):
    result_dict = dict()
    layer_description, items_urls_and_descriptions, urls_list_slice, start_venue_id, exceptions_log_file = args
    venue_id = start_venue_id
    for local_url_part in urls_list_slice:
        full_description = dict()
        full_description['id'] = venue_id
        url = root_site_url + local_url_part
        html = get_html(url, user_agent_header, post_data={}, exceptions_log_file=exceptions_log_file)
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html), parser)

        contacts_container = tree.xpath(layer_description['contacts_container_xpath'])
        name_container = tree.xpath(layer_description['name_xpath'])
        if name_container != []:
            name_node = name_container[0]
            full_description['name'] = name_node.text
        if contacts_container != []:
            print contacts_container
            contacts_container_node = contacts_container[0]
            address_components = contacts_container_node.xpath(layer_description['address_components_xpath'])
            address = ''
            if address_components != []:
                for address_component in address_components:
                    address = address + address_component.text + ' '
            print address
            full_description['address'] = address
            phone_node_container = contacts_container_node.xpath(layer_description['phone_xpath'])
            full_description['phone'] = ''
            if phone_node_container != []:
                phone_node = phone_node_container[0]
                print phone_node.text
                full_description['phone'] = phone_node.text
            email_node_container = contacts_container_node.xpath(layer_description['email_xpath'])
            full_description['email'] = ''
            if email_node_container != []:
                email_node = email_node_container[0]
                print email_node.text
                full_description['email'] = email_node.text
            web_node_container = contacts_container_node.xpath(layer_description['web_xpath'])
            full_description['web'] = ''
            if web_node_container != []:
                web_node = web_node_container[0]
                print web_node.text
                full_description['web'] = web_node.text
            text = ''
            #text_node_container = contacts_container_node.xpath(layer_description['text_xpath'])
        text_node_container = tree.xpath(layer_description['text_xpath'])
        if text_node_container != []:
            text_node = text_node_container[0]
            text = text = text_node.text
            for text_part_node in text_node.xpath(layer_description['text_other_parts_xpath']):
                if text_part_node.tail != None:
                    text = text + ' ' + text_part_node.tail
            print text
            full_description['text'] = text
        social_shares_container = tree.xpath(layer_description['social_shares_container_xpath'])
        if social_shares_container != []:
            social_shares_node = social_shares_container[0]
            facebook_container = social_shares_node.xpath(layer_description['facebook_xpath'])
            if facebook_container != []:
                print facebook_container[0].attrib['href']
                full_description['facebook_link'] = facebook_container[0].attrib['href']
            twitter_container = social_shares_node.xpath(layer_description['twitter_xpath'])
            if twitter_container != []:
                print twitter_container[0].attrib['href']
                full_description['twitter_link'] = twitter_container[0].attrib['href']
            google_container = social_shares_node.xpath(layer_description['google_xpath'])
            if google_container != []:
                print google_container[0].attrib['href']
                full_description['gplus_link'] = google_container[0].attrib['href']
                '''
        location_container = tree.xpath(layer_description['location_container_xpath'])
        if location_container != []:
            location_node = location_container[0]
            latitude_container = location_node.xpath(layer_description['latitude_xpath'])
            if latitude_container != []:
                latitude_value = latitude_container[0].get('value')
                if latitude_value != None:
                    print latitude_value
                    full_description['latitude'] = latitude_value
            longitude_container = location_node.xpath(layer_description['longitude_xpath'])
            if longitude_container != []:
                longitude_value = longitude_container[0].get('value')
                if longitude_value != None:
                    print longitude_value
                    full_description['longitude'] = longitude_value
                    '''
        latitude_container = tree.xpath(layer_description['latitude_xpath'])
        if latitude_container != []:
            latitude_value = latitude_container[0].get('value')
            if latitude_value != None:
                print latitude_value
                full_description['latitude'] = latitude_value
        longitude_container = tree.xpath(layer_description['longitude_xpath'])
        if longitude_container != []:
            longitude_value = longitude_container[0].get('value')
            if longitude_value != None:
                print longitude_value
                full_description['longitude'] = longitude_value

        img_container_list = tree.xpath(layer_description['img_container_xpath'])
        if img_container_list != []:
            img_container = img_container_list[0]
            img_num = 0
            img_list = list()
            for img_node in img_container.xpath(layer_description['img_node_xpath']):
                img_url = img_node.attrib.get('full')
                print img_url
                if img_url != None:
                    if img_url != '':
                        img_list.append(img_url)
                        img_file_name = '%s_%s' % (str(venue_id), str(img_num))
                        img_num = img_num + 1
                        img_download(img_url, img_file_name, img_dir, exceptions_log_file)
            full_description['img_urls'] = img_list

        short_description = items_urls_and_descriptions[local_url_part]['short_description']
        result_dict[local_url_part] = {'short_description' : short_description, 'full_description' : full_description}
        #print items_urls_and_descriptions[local_url_part]
        venue_id = venue_id + 1
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
        'name_xpath' : '/html/body/form[@id="form"]/div[@id="wrap-main"]/div[@class="column-tourist-main tc"]/div[@class="column-tourist-wide"]/h2[@class="fc-color tcs_analytics_title"]',
        #'contacts_container_xpath' : '/html/body/form[@id="form"]/div[@id="wrap-main"]/div[@class="column-tourist-main tc"]/div[@class="column-tourist-wide"]/div[@class="eq"]/div[@class="column-tourist-two"]',
        'contacts_container_xpath' : '//div[@class="column-tourist-two"]',
        'address_components_xpath' : 'div/div[@class="tcs-address"]/p/span[@class="Address_Layout"]',
        'phone_xpath' : 'div/div[@class="contact-link"]/span',
        'email_xpath' : 'div/div[@class="contact-link contact-email"]/a[@class="tcs_analytics_email"]',
        'web_xpath' : 'div/div[@class="contact-link contact-web"]/a[@class="tcs_analytics_externallink"]',
        #'text_xpath' : '/html/body/form[@id="form"]/div[@id="wrap-main"]/div[@class="column-tourist-main tc"]/div[@class="column-tourist-wide"]/div[@class="eq"]/div[@class="column-tourist-one"]/p',
        'text_xpath' : '//div[@class="column-tourist-one"]/p',
        'text_other_parts_xpath' : 'br',
        'social_shares_container_xpath' : '/html/body/form[@id="form"]/div[@id="social-share-wrapper"]/div[@id="social-share"]/div[@class="content-l"]/div[@class="options"]',
        'facebook_xpath' : 'a[@id="p_lt_zShare_S_hlnkFacebook"]',
        'twitter_xpath' : 'a[@id="p_lt_zShare_S_hlnkTwitter"]',
        'google_xpath' : 'a[@id="p_lt_zShare_S_hlnkGoogle"]',
        'location_container_xpath' : '/html/body/form[@id="form"]/div[@id="wrap-main"]/div[@class="column-tourist-main tc"]/div[@class="column-tourist-narrow"]',
        #'latitude_xpath' : 'input[@class="primary-latitude"]',
        'latitude_xpath' : '//input[@class="primary-latitude"]',
        #'longitude_xpath' : 'input[@class="primary-longitude"]',
        'longitude_xpath' : '//input[@class="primary-longitude"]',
        #'img_container_xpath' : '/html/body/form[@id="form"]/div[@id="wrap-main"]/div[@class="column-tourist-main tc"]/div[@class="column-tourist-wide"]/div[@class="eq"]/div[@class="column-tourist-one"]/div[@class="tourist-gallery"]/ul[@id="tourist-thumbs"]',
        'img_container_xpath' : '//ul[@id="tourist-thumbs"]',
        'img_node_xpath' : 'li/div[@class="clip"]/img',
        'process_this_layer_func' : third_layer_processor
    }
)

def process_site_layers(layers_description_list, exceptions_log_file):
    if len(layers_description_list) > 1:
        current_layer_description = layers_description_list.pop(0)
        next_layer_url_list = current_layer_description['process_this_layer_func'](current_layer_description, exceptions_log_file)
        layers_description_list[0]['items_urls_and_descriptions'] = next_layer_url_list
        return process_site_layers(layers_description_list, exceptions_log_file)
    elif len(layers_description_list) == 1:
        current_layer_description = layers_description_list.pop(0)
        return current_layer_description['process_this_layer_func'](current_layer_description, exceptions_log_file)


def to_csv(discoverireland_data):
    with codecs.open('discoverireland.csv', 'w') as f:
        except_file = open('except_after_scrape.log', 'w')
        writer = csv.writer(f, delimiter=';')
        #writer.writerow(['Name', 'Address', 'Phone', 'Web', 'Cuisines main', 'Cuisines rest', 'Advert text', 'Location coordinates', 'Images id'])
        writer.writerow(['Name', 'Category', 'Short info', 'Short address','Address', 'Telephone', 'Web', 'Email', 'Facebook', 'Twitter', 'Gplus', 'Advert text', 'Location coordinates', 'Images ID'])

        #for venue_description in discoverireland_data.values():
        for url, venue_description in discoverireland_data.items():
            print url
            print venue_description
            try:
                full_description = venue_description['full_description']
                name = get_description_item(full_description, 'name')
                address = get_description_item(full_description, 'address')
                web = get_description_item(full_description, 'web')
                email = get_description_item(full_description, 'email')
                phone = get_description_item(full_description, 'phone')
                advert_text = get_description_item(full_description, 'text')
                facebook = get_description_item(full_description, 'facebook_link')
                twitter = get_description_item(full_description, 'twitter_link')
                gplus = get_description_item(full_description, 'gplus_link')
                location = '(0, 0)'
                latitude = get_description_item(full_description, 'latitude')
                longitude = get_description_item(full_description, 'longitude')
                img_id = full_description['id']
                if latitude != '' and longitude != '':
                    location = '(%s, %s)' % (latitude, longitude)

                short_descriptions_list = venue_description['short_description']
                for short_description in short_descriptions_list:
                    category = get_description_item(short_description, 'Category')
                    short_info = get_description_item(short_description, 'Info')
                    start_date = get_description_item(short_description, 'Start Date')
                    end_date = get_description_item(short_description, 'End Date')
                    if start_date != '' and end_date != '':
                        short_info = short_info + ' Start Date: ' + start_date + ',  End Date: ' + end_date
                    short_address = get_description_item(short_description, 'Address')
                    telephone = get_description_item(short_description, 'Telephone')
                    if telephone != '' and phone == '':
                        phone = telephone
                    writer.writerow([name, category, short_info, short_address, address, phone, web, email, facebook, twitter, gplus, advert_text, location, img_id])
            except Exception as e:
                except_file.write(url + ' ' + str(e) + '\n')
        except_file.flush()
        except_file.close()

def do_scrape(download_dir='download', download_processes_num=8, except_log_file_name='request_exceptions_discoverireland.log'):
    global img_dir
    global processes_num
    processes_num = download_processes_num
    img_dir = site_subdir_creator(img_dir)(download_dir)
    except_log_file = open(except_log_file_name, 'w')
    start_time = time.time()
    discoverireland_data = process_site_layers(site_layers_description_list, except_log_file)
    print 'discoverireland.ie scrapping time: ', str(time.time() - start_time)
    save_data(discoverireland_data, 'discoverireland.dat')
    except_log_file.close()
    discoverireland_data = get_saved_data('discoverireland.dat')
    to_csv(discoverireland_data)

if __name__ == '__main__':
    
    
    create_dirs(img_dir)
    exceptions_log_file = open('discoverireland_exceptions.log', 'w')
    start_time = time.time()
    discoverireland_data = process_site_layers(site_layers_description_list, exceptions_log_file)
    print 'discoverireland.ie scrapping time: ', str(time.time() - start_time)
    save_data(discoverireland_data, 'discoverireland.dat')
    exceptions_log_file.close()
    
    discoverireland_data = get_saved_data('discoverireland.dat')
    to_csv(discoverireland_data)
    

    #exceptions_log_file = open('discoverireland_exceptions.log', 'w')
    #first_layer_processor(site_layers_description_list[0], exceptions_log_file) 
    #exceptions_log_file.close()
