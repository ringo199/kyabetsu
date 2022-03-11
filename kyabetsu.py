from .util import *
from hoshino import Service, util
from hoshino import util as hutil
from hoshino.typing import CQEvent
from .dao.usermanasqlitedao import UMSDao
from .dao.kyabetsuinfosqlitedao import KISDao
from matplotlib import pyplot as plt
from nonebot import MessageSegment as ms
from hoshino.util import DailyNumberLimiter

import math
import time

sv = Service('kyabetsu', bundle='大头菜', help_='''
Kyabetsu大头菜模拟器(韭菜模拟器)（划掉）v0.0.4
========
本模拟器为最初始版本，使用了集合啦！动物森友会的大头菜价格模型
周日上午5点到12点可以买入大头菜
之后周一到周六商店营业期间8:00-22：00可以询问大头菜价格，上午下午价格不同，分界线为12：00
※本周六如果有剩余大头菜没卖出去那么周日会坏掉，此时只能以一元一组（一般是100棵）的价格卖出
※bug会有很多，出现问题可以来杯咖啡
========
初始化mana
查看当前mana
查看大头菜价格
买入大头菜 <数量>
卖出大头菜 <数量>
买入全部
卖出全部
'''.strip())

lmt = DailyNumberLimiter(1)


@sv.on_fullmatch(('初始化mana'))
async def initMana(bot, ev: CQEvent):
    try:
        db = UMSDao(ev.user_id)
        if db.isInit == False:
            init_money = '10000'
            db._insert(ev.user_id, init_money)
            await bot.send(ev, f'mana已初始化，现在您拥有{init_money}mana可以用来进行大头菜交易!', at_sender=True)
        else:
            await bot.send(ev, 'mana已经初始化了', at_sender=True)
    except Exception as e:
        print(e)
        await bot.send(ev, 'mana初始化失败，请联系维护组进行调教', at_sender=True)


@sv.on_fullmatch(('kbt签到', '大头菜签到'))
async def give_mana(bot, ev: CQEvent):
    try:
        uid = ev.user_id
        if not lmt.check(uid):
            await bot.send(ev, '今天已经领取过mana了', at_sender=True)
            return
        db = UMSDao(uid)
        mana = 1000
        storemana = int(db._find_by_id(uid))
        storemana += mana
        db._update_by_id(uid, storemana)
        lmt.increase(uid)
        await bot.send(ev, f'签到成功，领取了{mana}，当前mana数为{storemana}', at_sender=True)
    except Exception as e:
        await bot.send(ev, f'查询失败，请联系维护组进行调教{e}', at_sender=True)


@sv.on_fullmatch(('查看当前mana', '查看当前玛那', '看看还有多少钱'))
async def viewMana(bot, ev: CQEvent):
    try:
        db = UMSDao(ev.user_id)
        mana = db._find_by_id(ev.user_id)
        await bot.send(ev, f'当前mana的数量为：{mana}', at_sender=True)
        print(f'当前mana的数量为：{mana}')
    except:
        await bot.send(ev, '查询失败，请联系维护组进行调教', at_sender=True)


# type：0为年周，1为种子，2为新鲜大头菜数量，3为烂菜数量
@sv.on_fullmatch(('查看当前大头菜', '查询当前大头菜', '查看大头菜', '查询大头菜', '看看还有多少菜', '看看有多少菜', '看看菜'))
async def viewKyabetsu(bot, ev: CQEvent):
    try:
        db = KISDao(ev.user_id)
        freshNum = db._find_by_id(ev.user_id, 2)[0]
        rottenNum = db._find_by_id(ev.user_id, 3)[0]
        await bot.send(ev, f'\n您当前的新鲜大头菜有{freshNum}颗，\n腐烂的大头菜有{rottenNum}颗', at_sender=True)
    except:
        await bot.send(ev, '查询失败，请联系维护组进行调教', at_sender=True)


@sv.on_prefix(('查看大头菜价格', '查看价格', '查看当前价格', '看看现在多少钱', '看看价格', '看看菜价', '查看菜价'))
async def viewPrice(bot, ev: CQEvent):
    try:
        uid = ev.user_id
        for m in ev.message:
            if m.type == 'at' and m.data['qq'] != 'all':
                uid = int(m.data['qq'])
        db = KISDao(uid)
        pattern, seed = db._find_by_id(uid, 1)
        freshNum = db._find_by_id(ev.user_id, 2)[0]
        price, isBuy, isDisable, isShopClose = getCurPrice(pattern, seed)
        msg = f'当前的价格为:{price}'
        if int(freshNum) == 0:
            msg += '，不过你手里没有大头菜哦～'
        else:
            msg += f'，你有{freshNum}棵大头菜可以进行售卖'
        if isShopClose:
            msg = '商店关门了，请等待营业时间8:00 - 22:00再来光顾'
        if isDisable:
            msg = '当前时间不可买入和卖出'
        if isBuy:
            msg = f'今天曹卖来了，可以以{price}的价格购买大头菜，曹卖中午12点就走，要抓紧时间哦～'
        await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '查询失败，请联系维护组进行调教', at_sender=True)


@sv.on_prefix(('买入大头菜', '买入', '购买'))
async def buyKyabetsu(bot, ev: CQEvent):
    try:
        num = ev.message.extract_plain_text()
        num = f'{num}'.strip()
        if not num:
            await bot.send(ev, '请填写买入数量', at_sender=True)
            return
        if num.isdigit():
            num = math.floor(int(num))
        else:
            await bot.send(ev, '请填写数字', at_sender=True)
            return

        umdb = UMSDao(ev.user_id)
        if umdb.isInit == False:
            await bot.send(ev, '请初始化mana再尝试交易', at_sender=True)
            return
        # is_Friend = False
        uid = ev.user_id
        for m in ev.message:
            if m.type == 'at' and m.data['qq'] != 'all':
                uid = int(m.data['qq'])
                # is_Friend = True
        kidb = KISDao(uid)
        pattern, seed = kidb._find_by_id(uid, 1)
        price, isBuy, isDisable, isShopClose = getCurPrice(pattern, seed)
        if isBuy:
            mana = int(price) * num
            storemana = int(umdb._find_by_id(ev.user_id))
            if storemana < mana:
                msg = '你的mana不够买这些菜'
            else:
                surplusmana = storemana - mana
                storenum = int(kidb._find_by_id(ev.user_id, 2)[0])
                newnum = storenum + num
                kidb._update_by_id(ev.user_id, 1, newnum)
                umdb._update_by_id(ev.user_id, surplusmana)
                msg = f'花费了{mana}mana购买了{num}颗大头菜，大头菜现数量为{newnum}，mana剩余{surplusmana}'

        else:
            msg = '当前时间不可买入'

        await bot.send(ev, msg, at_sender=True)
    except:
        await bot.send(ev, '买入失败，请联系维护组进行调教', at_sender=True)


@sv.on_fullmatch(('all in', 'allin', '老子全买了', '买入全部'))
async def buyAllKyabetsu(bot, ev: CQEvent):
    try:
        umdb = UMSDao(ev.user_id)
        if umdb.isInit == False:
            await bot.send(ev, '请初始化mana再尝试交易', at_sender=True)
            return
        uid = ev.user_id
        for m in ev.message:
            if m.type == 'at' and m.data['qq'] != 'all':
                uid = int(m.data['qq'])
        kidb = KISDao(uid)
        pattern, seed = kidb._find_by_id(uid, 1)
        price, isBuy, isDisable, isShopClose = getCurPrice(pattern, seed)
        if isBuy:
            storemana = int(umdb._find_by_id(ev.user_id))
            num = math.floor(storemana / int(price))
            mana = int(price) * num
            surplusmana = storemana - mana
            storenum = int(kidb._find_by_id(ev.user_id, 2)[0])
            newnum = storenum + num
            kidb._update_by_id(ev.user_id, 1, newnum)
            umdb._update_by_id(ev.user_id, surplusmana)
            msg = f'花费了{mana}mana购买了{num}颗大头菜，大头菜现数量为{newnum}，mana剩余{surplusmana}'

        else:
            msg = '当前时间不可买入'

        await bot.send(ev, msg, at_sender=True)
    except:
        await bot.send(ev, '买入失败，请联系维护组进行调教', at_sender=True)


@sv.on_prefix(('卖出大头菜', '卖出', '出售'))
async def soldKyabetsu(bot, ev: CQEvent):
    try:
        num = ev.message.extract_plain_text()
        num = f'{num}'.strip()
        if not num:
            await bot.send(ev, '请填写卖出数量', at_sender=True)
            return
        if num.isdigit():
            num = math.floor(int(num))
        else:
            await bot.send(ev, '请填写数字', at_sender=True)
            return
        umdb = UMSDao(ev.user_id)
        if umdb.isInit == False:
            await bot.send(ev, '请初始化mana再尝试交易', at_sender=True)
            return
        uid = ev.user_id
        for m in ev.message:
            if m.type == 'at' and m.data['qq'] != 'all':
                uid = int(m.data['qq'])
        kidb = KISDao(uid)

        storenum = int(kidb._find_by_id(ev.user_id, 2)[0])
        if storenum < num:
            await bot.send(ev, '卖出的数量大于持有数', at_sender=True)
            return
        pattern, seed = kidb._find_by_id(uid, 1)
        price, isBuy, isDisable, isShopClose = getCurPrice(pattern, seed)

        if isShopClose:
            bot.send(ev, '商店关门了，请等待营业时间8:00 - 22:00再来光顾', at_sender=True)
            return
        if not isBuy and not isDisable:
            mana = int(price) * num
            storemana = int(umdb._find_by_id(ev.user_id))
            surplusmana = storemana + mana
            newnum = storenum - num
            kidb._update_by_id(ev.user_id, 1, newnum)
            umdb._update_by_id(ev.user_id, surplusmana)
            msg = f'卖出了{num}棵大头菜获取了{mana}mana，mana现拥有{surplusmana}，大头菜剩余数量为{newnum}'
        else:
            msg = '当前时间不可卖出'
        await bot.send(ev, msg, at_sender=True)
    except:
        await bot.send(ev, '查询失败，请联系维护组进行调教', at_sender=True)


@sv.on_prefix(('抛了', '老子全卖了', '卖出全部'))
async def soldAllKyabetsu(bot, ev: CQEvent):
    try:
        umdb = UMSDao(ev.user_id)
        if umdb.isInit == False:
            await bot.send(ev, '请初始化mana再尝试交易', at_sender=True)
            return
        uid = ev.user_id
        for m in ev.message:
            if m.type == 'at' and m.data['qq'] != 'all':
                uid = int(m.data['qq'])
        kidb = KISDao(uid)

        storenum = int(kidb._find_by_id(ev.user_id, 2)[0])
        pattern, seed = kidb._find_by_id(uid, 1)
        price, isBuy, isDisable, isShopClose = getCurPrice(pattern, seed)

        if isShopClose:
            bot.send(ev, '商店关门了，请等待营业时间8:00 - 22:00再来光顾', at_sender=True)
            return
        if not isBuy and not isDisable:
            mana = int(price) * storenum
            storemana = int(umdb._find_by_id(ev.user_id))
            newmana = storemana + mana
            newnum = 0
            kidb._update_by_id(ev.user_id, 1, newnum)
            umdb._update_by_id(ev.user_id, newmana)
            msg = f'卖出了{storenum}棵大头菜获取了{mana}mana，mana现拥有{newmana}，大头菜剩余数量为{newnum}'
        else:
            msg = '当前时间不可卖出'
        await bot.send(ev, msg, at_sender=True)
    except:
        await bot.send(ev, '查询失败，请联系维护组进行调教', at_sender=True)

days_list = ["日", "一", "二", "三", "四", "五", "六"]
@sv.on_prefix(('查看大头菜趋势'))
async def viewPlot(bot, ev: CQEvent):
    try:
        db = KISDao(ev.user_id)
        year_week = db._find_by_id(ev.user_id, 0)[0]
        pattern, seed = db._find_by_id(ev.user_id, 1)
        year = str(year_week)[0:4]
        week = str(year_week)[4:]
        price = getPrice(pattern, seed)
        days_index = getCurType()
        if days_index == 0:
            await bot.send(ev, '商店还没卖，没有价格可查询', at_sender=True)
            return
        else:
            price = price[0 : days_index + 1]
        x, y = {}, {}
        buyPrice = ''
        for key, value in enumerate(price):
            days = days_list[math.floor((key + 1) / 2)]
            time = '上午' if math.floor(key % 2) == 1 else '下午'
            if key != 0:
                x[key - 1] = f'周{days}{time}'
                y[key - 1] = int(value)
            else:
                buyPrice = value

        #设置中文字体
        plt.rcParams['font.family'] = ['Microsoft YaHei']
        plt.figure(figsize=(10, 4.5))
        plt.title(f"{year}年第{week}周大头菜价格趋势，买入价为{buyPrice}")
        plt.xlabel("时间")
        plt.ylabel("价格")
        plt.plot(list(x.values()), list(y.values()))
        pic = hutil.fig2b64(plt)
        plt.close()
        msg = f"{ms.image(pic)}"
        await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, f'查询失败，请联系维护组进行调教, {e}', at_sender=True)


# pattern, seed = getSeed()
# print('模式：' + str(pattern) + '\n种子：' + str(seed))
# price = getPrice(pattern, seed)
# print('买入价格：' + price[0])
# print('周一上午：' + price[1])
# print('周一下午：' + price[2])
# print('周二上午：' + price[3])
# print('周二下午：' + price[4])
# print('周三上午：' + price[5])
# print('周三下午：' + price[6])
# print('周四上午：' + price[7])
# print('周四下午：' + price[8])
# print('周五上午：' + price[9])
# print('周五下午：' + price[10])
# print('周六上午：' + price[11])
# print('周六下午：' + price[12])
