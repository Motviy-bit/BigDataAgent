from selenium import webdriver
from lxml.html import fromstring
import time
import json


def get_driver():
    agent = webdriver.Firefox(executable_path='geckodriver.exe')
    return agent


def get_article_links(source_code):
    all_article_links = source_code.xpath('///ul/li/h3/a/@href')
    links_pdf = []
    article_links = []
    for any_article_link in all_article_links:
        if '.pdf' in any_article_link:
            links_pdf.append(any_article_link)
        else:
            article_links.append(any_article_link)
    return article_links


def get_source_page(agent, link):
    agent.get(link)
    source_code = fromstring(agent.page_source)
    return source_code


def list_to_str(lst):
    strlst = [str(elem) for elem in lst]
    return ' '.join(strlst)


def fltr(lst):
    new_lst = list(map(lambda s: s.strip(), lst))
    new_lst[:] = [item for item in new_lst if item != '']
    return new_lst


def bad_symbols(my_string):
    symbols = ['\n', '/', ':', '?', '\'', '\"', '\\', '<', '>', '|']
    for i in symbols:
        my_string = my_string.replace(i, '')
    my_string = my_string.replace(' ', '_')
    if len(my_string) > 95:
        lst = my_string.split('_')
        lst_new = lst[:3]
        my_string = '_'.join([str(i) for i in lst_new])
        return my_string
    else:
        return my_string


def get_data(driver, article_links):
    for article_url in article_links:
        all_data = dict()
        item = dict()
        source_code = get_source_page(driver, article_url)
        article_title = source_code.xpath('//div[@class="ft_top_content"]/h1/text()')
        if article_title:
            article_title = list_to_str(article_title)
            article_title_save = bad_symbols(article_title)
            item['Article title'] = article_title
            item['Journal title'] = source_code.xpath('//div [@class="col-12 col-sm"]/h1/a/text()')
            item['Journal URL'] = source_code.xpath('//a [@class="text-danger"]/@href')
            author = source_code.xpath('//div [@class="ft_top_content"]/div[1]/p[1]/strong/text()')
            if author:

                item['Author'] = author
            else:
                author_1 = source_code.xpath('//div [@class="ft_top_content"]/div[1]/strong/text()')
                item['Author'] = author_1

            try:
                corr_author = source_code.xpath('//div[@class="ft_top_content"]/div[1]/dl [@class="dl-horizontal"]/dt/text()')
            except Exception:
                break
            if corr_author:
                corr_author_text = source_code.xpath('//div[@class="ft_top_content"]/div[1]/dl [@class="dl-horizontal"]/dd/text()')
                corr_author_text = fltr(corr_author_text)
                item['Corresponding Author'] = corr_author_text
            for i in range(10):
                search_abstract = source_code.xpath(f'//div[@class="ft_top_content"]/div[{i}]/h3/text()')
                search_abstract = list_to_str(search_abstract)
                if search_abstract == 'Abstract':
                    abstract_text = source_code.xpath(f'//div[@class="ft_top_content"]/div[{i+1}]/p/text()')
                    abstract_text = fltr(abstract_text)
                    item['Abstract'] = abstract_text
            # By now, Authors' names, articles, journals, journals' URLS, corresponding authors and abstract
            # must be collected. Now we are going to parse the second block with "ft_below_content" class. There are:
            # Keywords, introduction, Materials and Methods, Results and Discussion, Literature Review, and so on.
            # 2nd block will be just a list with this additional info
            additional_info = source_code.xpath('//div [@class="ft_below_content"]/child::*/text()')
            additional_info = fltr(additional_info)
            item['Additional information'] = additional_info
            all_data[article_title] = item
            with open(article_title_save + '.json', 'w', encoding='utf-8') as file:
                json.dump(all_data, file, ensure_ascii=False, indent=4)



if __name__ == '__main__':
    driver = get_driver()
    url = 'https://www.imedpub.com/scholarly/big-data-journals-articles-ppts-list.php'
    driver.get(url)
    time.sleep(7)
    SCROLL_PAUSE_TIME = 2
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    source = fromstring(driver.page_source)
    article_urls = get_article_links(source)
    get_data(driver, article_urls)
    driver.close()
