#!/usr/bin/env python


mssql = {'host': 'dbhost',
         'user': 'dbuser',
         'passwd': 'dbPwd',
         'db': 'db'}

mysql = {'host': 'morfisem.mysql.pythonanywhere-services.com',
         'user': 'morfisem',
         'passwd': 'Flask4Ever!',
         'db': '$fikadb'}

postgresql = {'host': 'packy.db.elephantsql.com',
         'user': 'osulvond',
         'passwd': '5DcllwBbzzR9FuWVu6vVsx68Ghto-8dd',
         'db': 'osulvond'}




mssqlConfig = "mssql+pyodbc://{}:{}@{}:1433/{}?driver=SQL+Server+Native+Client+10.0".format(mssql['user'], mssql['passwd'], mssql['host'], mssql['db'])
postgresqlConfig = "postgresql+psycopg2://{}:{}@{}/{}".format(postgresql['user'], postgresql['passwd'], postgresql['host'], postgresql['db'])
#sqliteConfig = "sqlite:////playground//code//fika-mvp//FreindlyServer//data.db"
sqliteConfig = "sqlite:///data.db"
mysqlConfig = "mysql://{}:{}@{}:3306/{}".format(mysql['user'], mysql['passwd'], mysql['host'], mysql['db'])
