#coding=utf-8
from base import Line,Stand
import urllib,re,json
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