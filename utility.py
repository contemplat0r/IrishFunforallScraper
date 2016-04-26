# -*- coding: utf8 -*- 

from lxml import etree
from StringIO import StringIO
import os
import requests
import pickle
import codecs
import httplib
import sys
import shutil

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

def get_html(url, headers={'User-Agent' : 'requests'}, post_data={}, exceptions_log_file=None):
    req = None
    html = None
    try: 
        if post_data == {}:
            req = requests.get(url, headers=headers)
        else:
            req = requests.post(url, headers=headers, data=post_data)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError, httplib.IncompleteRead, requests.exceptions.MissingSchema) as e:
        print 'get_html: ' + url + '  Exception: ' + str(e) + '\n'
        if exceptions_log_file != None:
            exceptions_log_file.write('get_html: ' + url + ' Exception: ' + str(e) + '\n')
            exceptions_log_file.flush()
    if req != None:
        html = req.text

    return html

def img_download(url, file_name, file_dir, exceptions_log_file=None):
    try:
        img = requests.get(url, stream=True)
        img_type = url.split('.').pop()
        img_file = '%s/%s.%s' % (str(file_dir), str(file_name), str(img_type))
        with open(img_file, 'wb') as f:
            for chunk in img.iter_content(512):
                f.write(chunk)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError, httplib.IncompleteRead, requests.exceptions.MissingSchema) as e:
        if exceptions_log_file != None:
            exceptions_log_file.write('img_download: ' + url + ' Exception: ' + str(e) + '\n')
            exceptions_log_file.flush()


def save_html(html, filename):
    success = True
    f = codecs.open(filename, 'w', encoding='utf-8')
    f.write(html)
    f.close()
    return success

def get_saved_html(filename):
    f = codecs.open(filename, 'r', encoding='utf-8')
    html = f.read()
    f.close()
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

def walk_to_root(node):
    if node != None:
        walk_to_root(node.getparent())
        node_str = node.tag
        for attrib, value in node.items():
            node_str = node_str + ' %s=%s' % (attrib, value)
        print node_str
    else:
        print 'Root element reached'
    return

def define_download_dir_path(download_dir=None):
    if download_dir != None and download_dir != '' and len(download_dir) > 1:
        if download_dir[0] != '/':
            #download_dir_path = os.path.join(os.path.dirname(__file__), download_dir)
            download_dir_path = os.path.join(os.path.abspath(os.path.curdir), download_dir)
        else:
            download_dir_path = download_dir
        return download_dir_path
    else:
        return None

def create_download_dir(download_dir_path=None):
    if download_dir_path != None:
        create_dirs(download_dir_path)
    else:
        print 'Error! Not define img download dir'


def site_subdir_creator(site_subdir):
    def create_site_subdir(download_dir_path):
        site_subdir_path = os.path.join(download_dir_path, site_subdir)
        if os.path.exists(site_subdir_path):
            shutil.rmtree(site_subdir_path)
        create_dirs(site_subdir_path)
        return site_subdir_path
    return create_site_subdir


if __name__ == '__main__':
    pass
