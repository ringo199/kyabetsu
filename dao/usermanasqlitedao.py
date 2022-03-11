import sqlite3
import os

DB_PATH = os.path.expanduser('~/.hoshino/kyabetsu.db')
# DB_PATH = os.path.expanduser('/Users/tyxiong/Documents/demo/kyabetsu/test/kyabetsu.db')

class UMSDao:

    def __init__(self, user_id):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._create_table()
        self.isInit = self._connect().execute("SELECT * FROM USER_MANA WHERE UID=?",(user_id,)).fetchone()!=None
            # raise Exception('还未初始化玛那，请开户后再进行操作')
            # self._insert(user_id, init_money)


    def _connect(self):
        return sqlite3.connect(DB_PATH)


    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS USER_MANA
                          (UID INT PRIMARY KEY    NOT NULL,
                           MANA       TEXT    NOT NULL);''')
        except:
            raise Exception('创建mana表发生错误')


    def _insert(self, user_id, init_mana):
        try:
            conn = self._connect()
            conn.execute("INSERT INTO USER_MANA (UID,MANA) \
                                VALUES (?, ?)", (user_id, init_mana))
            conn.commit()
        except (sqlite3.DatabaseError):
            raise Exception('初始化玩家mana发生错误') 
 
           
    def _update_by_id(self, user_id, mana):
        try:
            conn = self._connect()
            r = conn.execute("SELECT * FROM USER_MANA WHERE UID=?",(user_id,)).fetchone()
            if r!=None:
                conn.execute("UPDATE USER_MANA SET MANA=? WHERE UID=?",(mana, user_id))
                conn.commit()
            else:
                raise Exception('更新玩家mana发生错误')
        except:
            raise Exception('更新玩家mana发生错误')


    def _find_by_id(self, user_id):
        try:
            r = self._connect().execute("SELECT MANA FROM USER_MANA WHERE UID=?",(user_id,)).fetchone()        
            return r[0]
        except:
            raise Exception('获取mana发生错误')