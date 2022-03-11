import sqlite3
import os
import time
import random


DB_PATH = os.path.expanduser('~/.hoshino/kyabetsu.db')
# DB_PATH = os.path.expanduser('/Users/tyxiong/Documents/demo/kyabetsu/test/kyabetsu.db')


def getSeed():
    pattern = random.randint(0, 3)
    seed = random.randint(0, 2**32 - 1)

    return pattern, seed


class KISDao:

    def __init__(self, user_id):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._create_table()
        if self._connect().execute("SELECT * FROM KYABETSU_INFO WHERE UID=?",(user_id,)).fetchone()==None:
            self._insert(user_id)
        else:
            old_year_week = int(self._find_by_id(user_id, 0)[0])
            year_week = int(time.strftime("%Y%U"))

            if year_week != old_year_week:
                freshNum = self._find_by_id(user_id, 2)[0]
                rottenNum = self._find_by_id(user_id, 3)[0]
                freshNum = int(int(freshNum) / 100) + (1 if int(freshNum) % 100 != 0 else 0)
                rottenNum = int(freshNum) + int(rottenNum)
                self._update_by_id(user_id, 0, 0, rottenNum)


    def _connect(self):
        return sqlite3.connect(DB_PATH)


    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS KYABETSU_INFO
                          (UID INT PRIMARY KEY    NOT NULL,
                           YEARWEEK       INTEGER    NOT NULL,
                           PATTERN       TINYINT    NOT NULL,
                           SEED       INTEGER    NOT NULL,
                           FRESH_NUM       TEXT    NOT NULL,
                           ROTTEN_NUM       TEXT    NOT NULL);''')
        except:
            raise Exception('创建大头菜信息表发生错误')


    def _insert(self, user_id):
        try:
            year_week = time.strftime("%Y%U")
            pattern, seed = getSeed()
            conn = self._connect()
            conn.execute("INSERT INTO KYABETSU_INFO (UID,YEARWEEK,PATTERN,SEED,FRESH_NUM,ROTTEN_NUM) \
                                VALUES (?, ?, ?, ?, ?, ?)", (
                                    user_id, year_week, pattern, seed, 0, 0))
            conn.commit()
        except (sqlite3.DatabaseError):
            raise Exception('初始化玩家信息发生错误') 
 

    # type：0为时间过期，重置大头菜数量以及更新时间种子
    # type：1为交易行为，买入或者卖出
    def _update_by_id(self, user_id, type, freshNum=0, rottenNum=0):
        try:
            conn = self._connect()
            r = conn.execute("SELECT * FROM KYABETSU_INFO WHERE UID=?",(user_id,)).fetchone()
            if r!=None:
                if type == 0:
                    year_week = time.strftime("%Y%U")
                    pattern, seed = getSeed()
                    conn.execute("UPDATE KYABETSU_INFO SET YEARWEEK=?, PATTERN=?, SEED=?, FRESH_NUM=?, ROTTEN_NUM=?  WHERE UID=?",
                                    (year_week, pattern, seed, freshNum, rottenNum, user_id))
                else:
                    conn.execute("UPDATE KYABETSU_INFO SET FRESH_NUM=?  WHERE UID=?",
                                    (freshNum, user_id))
                conn.commit()
            else:
                raise Exception('更新大头菜信息发生错误')
        except Exception as e:
            raise Exception(e)


    # type：0为年周，1为种子，2为新鲜大头菜数量，3为烂菜数量
    def _find_by_id(self, user_id, type=None):
        try:
            keyword = '*'
            if type == 0:
                keyword = 'YEARWEEK'
            if type == 1:
                keyword = 'PATTERN,SEED'
            if type == 2:
                keyword = 'FRESH_NUM'
            if type == 3:
                keyword = 'ROTTEN_NUM'
            # getWhat = ''
            # if type == 0:
            #     getWhat = ''
            r = self._connect().execute("SELECT " + keyword + " FROM KYABETSU_INFO WHERE UID=?",(user_id,)).fetchone()
            return r
        except:
            raise Exception('获取信息发生错误')