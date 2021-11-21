import os
import subprocess
import time
import pandas as pd
import socket
import tldextract
import gc
from random import randint

from selenium.webdriver.common.by import By
from tbselenium.tbdriver import TorBrowserDriver
from selenium import webdriver
from selenium.common.exceptions import WebDriverException as wde, ElementClickInterceptedException, \
    ElementNotInteractableException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import warnings
warnings.filterwarnings('ignore')

# path to tor browser bundle
# Must use absolute path
TBB_PATH = '/home/jhiggs/Documents/TOR/tor-browser_en-US/'

# path to pcap files
# Must use absolute path
PACP_PATH = '/home/jhiggs/IdeaProjects/data-collection/PCAP'

run_time = 300

isFirefox = True


def web_crawler(index, link, ip_address, firefox):
    """
    This function is a web crawler for collection of traffic traces and saving those traces to pcap files.
    :param index: current trace of the link
    :param link: webpage address from where traffic is to be collected
    :param ip_address: ip-addres of the machine from which traffic is to be collected
    :param timeout: duration upto which traffic information needs to be collected
    :param pkt_count: number of packets to be collected for a particular trace
    :return:
    """

    # Extracting domain name for saving trace separately
    url = link
    lnk = tldextract.extract(url)
    domain_name = lnk.domain + '.' +lnk.suffix

    # find using ifconfig
    interface = 'wlp59s0'
    cap = DesiredCapabilities().FIREFOX
    cap["marionette"] = True  # optional
    try:

        if firefox : driver = webdriver.Firefox()
        else: driver = TorBrowserDriver(TBB_PATH)

        # saving the pcapfiles
        PP = PACP_PATH
    except wde as e:
        print('Browser crashed:')
        print(e)
        print('Trying again in 10 seconds ...')
        time.sleep(10)
        driver = driver
        print('Success!\n')
    except Exception as e:
        raise Exception(e)

    if not os.path.isdir(PP):
        print('Creating directory for saving capture files (pcap) ...')
        os.makedirs(PP)
    else:
        pass


    # command to be executed for capturing the trace
    command = "sudo timeout {0} tcpdump -i ".format(run_time) + str(interface) + " -n host " + str(ip_address) + " -w " + PP + "/" + domain_name + "_" + str(index) + ".pcap"
    print('Capture trace ...')
    capture = subprocess.Popen(command, shell=True)

    driver.get(url)  # launches website

    # generates random activity by clicking links the page
    while hasNotFinished(capture) :
        elements = driver.find_elements_by_tag_name('a')
        tryElement(driver, elements, capture)

    print('Traffic trace captured and saved successfully.')
    driver.quit()

# checks if the tcpdump has finished
def hasNotFinished(popen):
    return popen.poll() is None


def tryElement(driver, elements, capture) :
    element = elements[randint(0, len(elements) - 1)]  # find a random element on the page
    if element.is_displayed() and element.is_enabled():  # ensure we can click on the element
        try:
            element.click()
            time.sleep(20)  # sleep for a bit to make sure we can accurately collect data
        except (ElementNotInteractableException, ElementClickInterceptedException):
                if hasNotFinished(capture) :  # on an exception find a differnt element and try again
                    tryElement(driver, driver.find_elements_by_tag_name('a'), capture)

if __name__ == '__main__':

    print('Starting to collect traffic trace for the webpages of similar topics...')

    IP_ADDRESS = '10.1.1.45' # ip-address of the machine from which traffic is to be captured
    print('IP-Address : ', IP_ADDRESS)

    # Number of traces to be collected for a partiular link
    traces = 1

    links_path = './modified.xlsx' # path to excel file containing links of the webpages

    # getting excel file containing links
    links = pd.read_excel(links_path)


    print('Web crawler started ...')
    start_time = pd.Timestamp.now()
    # getting traces for the links
    print(range(traces))
    for j in range(traces):
        print('Batch : %d'%(j+1))
        print('+'*80)
        for i in range(len(links)):
            print('Trace: %d for domain %s'%(j+1, links.iloc[i][0]))
            start_time_tr = pd.Timestamp.now()
            web_crawler(j+1, links.iloc[i][1], IP_ADDRESS, isFirefox)
            end_time_tr = pd.Timestamp.now() - start_time_tr
            print('Time taken to collect trace: ', end_time_tr)
            gc.collect()
            print('*'*80)

    end_time = pd.Timestamp.now() - start_time
    print('program execution completed.')
    print('Time taken for data collection: ', end_time)
