# -*- coding: utf8 -*- 

import fundays_multiprocessing 
import discoverireland_multiprocessing
import menupages_multiprocessing
from utility import define_download_dir_path, create_download_dir
download_dir = 'download'


if __name__ == '__main__':

    download_dir_path = define_download_dir_path(download_dir)
    create_download_dir(download_dir_path)
    fundays_multiprocessing.do_scrape(download_dir_path, download_processes_num=4, except_log_file_name = 'request_exceptions_fundays.log')
    #discoverireland_multiprocessing.do_scrape(download_dir_path, download_processes_num=12, except_log_file_name = 'request_exceptions_discoverireland.log')
    menupages_multiprocessing.do_scrape(download_dir_path, download_processes_num=8, except_log_file_name = 'request_exceptions_menupages.log')

