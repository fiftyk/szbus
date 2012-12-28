#coding=utf-8
from pyquery import PyQuery as pq
import urllib,re

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

class SzBusTool:
	b = "http://www.szjt.gov.cn/apts/%s"
	line_base = b%"APTSLine.aspx"#线路
	stand_base = b%"default.aspx"#电子站牌

	selector01 = "form input" 

	STANDS = {}#站点信息缓存

	def __init__(self):
		self.pq = pq(self.line_base)
		self.param01 = None#第一步查询时的参数
		self.url01 = {}#第一步查询时的URL<line_name:line_query_url>

		self.stand_param = None#站牌查询参数

	def get_stand(self,name,code):
		#从缓存中获取站牌
		stands = self.STANDS.get(name)
		if stands is not None:
			if code is None:
				return stands
			else:
				stand = stands.get(code)
				if stand is not None:
					return [stand]

		#如果缓存中还没有该name的stand，从服务器查询
		self.fetch_stand(name)

		return self.get_stand(name,code)

	def fetch_stand(self,name):
		'''
		从服务器查询该name的stand信息
		'''
		self.fetch_stand_param()

		params = "&".join(self.stand_param[:-1]).replace('[%s]'%'Code','')\
			.replace('[%s]'%'Name',urllib.quote(name))

		#拼接该name站牌的请求
		url = "%s?%s"%(self.stand_base,params)
		
		# print url

		stands = {}#用于存储相同站点不同方向

		for a in pq(url)('#ctl00_MainContent_Message a').items('a'):
			#default.aspx?StandCode=CSM&StandName=三元新村
			params = a.attr('href').replace("default.aspx?","").split('&')
			code,name = [param.split('=')[-1].encode('utf-8') for param in params]
			#此处还可以获取站牌的 "所在行政区"	"所在道路"	"所在路段"	"站点方位"等信息

			#创建Stand实例，并缓存
			stand = Stand(name,code)
			stands[code] = stand

		self.STANDS[name] = stands

	def fetch_stand_param(self):
		'''
		获取stand查询参数
		'''
		if self.stand_param is None:
			self.stand_param = []
			for item in pq(self.stand_base)(self.selector01).items('input'):
				key,val,t = item.attr('name'),item.val(),item.attr('type')
				if t == 'text':
					if key.endswith('Code'):
						val = '[%s]'%'Code'
					if key.endswith('Name'):
						val = '[%s]'%'Name'
				if t == 'submit' or t == 'hidden':
					val = urllib.quote(val.encode('GBK'))
				self.stand_param.append('%s=%s'%(key,val))

	def query_stand(self,name,code=None):
		'''
		查询站牌
		@param {str} 站牌名称
		@param {str} 站牌编号
		'''
		stands = self.get_stand(name,code)
		return stands

	def query_step_1(self,line_name):
		'''
		根据线路名称查询 step1
		@param {str} line_name 线路名称
		'''
		url = self.__get_url01(line_name)

		print url

		print u"获取结果line请求列表"

		t = pq(url)
		for a in t("a").items('a'):
			print a.attr('href')
	
	def __get_url01(self,line_name):
		'''
		生成第一步的URL
		'''
		self.__get_param01()

		url = self.url01.get(line_name)

		if url is None:
			param01 = "&".join(self.param01).replace('[line_name]',line_name)
			self.url01[line_name] = "%s?%s"%(self.line_base,param01)

		return self.url01[line_name]

	def __get_param01(self):
		'''
		生成第一步的param
		'''
		if self.param01 is None:
			self.param01 = []
			for i in self.pq(self.selector01).items('input'):
				key,val = i.attr('name'),i.val()
				if val is None:
					val = "[line_name]"#%s 格式化用不上
				else:
					val = urllib.quote(i.val().encode('GBK'))
				self.param01.append('%s=%s'%(key,val))
		
if __name__ == '__main__':
	# SzBusTool().query_step_1("39")
	import sys
	name = sys.argv[1]
	line = sys.argv[2].decode('utf-8')

	#按站牌名称查找站点
	stands = SzBusTool().query_stand(name)
	
	# print "站点:"
	print stands

	print "线路信息"

	lines = stands.values()[0].get_lines()
	
	print lines.get(line)
	lines = stands.values()[1].get_lines()
	print lines.get(line)

