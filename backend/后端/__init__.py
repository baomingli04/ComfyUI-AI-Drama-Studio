"""项目包：兼容层——把 PyMySQL 当作 MySQLdb 使用。"""
import pymysql

pymysql.install_as_MySQLdb()
