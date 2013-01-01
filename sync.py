#coding=utf-8
import sqlite3

class Sync:
	line_check = "select * from T_LINE where guid='%s'"
	line_insert = "insert into T_LINE (GUID,NAME,DESC) values (%s)"

	stand_check = "select * from T_STAND where id='%s'"
	stand_insert = "insert into T_STAND (ID,NAME) values (%s)"

	line_stand_check = "select * from T_LINE_STAND where line_guid='%s' and stand_id='%s'"
	line_stand_insert = "insert into T_LINE_STAND (LINE_GUID,STAND_ID) values (%s)"

	def __init__(self,db):
		self.conn = sqlite3.connect(db)

	def append_line(self,guid,name,desc):
		'''
		向数据库添加线路，添加前先判断是否已经存在
		'''
		if self.get_line(guid) is None:
			sql = self.line_insert%",".join(["'%s'"%i for i in [guid,name,desc]])
			
			cursor = self.conn.cursor()
			cursor.execute(sql)
			self.conn.commit()
			print "add line:%s(%s)"%(name,desc)

	def get_line(self,guid):
		'''
		判断线路数据是否已存在
		'''
		sql = self.line_check%guid
		r = self.conn.cursor().execute(sql).fetchone()
		return r

	def append_stand(self,uid,name):
		if self.get_stand(uid) is None:
			sql = self.stand_insert%",".join(["'%s'"%i for i in [uid,name]])

			cursor = self.conn.cursor()
			print uid,name,sql
			cursor.execute(sql)
			self.conn.commit()
			print "add stand:%s(%s)"%(name,uid)

	def get_stand(self,uid):
		sql = self.stand_check%uid
		r = self.conn.cursor().execute(sql).fetchone()
		return r

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