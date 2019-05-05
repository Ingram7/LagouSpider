# -*- coding: utf-8 -*-


import scrapy
from scrapy_splash import SplashRequest

from ..items import LagouspiderItem

lua_script = '''
function main(splash)
  splash.images_enabled = false
  splash:go(splash.args.url)       
  splash:wait(2)                    
  return splash:html()              
end
'''
class LagouspdSpider(scrapy.Spider):
    name = 'lagouspd'
    allowed_domains = ['lagou.com']
    start_urls = ['http://lagou.com/']

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.start_parse_job, meta={'cookiejar':'chrome'})

    def start_parse_job(self, response):

        for url_job in response.xpath('//div[contains(@class, "menu_sub dn")]//dd/a'):

            classify_href = url_job.xpath('@href').extract_first()
            classify_name = url_job.xpath('text()').extract_first()
            # print(classify_name)
            url = classify_href + '1/?filterOption=3'

            yield SplashRequest(url,
                                endpoint='execute',
                                meta={'classify_name': classify_name, 'classify_href': classify_href},
                                callback=self.parse_total_page,
                                dont_filter=True,
                                args={'lua_source': lua_script},
                                cache_args=['lua_source'])

    def parse_total_page(self, response):
        try:
            total_page = response.xpath('//*[@id="order"]/li/div[4]/div/span[2]/text()').extract()[0]
        except Exception as e:
            total_page = '0'

        classify_href = response.meta['classify_href']
        for i in range(1, int(total_page) + 1):
            url = classify_href + '{}/?filterOption=3'.format(i)

            yield SplashRequest(url,
                                endpoint='execute',
                                meta={'classify_name': response.meta['classify_name']},
                                callback=self.parse_item,
                                dont_filter=True,
                                args={'lua_source': lua_script},
                                cache_args=['lua_source'])

    def parse_item(self, response):

        for node in response.xpath('//li[@class="con_list_item default_list"]'):
            job_name = ''.join(node.xpath(
                './div[@class="list_item_top"]/div[@class="position"]/div[@class="p_top"]/a/h3/text()').extract_first()).strip()
            money = ''.join(node.xpath(
                './div[@class="list_item_top"]/div[@class="position"]/div[@class="p_bot"]/div[@class="li_b_l"]/span/text()').extract_first()).strip()
            company = ''.join(node.xpath(
                './div[@class="list_item_top"]/div[@class="company"]/div[@class="company_name"]/a/text()').extract_first()).strip()
            job_info_url = node.xpath(
                './div[@class="list_item_top"]/div[@class="position"]/div[@class="p_top"]/a/@href').extract_first()

            yield SplashRequest(url=job_info_url,
                                endpoint='execute',
                                meta={'job_name': job_name,
                                      'money': money,
                                      'company': company,
                                      'classify_name': response.meta['classify_name']},
                                callback=self.parse_info,
                                dont_filter=True,
                                args={'lua_source': lua_script},
                                cache_args=['lua_source'])

    def parse_info(self, response):
        # print(response.request.headers['User-Agent'])

        item = LagouspiderItem()
        item['job_name'] = response.meta['job_name']
        item['money'] = response.meta['money']
        item['company'] = response.meta['company']
        item['classify_name'] = response.meta['classify_name']
        item['advantage'] = ''.join(response.css('.job-advantage p::text').extract()).strip()
        item['requirements'] = ''.join(response.css('.job_bt p::text').extract()).strip()
        item['info'] = ''.join(response.css(
            '.position-head .position-content .position-content-l .job_request p').xpath('./span/text()').extract()).strip()
        print('item:' + str(item))
        yield item