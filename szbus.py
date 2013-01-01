#coding=utf-8
from pyquery import PyQuery as pq
from base import Line,Stand
import urllib,re,json
from sync import Sync
import socket
socket.setdefaulttimeout(30)

def urlread(url,count=3):
    fails = 0
    while 1:
        try:
            if fails >= count:
                return None
            return urllib.urlopen(url).read()
        except:
            print "......连接超时，重试：%d次"%fails
            fails += 1

class BusExtractor:
    #根据站牌查询 > "途径线路","方向"，"更新时间","站距"
    url01 = "http://www.szjt.gov.cn/apts/default.aspx?StandCode=%s"
    #根据线路查询 > "站台","编号","车牌","进站时间"
    url02 = "http://www.szjt.gov.cn/apts/APTSLine.aspx?LineGuid=%s"
    #
    selector01 = "#ctl00_MainContent_Message td"

    #
    pt01 = re.compile(r"LineGuid=(.*)&LineInfo=(.+)\((.+)\)")
    pt02 = re.compile(r"StandName=(.+)$")

    lines = {}#线路集合
    stands = {}#站牌集合

    sync = Sync("bus.sqlite")

    @classmethod
    def run(cls,code):
        cls.get_lines_by_stand(code)

    @classmethod
    def get_lines_by_stand(cls,code):
        '''
        站点找线路
        '''
        #判断站点是否已经搜索过
        if code in cls.stands:
            print u"站点[%s]已经完成线路搜索"%code
            return
        else:
            print u"开始站点[%s]的搜索..."%code
            cls.stands.update({code:None})

        page = pq(cls.url01%code)

        result,size = [],0
        for td in page(cls.selector01).items('td'):
            href = td("a").attr("href")
            if href is not None:
                result.append(cls.pt01.findall(href)[0])
            else:
                result.append(td.html())
            size += 1

        lines = []
        for i in xrange(size/5):
            line = result[i*5:i*5+5]
            lines.append(line)
            
            #插入数据库
            cls.sync.append_line(*line[0])

            #线路查询站点
            cls.get_stands_by_line(line[0][0])

    @classmethod
    def get_stands_by_line(cls,guid):
        '''
        线路找站点
        '''
        #判断站点是否已经搜索过
        if guid in cls.lines:
            print u">>>线路[%s]已经完成线路搜索"%guid
            return
        else:
            print u">>>开始线路[%s]的搜索..."%guid
            cls.lines.update({guid:None})

        page = pq(cls.url02%guid)

        result,size = [],0
        for td in page(cls.selector01).items('td'):
            href = td("a").attr("href")
            if href is not None:
                result.append(cls.pt02.findall(href)[0])
            else:
                result.append(td.html())
            size += 1

        stands = []
        for i in xrange(size/4):
            stand = result[i*4:i*4+4]
            stands.append(stand)

            cls.sync.append_stand(stand[1],stand[0])

            #站点查询线路
            cls.get_lines_by_stand(stand[1])

class SzMapExtractor:
    linelist = "http://www.sz-map.com/maps/bll?m=gllb"
    standinfo = "http://www.sz-map.com/maps/p?ids=%s&m=spbi"
    lineinfo = "http://www.sz-map.com/maps/tf?ids=%s&m=sblbi"

    @classmethod
    def get_linelist(cls):
        html = urlread(cls.linelist)
        results = json.loads(html)
        lines = reduce(lambda x,y:x+y,[num.get("values") for num in results.get("number")])
        print len(lines),lines[0]
        return lines

    @classmethod
    def get_stand_info(cls,uid):
        html = urlread(cls.standinfo%uid)
        results = json.loads(html)
        if results.get("success") is False:
            return None
        else:
            return results.get("pois").get("poi")[0]

    @classmethod
    def get_line_info(cls,uid):
        html = urlread(cls.lineinfo%uid)
        results = json.loads(html)
        if results.get("success") is False:
            return None
        else:
            return results.get("busline")

if __name__ == '__main__':
    fp_lines = open("T_LINES.txt","w")
    fp_stations = open("T_STATIONS.txt","w")
    fp_line_sta = open("T_LINE_STA.txt","w")

    lines = SzMapExtractor.get_linelist()

    lsize,ssize = 0,0
    pass_stas = []

    for line in lines:
        uid = line.get("id")#获取线路编号
        lineinfo = SzMapExtractor.get_line_info(uid)
        
        # print "线路:",lineinfo.get("name"),lineinfo.get("direction")

        stations = lineinfo.get("stations")
        del lineinfo["stations"]
        values = ",".join(["'%s'"%info for info in lineinfo.values()])
        # fp_lines.write(values.encode("utf-8")+"\n")
        print ",".join(lineinfo.keys())
        
        for sta in stations:
            uid = sta.get("id")
            info = SzMapExtractor.get_stand_info(uid)
            if info is None:
                print ">>>>>>",uid
                continue
            uid = info.get("id")
            if uid not in pass_stas:
                info.update(sta)
                geom = info.get("geometry")
                del info["geometry"]
                info.update(geom)
                values = ",".join(["'%s'"%inf for inf in info.values()])
                # fp_stations.write(values.encode("utf-8")+"\n")
                print ",".join(info.keys())
                line_sta = "%s,%s\n"%(lineinfo.get("lguid"),info.get("sguid"))
                # fp_line_sta.write(line_sta)

                pass_stas.append(uid)
                ssize += 1
                if ssize%50 == 0:
                    print "进度报告:线路总计：%s(%d),站点总计:%d"%(lineinfo.get("name").encode("utf-8"),lsize,ssize)
        lsize += 1
        break