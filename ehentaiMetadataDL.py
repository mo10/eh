import requests
from lxml import etree
import time
import html
import json

header = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    'DNT': '1',
    'Referer': 'https://e-hentai.org/',

    'Cookie': "你的Cookie"
}
'''
将你要爬的链接放进queue.txt，一行一个链接
爬失败的链接会放进failed.txt中，格式为:
10:<http返回值>:链接     请求错误，详情参见http返回值
20:链接                 内容解析错误，可能是返回的页面内容不对，详情请访问对应链接

在脚本目录新建文件夹，命名为g
该文件夹用于存储爬下来的metadata
metadata存储为JSON格式，格式为:
{
  "title"       : 字符串,标题
  "subtitle"    : 字符串,原标题/小标题等，没有会显示No Data(数据不存在均显示为No Data，下同)
  "category"    : 字符串,分类:non-h,Doujinshi等
  "posted_time" : 字符串,发布时间
  "uploader"    : 字符串,上传者
  "language"    : 字符串,语言
  "favorited"   : 整数,添加收藏的人数
  "rating"      : 整数,评分人数
  "average"     : 浮点数,平均得分
  "tags"        : [] 数组,例:["language:chinese", "language:translated", "parody:nier automata", "character:2b"]
  "comments"    : [] 数组,例:
    [
      {
        "posted_time" : 字符串,发表时间
        "uploader"    : 字符串,发表者
        "is_uploader" : 布尔型,是否为上传者
        "score"       : 整数,得分
        "content"     : 字符串,评论内容,注意:多行评论和内附链接评论会出现html标签,如<br/> <a>
      }
    ]
}
'''
fqueue = open('queue.txt')
ffailed = open('failed.txt','w+')

def getFirstTextByXpath(htmlNode,xpathStr):
    text = htmlNode.xpath(xpathStr)
    if len(text) == 0:
        return 'No Data'
    return text[0]

def getInnerHTMLByXpath(htmlNode,xpathStr):
    nodes = htmlNode.xpath(xpathStr)
    finalStr = ""
    for node in nodes:
        # 文本类型
        if type(node) == etree._ElementUnicodeResult:
            finalStr += node
        elif type(node) == etree._Element:
            finalStr += etree.tostring(node).decode('utf-8')
    return html.unescape(finalStr)

progress=0
for nextGallery in fqueue:
    matedata={}
    progress+=1
    print("progress:%d"%progress,end=' ')
    # 抓取作品页面
    nextGallery = nextGallery[:-1]
    time.sleep(1.5)
    header['Referer'] = 'https://e-hentai.org/'
    r = requests.get(nextGallery,headers = header)
    if r.status_code != 200:
        ffailed.write("10:%d:%s\n"%(r.status_code,nextGallery))
        print("failed:10:%d:%s"%(r.status_code,nextGallery))
        continue

    # 解析HTML
    htmlNode = etree.HTML(r.text)

    # 获取标题
    title = htmlNode.xpath('//*[@id="gn"]/text()')
    if len(title) == 0:
        ffailed.write("20:%s\n"%(nextGallery))
        print("failed:20:%s"%(nextGallery))
        continue

    # 获取Tag
    tags = htmlNode.xpath('//*[@id="taglist"]//a/@onclick') 
    for i in range(len(tags)):
        tags[i] = tags[i][23:-7] # 截取tag，抛弃js字串

    # 获取标题
    matedata['title']       = title[0]
    # 获取Tag
    matedata['tags']        = tags
    # 获取小标题
    matedata['subtitle']    = getFirstTextByXpath(htmlNode,'//*[@id="gj"]/text()')
    # 获取分类
    matedata['category']    = getFirstTextByXpath(htmlNode,'//*[@id="gdc"]/div/text()')
    # 获取发布时间
    matedata['posted_time'] = getFirstTextByXpath(htmlNode,'//*[@id="gdd"]//tr[1]/td[2]/text()')
    # 获取发布者
    matedata['uploader']    = getFirstTextByXpath(htmlNode,'//*[@id="gdn"]/a[1]/text()')
    # 获取语言
    matedata['language']    = getFirstTextByXpath(htmlNode,'//*[@id="gdd"]//tr[4]/td[2]/text()')[:-2]
    # 获取收藏数
    matedata['favorited']   = int(getFirstTextByXpath(htmlNode,'//*[@id="favcount"]/text()')[:-6])
    # 获取评分数
    matedata['rating']      = int(getFirstTextByXpath(htmlNode,'//*[@id="rating_count"]/text()'))
    # 获取评分
    matedata['average']     = float(getFirstTextByXpath(htmlNode,'//*[@id="rating_label"]/text()')[9:])
    
    # 解析评论
    comments = []
    commentEles = htmlNode.xpath('//*[@id="cdiv"]/div[@class="c1"]')
    for commentEle in commentEles:
        comment = {}
        # 获取发布时间
        comment['posted_time']  = getFirstTextByXpath(commentEle,'div[@class="c2"]/div[@class="c3"]/text()[1]')[10:-7]
        # 获取发布者
        comment['uploader']     = getFirstTextByXpath(commentEle,'div[@class="c2"]/div[@class="c3"]/a[1]/text()')
        # 该评论是否为上传者发布
        comment['is_uploader']  = True
        comment['score']        = 0
        # 获取评分
        score = getFirstTextByXpath(commentEle,'div[@class="c2"]/div[@class="c5 nosel"]/span/text()')
        # 无得分数据则为上传者发布
        if score != 'No Data':
            comment['is_uploader'] = False
            # 获取评分
            comment['score']        = int(score)
        # 获取评论内容
        comment['content']      = getInnerHTMLByXpath(commentEle,'div[@class="c6"]/node()')
        # 添加评论
        comments.append(comment)
    # 添加评论
    matedata['comments'] = comments

    matedataJ = json.dumps(matedata)

    outputFilename = nextGallery[23:-1].replace("/", "-") # 123456/123abcdef to 123456-123abcdef
    fd = open('./g/%s.json'%(outputFilename),'w')
    fd.write(matedataJ)
    fd.close()

    print("Success")

print("Done.")
fqueue.close()
ffailed.close()
