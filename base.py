#coding=utf-8
from pyquery import PyQuery as pq
import re,urllib

class Line:
	'''
	公交线路
	'''
	guid_pattern = re.compile(r'LineGuid=[\w|-]+&')
	info_pattern = re.compile(r'LineInfo=.+$')
	code_pattern = re.compile(r'.+\(')
	LINES = {}

	def __init__(self,guid,info):
		self.LineGuid = guid
		self.LineInfo = info
		self.__code = None

	@property
	def code(self):
		if self.__code is None:
			self.__code = self.code_pattern.findall(self.LineInfo)[0][:-1]
		return self.__code

	def __str__(self):
		attr = ','.join(self.attr)
		print attr
		return '%s:%s'%(self.LineInfo.encode('utf-8'),attr.encode('utf-8'))

	def refresh(self):
		'''
		刷新线路状态
		'''
		pass

class Stand:
	base = "http://www.szjt.gov.cn/apts/default.aspx"

	'''
	公交站牌
	'''
	def __init__(self,name,code):
		self.StandCode = code
		self.StandName = name
		self.region = None
		self.road = None
		self.segment = None
		self.direct = None

		self.lines = None#站牌途径线路

	def get_lines(self):
		'''
		获取站牌线路
		'''
		if self.lines is None:
			self.fetch_lines()

		return self.lines

	def fetch_lines(self):
		'''
		从服务器查询站牌所属线路信息
		'''
		#urllib.quote(val.encode('GBK'))
		url = "%s?StandCode=%s&StandName=%s"%(
			self.base,
			self.StandCode,
			urllib.quote(self.StandName))

		self.lines = {}

		result = pq(url)

		for a in result('#ctl00_MainContent_Message a').items('a'):
			#APTSLine.aspx?LineGuid=fbe2afe7-aa3a-465b-947a-312bc24cdbe9&LineInfo=10(南线)
			href = a.attr('href')
			guid = Line.guid_pattern.findall(href)[0][9:-1]
			info = Line.info_pattern.findall(href)[0][9:]
			
			line = Line(guid,info)

			attr = []
			for td in a.parents('td').parents('tr').items('td'):
				attr.append(td.html())

			line.attr = attr[1:]

			self.lines[line.code] = line


	def __str__(self):
		return '%s(%s)'%(self.StandName,self.StandCode)

	def refresh(self):
		'''
		刷新站牌状态
		'''
		pass
