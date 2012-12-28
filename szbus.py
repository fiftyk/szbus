#coding=utf-8
from pyquery import PyQuery as pq
from base import Line,Stand
import urllib,re,sqlite3

class Sync:
	line_check = "select * from T_LINE where guid='%s'"
	line_insert = "insert into T_LINE (GUID,NAME,DESC) values (%s)"

	stand_check = "select * from T_STAND where id='%s'"
	stand_insert = "insert into T_STAND (NAME,ID) values (%s)"

	line_stand_check = "select * from T_LINE_STAND where line_guid='%s' and stand_id='%s'"
	line_stand_insert = "insert into T_LINE_STAND (LINE_GUID,STAND_ID) values (%s)"

	def __init__(self,db):
		self.conn = sqlite3.connect(db)

	def append_line(self,guid,name,desc):
		'''
		向数据库添加线路，添加前先判断是否已经存在
		'''
		if self.check_line(guid,name,desc) is False:
			sql = self.line_insert%",".join(["'%s'"%i for i in [guid,name,desc]])
			
			cursor = self.conn.cursor()
			cursor.execute(sql)
			self.conn.commit()
			print "add line:%s(%s)"%(name,desc)

	def check_line(self,guid,name,desc):
		'''
		判断线路数据是否已存在
		'''
		sql = self.line_check%guid
		r = self.conn.cursor().execute(sql).fetchone()
		if r is not None:
			print "exist line:%s(%s)"%(name,desc)
			return True
		return False

	def append_stand(self,uid,name):
		if self.check_stand(uid,name) is False:
			sql = self.stand_insert%",".join(["'%s'"%i for i in [uid,name]])

			cursor = self.conn.cursor()
			cursor.execute(sql)
			self.conn.commit()
			print "add stand:%s(%s)"%(name,uid)

	def check_stand(self,name,uid):
		sql = self.stand_check%uid
		r = self.conn.cursor().execute(sql).fetchone()
		if r is not None:
			print "exist stand:%s(%s)"%(name,uid)
			return True
		return False

	def append_line_stand(self,guid,uid):
		if self.check_line_stand(guid,uid) is False:
			sql = self.line_stand_insert%",".join(["'%s'"%i for i in [guid,uid]])

			cursor = self.conn.cursor()
			cursor.execute(sql)
			self.conn.commit()
			print "add line_stand:%s(%s)"%(guid,uid)

	def check_line_stand(self,guid,uid):
		sql = self.line_stand_check%(guid,uid)
		r = self.conn.cursor().execute(sql).fetchone()
		if r is not None:
			print "exist line_stand:%s(%s)"%(guid,uid)
			return True
		return False

param01 = {
	"__EVENTVALIDATION":"/wEWAwKi6d2xDAL88Oh8AqX89aoKpYwmbFse8btxSRSeF1SjYe7FDBo=",
	"__VIEWSTATE":"/wEPDwUJNDk3MjU2MjgyD2QWAmYPZBYCAgMPZBYCAgEPZBYCAgYPDxYCHgdWaXNpYmxlaGRkZLjIYtHjVvVwuQEcmZdla0sXvFjO",
	"ctl00$MainContent$LineName":"[line]",
	"ctl00$MainContent$SearchLine":"搜索"
}

param02 = "LineGuid=%s"

domain = "http://www.szjt.gov.cn/apts/"
APTSLine = "APTSLine.aspx"
resultTable = "#ctl00_MainContent_Message a"
pattern01 = re.compile(r"LineGuid=([\w|-]+)&LineInfo=(.+)\((.+)\)")
pattern02 = re.compile(r"StandName=(.*)")

def query_lines(line,sync=None):
	param = "&".join(["%s=%s"%(k,v) for k,v in param01.items()]).replace("[line]",line)
	url = "%s%s?%s"%(domain,APTSLine,param)
	page = pq(url)

	for anchor in page(resultTable).items('a'):
		href = anchor.attr("href")
		guid,line,desc = pattern01.findall(href)[0]
		if sync is not None:
			sync.append_line(guid,line,desc)

def fetch_line(line,sync=None,on=False):
	url = "%s%s?%s"%(domain,APTSLine,param02%line)
	
	print url
	page = pq(url)

	result,size = [],0
	for td in page("#ctl00_MainContent_Message td").items('td'):
		href = td("a").attr("href")
		if href is not None:
			result.append(pattern02.findall(href)[0])
		else:
			result.append(td.html())
		size += 1

	result = [result[i*4:i*4+4] for i in xrange(size/4)]

	if sync is not None:
		for i in result:
			sync.append_stand(*i[:2])
			sync.append_line_stand(line,i[1])

	if on is False:
		return result
	else:
		return [i for i in result if i[-1] is not None]
		
if __name__ == '__main__':
	sync = Sync('bus.sqlite')
	query_lines("10",sync)
	info = fetch_line("2f3022aa-d016-455f-8d42-e96fc113ec41",sync,True)
	print info