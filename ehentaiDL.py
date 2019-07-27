import requests
from lxml import etree
import time

header = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    'DNT': '1',
    'Referer': 'https://e-hentai.org/',

    'Cookie': "你的COOKIE"
}
payload ={
    'dltype':'org',
    'dlcheck':'Download Original Archive',
}
# 本脚本未经过大量测试，可能会Ban IP 禁止访问24小时
# 将你要下的本子链接放在queue.txt中，success.txt为输出的本子zip下载链接
fqueue = open('queue.txt')
fsuccess = open('success.txt','w+')
ffailed = open('failed.txt','w+')

progress=0
for nextGallery in fqueue:
    progress+=1
    print("progress:%d "%progress)
    # 抓取作品页面
    nextGallery = nextGallery[:-1]
    time.sleep(1.5)
    header['Referer'] = 'https://e-hentai.org/'
    r = requests.get(nextGallery,headers = header)
    if r.status_code != 200:
        ffailed.write("10:%s\n"%nextGallery)
        print("failed:10")
        continue
    # 尝试获取存档请求链接
    html = etree.HTML(r.text)
    eleValue = html.xpath('//*[@id="gd5"]/p[2]/a/@onclick')
    if len(eleValue) == 0:
        ffailed.write("20:%s\n"%nextGallery)
        print("failed:20")
        continue
    archiveReqURL = eleValue[0][14:-10]
    # 请求下载存档链接
    time.sleep(1.5)
    header['Referer'] = nextGallery
    ar = requests.post(archiveReqURL, data = payload,headers = header)
    if ar.status_code != 200:
        ffailed.write("30:%s\n"%nextGallery)
        print("failed:30")
        continue
    # 抓取下载地址
    ahtml = etree.HTML(ar.text)
    eleValue = ahtml.xpath('//*[@id="continue"]/a/@href')
    if len(eleValue) == 0:
        ffailed.write("40:%s\n"%nextGallery)
        print("failed:40")
        continue
    fsuccess.write("%s\n"%eleValue[0])
    print("Success")

print("Done.")
fqueue.close()
fsuccess.close()
ffailed.close()
