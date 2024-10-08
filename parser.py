import requests
from bs4 import BeautifulSoup
import csv
import re
import tkinter as tk
from tkinter import messagebox

SUBSCRIBERS_PARSING_LIMIT = 100

URL_BASE = 'https://tgstat.ru'
URL_GEO = 'https://tgstat.ru/tags/geo'
URL_REGION_START = "https://tgstat.ru/tag/"
URL_STAT = "/stat"
# https://tgstat.ru/channel/@incident22
HEADERS = {
    # "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36",
    # "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "user-agent": 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
           "accept" :"*/*"}

def get_H_text_strip(html_h):
    result = None
    try:
        result = html_h.text.strip()
    except:
        pass
    finally:
        return result

def get_tag_text_strip(html_tag):
    result = None
    try:
        result = html_tag.get_text().strip()
    except:
        pass
    finally:
        return result

def get_html(url, params = None):
    result = requests.get(url, headers=HEADERS, params=params)
    if result.status_code != 200:
        print('Error, status_code: ', result.status_code)
        exit(1)
    return result.text

def get_regions_url(html):
    """
    Return list of all region url. 
    Example: ["https://tgstat.ru/tag/altai-region", "..."]
    """
    soup = BeautifulSoup(html, 'html.parser')
    tagslist_div = soup.find('div', id='tagsList')
    try:
        regions = tagslist_div.find_all("div", class_="card")
    except Exception as e:
        print(f"Exeption ({e}). Impossible to get regions url. You have probably been banned.")
        exit(1)
    
    region_links = []
    for region in regions:
        region_links.append(URL_BASE + region.find('a').get('href'))
    
    return region_links            

def choose_custom_region_url(region_links):
    print("Aviable regions:")
    for i in range(len(region_links)):
        print(f"{i} - {region_links[i]}")

    region_nums = input("Enter the region number for parsing (like: 0 2 6 \ or range: 54-78): ")
    if "-" in region_nums:
        start,end = map(int, region_nums.strip().split("-"))
        urls = [region_links[i] for i in range(start,end)]
    else:
        region_nums = map(int, region_nums.strip().split(" "))
        urls = [region_links[i] for i in region_nums]
        
    print("Start parsing these custom regions: ", urls)
    return urls

def get_chanels_url(html):
    """    
    Args: html from region url (like https://tgstat.ru/tag/altai-region)

    Return List of all chanels links. Example: ['https://tgstat.ru/channel/@incident22','.....']
    """
    soup = BeautifulSoup(html, 'html.parser')
    cards = []
    items = soup.find_all("div", class_="card")
    try:
        for item in items:
            cards.append(item.find('a', class_='text-body').get('href'))
    except Exception as e:
        print(f"Exeption ({e}). Impossible to get chanels url. You have probably been banned.")
        exit(1)
    return cards

def get_num_only(str):
    return re.sub(r'\D', '', str)

def get_empty_dict_structure():
    return {
        "name": None,
        "category": None,
        "about": None,
        "subs_num_total": None,
        "subs_num_today": None,
        "subs_num_week": None,
        "subs_num_moonth": None,
        "citation_index": None,
        "citation_num1": None,
        "citation_num2": None,
        "citation_reposts": None,
        "avg_coverage": None,
        "avg_coverage_without_ad": None,
        "chanel_created_date": None,
        "publications": None,
        "publications_by_day": None,
        "publications_by_week": None,
        "publications_by_month": None,
        "ER": None,
        "reposts": None,
        "komments": None,
        "reactions": None,
        "male%": None,
    }

def extract_description(hr_tag):
    text_after_hr = []
    current_element = hr_tag.next_sibling
    
    while current_element and current_element.name != 'p':
        if isinstance(current_element, str):
            text_after_hr.append(current_element.strip())
        elif current_element.name == "a":
            text_after_hr.append(current_element.get("href"))
        current_element = current_element.next_sibling
    
    result = ' '.join(filter(None, text_after_hr))
    return result

def get_header_stats(header):
    """
        Get basic statistic for 1 chanel
    """
    result = {
        "name": None,
        "category": None,
        "about": None,
    }
    try:        
        result["name"] = get_H_text_strip(header.h1)
        result["category"] = get_tag_text_strip(header.find("div", class_="text-left text-sm-right").find("div", class_="mt-2").find("a"))
        hr_tag = header.find("div", class_="col-12 col-sm-7 col-md-8 col-lg-6").find('hr', class_='m-0 mb-3')
        if hr_tag:
            result["about"] = extract_description(hr_tag)
    except Exception as e:
        ex_msg = f"Warning in get base statistics: {e}"
        raise Exception(ex_msg)
    
    return result

def get_subs_stat(html_block):
    result = {
            "subs_num_total": None,
            "subs_num_today": None,
            "subs_num_week": None,
            "subs_num_moonth": None,
        }
    try:
        result["subs_num_total"] = get_H_text_strip(html_block.h2)
        subs_num2 = html_block.find_all("b") # shoud be 3 <b> tags
        result["subs_num_today"] = get_tag_text_strip(subs_num2[0])
        result["subs_num_week"] = get_tag_text_strip(subs_num2[1])
        result["subs_num_moonth"] = get_tag_text_strip(subs_num2[2])
    except Exception as e:
        print(f"Warning in get subscribers statistics: {e}.", "Continue!")
    finally:
        return result

def get_cite_stat(html_block):
    result = {
            "citation_index": None,
            "citation_num1": None,
            "citation_num2": None,
            "citation_reposts": None,
        }
    try:
        result["citation_index"] = get_H_text_strip(html_block.h2)
        citation_index2 = html_block.find_all("b") # shoud be 3 <b> tags
        result["citation_num1"] = get_tag_text_strip(citation_index2[0])
        result["citation_num2"] = get_tag_text_strip(citation_index2[1])
        result["citation_reposts"] = get_tag_text_strip(citation_index2[2])
    except Exception as e:
        print(f"Warning in get citation statistics: {e}.", "Continue!")
    finally:
        return result

def get_avg_coverage_stat(html_block):
    result = {"avg_coverage": None}
    try:
        result["avg_coverage"] = get_H_text_strip(html_block.h2)
    except Exception as e:
        print(f"Warning in get coverage statistics: {e}.", "Continue!")
    finally:
        return result

def get_avg_coverage_without_ad_stat(html_block):
    result = {"avg_coverage_without_ad": None}
    try:
        result["avg_coverage_without_ad"] = get_H_text_strip(html_block.h2)
    except Exception as e:
        print(f"Warning in get coverage without ad statistics: {e}.", "Continue!")
    finally:
        return result

def get_chanel_created_date_stat(html_block):
    result = {"chanel_created_date": None}
    try:
        result["chanel_created_date"] = get_tag_text_strip(html_block.find("b"))
    except Exception as e:
        print(f"Warning in get date statistics: {e}.", "Continue!")
    finally:
        return result

def get_publications_stat(html_block):
    result = {
            "publications": None,
            "publications_by_day": None,
            "publications_by_week": None,
            "publications_by_month": None,
        }
    try:
        result["publications"] = get_num_only(get_H_text_strip(html_block.h2))
        publications_by_time = html_block.find_all("b") # shoud be 3 <b> tags
        result["publications_by_day"] = get_tag_text_strip(publications_by_time[0])
        result["publications_by_week"] = get_tag_text_strip(publications_by_time[1])
        result["publications_by_month"] = get_tag_text_strip(publications_by_time[2])
    except Exception as e:
        print(f"Warning in get publications statistics: {e}.", "Continue!")
    finally:
        return result

def get_ER_stat(html_block):
    result = {
            "ER": None,
            "reposts": None,
            "komments": None,
            "reactions": None,
        }
    try:
        result["ER"] = get_H_text_strip(html_block.h2)
        subscriber_engagement_rate_ER2 = html_block.find_all("b") # shoud be 3 <b> tags
        result["reposts"] = get_tag_text_strip(subscriber_engagement_rate_ER2[0])
        result["komments"] = get_tag_text_strip(subscriber_engagement_rate_ER2[1])
        result["reactions"] = get_tag_text_strip(subscriber_engagement_rate_ER2[2])
    except Exception as e:
        print(f"Warning in get ER statistics: {e}.", "Continue!")
    finally:
        return result

def get_gender_stat(html_block):
    result = {
            "male%": None
        }
    try:
        male = html_block.find("div", class_="col col-sm-6 mb-0").find("b")
        result["male%"] = get_tag_text_strip(male)
    except Exception as e:
        print(f"Warning in get gender statistics: {e}.", "Continue!")
    finally:
        return result

def wait_for_relogin():
    # Створюємо головне вікно
    root = tk.Tk()
    # root.withdraw() # hide
    messagebox.showinfo("Warning", "Login via Telegram on tgstat and then press OK")
    root.destroy()

def get_all_stats(html):
    """
        Get another statistic for 1 chanel (from url.../stat)
    """
    soup = BeautifulSoup(html, 'html.parser')
    result = get_empty_dict_structure()
    try:
        header = soup.find("div", class_="card card-body border mt-2")
        result.update(get_header_stats(header))
        
        body = soup.find("div", id="sticky-center-column")    
        list_html_blocks = body.find_all("div", class_="col-lg-6 col-md-12 col-sm-12")
        
        for block in list_html_blocks:
            block_name = get_tag_text_strip(block.find("div", class_="position-absolute text-uppercase text-dark font-12"))
            if block_name is None or block_name == "":
                continue
            elif "подписчики" == block_name:
                result.update(get_subs_stat(block))
            elif "индекс цитирования" == block_name:
                result.update(get_cite_stat(block))
            elif "средний охват" in block_name:
                result.update(get_avg_coverage_stat(block))
            elif "средний рекламный" in block_name:
                result.update(get_avg_coverage_without_ad_stat(block))
            elif "возраст канала" == block_name:
                result.update(get_chanel_created_date_stat(block))
            elif "публикации" == block_name:
                result.update(get_publications_stat(block))
            elif "(ER)" in block_name:
                result.update(get_ER_stat(block))
            elif "пол подписчиков" == block_name:
                result.update(get_gender_stat(block))
    except Exception as e:
        print(f"Exeption in get additional statistics: {e}. NEXT!")
    finally:
        return result

def save_file(items, path):
    with open(path+".csv", "w", encoding="UTF-8", errors='ignore', newline = '') as file:
        writer = csv.writer(file, delimiter=';')
        headers = list(items[0].keys())
        writer.writerow(headers)
        for chanel in items:
            writer.writerow(list(chanel.values()))

def parse():
    html_geo = get_html(URL_GEO)    
    region_links = get_regions_url(html_geo)
    
    is_use_custom_region = True if input("Use custom region? (y/n):") == "y" else False
    if is_use_custom_region:
        region_links_cut = choose_custom_region_url(region_links)
    
    for region_url in region_links_cut:
        chanels = []
        region_html = get_html(region_url)
        if region_html is None:
            print("region_html is None")
        chanels_url = get_chanels_url(region_html)
        
        print(f"Scanning {region_url} - {len(chanels_url)} chanels")
        for chanel_url in chanels_url:    
            try:
                chanel_info = {"tg_link": "https://t.me/" + chanel_url.split("@")[-1]} # telegram link is the same as url
                
                chanel_stats_html = get_html(chanel_url+URL_STAT)

                all_stats = get_all_stats(chanel_stats_html)
                while all_stats == get_empty_dict_structure():
                    wait_for_relogin()
                    chanel_stats_html = get_html(chanel_url+URL_STAT)
                    all_stats = get_all_stats(chanel_stats_html)
                
                chanel_info.update(all_stats)
                chanels.append(chanel_info)
                
                if int(chanel_info["subs_num_total"].replace(" ", "")) < SUBSCRIBERS_PARSING_LIMIT:
                    break
                
            except Exception as e:
                print(f"Exeption in {chanel_url}: {e}. Continue!")
                    
        region_name = str(region_links.index(region_url)) + " " + region_url.split("/")[-1]
        save_file(chanels, region_name)
        print(f'{len(chanels)} telegram channels saved in {region_name}.')
    
parse()