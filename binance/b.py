import csv
import json
import sys

import flask
import requests
from bs4 import BeautifulSoup
from pybit import usdt_perpetual
import time
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template, url_for, redirect, request, make_response
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

#position: absolute; left:25%; width: 50%; margin: 10;
from funs import pcheck
from smtplib import SMTP
import logging
import random
import string
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, MetaData, Table, Integer, String, \
    Column, DateTime, ForeignKey, Numeric, SmallInteger
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Session = sessionmaker()
engine = create_engine('sqlite:///db/data.db?check_same_thread=False')
Session.configure(bind=engine)
Base = declarative_base()

class Orders(Base):
    __tablename__ = 'orders'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    id_users = Column(String(), nullable=True)
    symbol = Column(String(), nullable=True)
    url = Column(String(), nullable=True)
    koef = Column(String(), nullable=True)
    qty = Column(String(), nullable=True)
    side = Column(String(), nullable=True)
    fake = Column(String(), nullable=True)


class Thread_th(Base):
    __tablename__ = 'threads_th'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    url = Column(String())

class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    api_acc = Column(String())
    email = Column(String(), unique=True, nullable=True)
    api = Column(String())
    secret = Column(String())
    hashed_password = Column(String(), nullable=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Proxy(Base, UserMixin):
    __tablename__ = 'proxy'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    ip = Column(String())
    login = Column(String())
    password = Column(String())

class Trader(Base, UserMixin):
    __tablename__ = 'trader'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    id_acc = Column(String())
    url = Column(String())
    procent = Column(String())
    stop = Column(String())
    stop_list = Column(String())
    dep = Column(String())
    proxy = Column(String())





Base.metadata.create_all(engine)






application = Flask(__name__)
application.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(application)

@login_manager.user_loader
def load_user(user_id):
    db_sess = Session()
    return db_sess.query(User).get(user_id)

def generate_random_string(length):
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for i in range(length))
    return rand_string


def main():
    application.run(host='0.0.0.0')
    print(flask.request.url)



headers = {'content-type': 'application/json'}


url = r'https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition'


#def th1(arg, b):
#    db_sess = Session()
#    while True:
#        if db_sess.query(Trader).filter((Trader.url == arg)).first():
#            print('поток', b)
#
#            json_data = {
#                "encryptedUid": f'{arg}',
#                "tradeType": 'PERPETUAL'
#            }
#            try:
#                response = requests.post(url, headers=headers, json=json_data)
#
#                if response.status_code != 200:
#                    response.raise_for_status()
#                data = json.loads(response.text)['data']['otherPositionRetList']
#                print(data)
#            except Exception as e:
#                print(e)
#            time.sleep(2)
#        else:
#            sys.exit()


def dep_th():
    db_sess = Session()

    while True:
        if db_sess.query(Trader).filter((Trader.dep == None)).first():
            trader_op = db_sess.query(Trader).filter((Trader.dep == None)).all()

            for d in trader_op:
                options = webdriver.ChromeOptions()
                options.add_argument('headless')
                options.add_argument('--no-sandbox')
                driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                link = f'https://www.binance.com/ru/futures-activity/leaderboard/user?encryptedUid={d.url}'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
                # response = requests.get(link, headers=headers)
                # soup = BeautifulSoup(response.text, 'lxml')
                driver.implicitly_wait(20)
                driver.get(link)
                time.sleep(5)
                html = driver.page_source
                soup = BeautifulSoup(html, 'lxml')

                symb = soup.find_all('div', class_='border-container css-vurnku')

                print(symb)
                text = ''
                for i in symb:
                    text = text + i.text

                roi = text.split('Ежедневный ROI')
                roi = roi[1].split('%PNL')

                pnl = text.split('PNL по дням (USD)')
                pnl = pnl[1].split('Еженедельный ROI')

                if '.' in str(roi):
                    roi = roi[0].split('.')
                    roi[0] = roi[0].replace(',', '')

                if '.' in str(pnl):
                    pnl = pnl[0].split('.')
                    pnl[0] = pnl[0].replace(',', '')

                roi = float(roi[0])
                pnl = float(pnl[0])


                dep = pnl * 100 / roi
                trader_d = db_sess.query(Trader).filter((Trader.url == d.url)).all()

                for l in trader_d:
                    l.dep = dep
                try:
                    db_sess.commit()
                except Exception:
                    db_sess.rollback()

                time.sleep(30)
        else:
            trader_op = db_sess.query(Trader).all()

            for d in trader_op:
                options = webdriver.ChromeOptions()
                options.add_argument('headless')
                options.add_argument('--no-sandbox')
                driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                link = f'https://www.binance.com/ru/futures-activity/leaderboard/user?encryptedUid={d.url}'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
                # response = requests.get(link, headers=headers)
                # soup = BeautifulSoup(response.text, 'lxml')
                driver.implicitly_wait(20)
                driver.get(link)
                time.sleep(5)
                html = driver.page_source
                soup = BeautifulSoup(html, 'lxml')

                symb = soup.find_all('div', class_='border-container css-vurnku')

                print(symb)
                text = ''
                for i in symb:
                    text = text + i.text

                roi = text.split('Ежедневный ROI')
                roi = roi[1].split('%PNL')

                pnl = text.split('PNL по дням (USD)')
                pnl = pnl[1].split('Еженедельный ROI')

                if '.' in str(roi):
                    roi = roi[0].split('.')
                    roi[0] = roi[0].replace(',', '')

                if '.' in str(pnl):
                    pnl = pnl[0].split('.')
                    pnl[0] = pnl[0].replace(',', '')

                roi = float(roi[0])
                pnl = float(pnl[0])

                dep = pnl * 100 / roi
                trader_d = db_sess.query(Trader).filter((Trader.url == d.url)).all()

                for l in trader_d:
                    l.dep = dep
                try:
                    db_sess.commit()
                except Exception:
                    db_sess.rollback()

                time.sleep(30)



def th1(arg, b):
    db_sess = Session()

    def dep(uid):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        link = f'https://www.binance.com/ru/futures-activity/leaderboard/user?encryptedUid={uid}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
        # response = requests.get(link, headers=headers)
        # soup = BeautifulSoup(response.text, 'lxml')
        driver.implicitly_wait(20)
        driver.get(link)
        time.sleep(5)
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        symb = soup.find_all('div', class_='border-container css-vurnku')

        print(symb)
        text = ''
        for i in symb:
            text = text + i.text

        roi = text.split('Ежедневный ROI')
        roi = roi[1].split('%PNL')

        pnl = text.split('PNL по дням (USD)')
        pnl = pnl[1].split('Еженедельный ROI')

        if '.' in str(roi):
            roi = roi[0].split('.')
            roi[0] = roi[0].replace(',', '')

        if '.' in str(pnl):
            pnl = pnl[0].split('.')
            pnl[0] = pnl[0].replace(',', '')

        roi = float(roi[0])
        pnl = float(pnl[0])

        print(roi)
        print(pnl)

        dep = pnl * 100 / roi
        return dep

    def open_order(symboul, leverage, qty, id, side, url):
        try:
            trader_op = db_sess.query(Trader).filter((Trader.url == url), (Trader.id_acc == id)).first()
            if trader_op.dep == None:
                deposit = dep(url)
                trader_op.dep = deposit

            else:
                deposit = trader_op.dep

            user = db_sess.query(User).filter((User.id == trader_op.id_acc)).first()

            session_auth = usdt_perpetual.HTTP(
                endpoint="https://api.bybit.com",
                api_key=user.api,
                api_secret=user.secret
            )

            session_unauth = usdt_perpetual.HTTP(
                endpoint="https://api.bybit.com"
            )

            if float(side) > 0:
                side = 'Buy'
            else:
                side = 'Sell'

            try:
                print(session_auth.position_mode_switch(
                    symbol=symboul,
                    mode="BothSide"
                ))
            except Exception as e:
                print(e)

            try:
                session_auth.set_leverage(symbol=symboul, buy_leverage=leverage, sell_leverage=leverage)
            except Exception as e:
                print(e)

            procent = float(trader_op.procent)
            dep_clear = session_auth.get_wallet_balance()['result']['USDT']['equity']

            new_dep = float(dep_clear) * procent / 100
            koef = float(new_dep) / float(deposit)
            if '-' in str(qty):
                qty = str(qty).replace('-', '')
            qty2 = float(qty) * koef
            print(deposit)
            print(new_dep)
            print(koef)
            print(qty)
            print(qty2)
            print(session_auth.place_active_order(
                symbol=symboul,
                side=side,
                order_type="Market",
                qty=round(float(qty2), 3),
                time_in_force="GoodTillCancel",
                reduce_only=False,
                close_on_trigger=False
            ))

            orders = Orders(
                id_users=trader_op.id_acc,
                symbol=symboul,
                url=url,
                koef=koef,
                qty=qty,
                side=side
            )

            db_sess.add(orders)

            try:
                db_sess.commit()
            except Exception:
                db_sess.rollback()

        except Exception as e:
            print('5')
            print(e)

    def close_order(symboul, id, side):
        user = db_sess.query(User).filter((User.id == id)).first()
        anti_side = ''
        session_auth = usdt_perpetual.HTTP(
            endpoint="https://api.bybit.com",
            api_key=user.api,
            api_secret=user.secret
        )

        qty5 = session_auth.my_position(
            symbol=symboul
        )

        for x in qty5['result']:
            if str(x['side']) == side:
                qty5 = x['size']

        if side == 'Sell':
            anti_side = 'Buy'
        else:
            anti_side = 'Sell'

        print(session_auth.place_active_order(
            symbol=symboul,
            side=anti_side,
            order_type='Market',
            qty=float(qty5),
            time_in_force="GoodTillCancel",
            reduce_only=True,
            close_on_trigger=True
        ))

        db_sess.query(Orders).filter((Orders.id_users == id), (Orders.symbol == symboul)).delete()

        try:
            db_sess.commit()
        except Exception:
            db_sess.rollback()


    print(1)
    if db_sess.query(Trader).filter((Trader.url == arg)).first().proxy == None:
        print('тут')
        proxys = db_sess.query(Proxy).all()
        for p in proxys:
            if db_sess.query(Trader).filter((Trader.proxy == p.ip)).first():
                pass
            else:
                trader_proxy = db_sess.query(Trader).filter((Trader.url == arg)).all()
                for x in trader_proxy:
                    x.proxy = p.ip

                try:
                    db_sess.commit()
                    break
                except Exception:
                    db_sess.rollback()


    try:
        trader_proxy = db_sess.query(Trader).filter((Trader.url == arg)).first()
        proxys_tr = db_sess.query(Proxy).filter((Proxy.ip == trader_proxy.proxy)).first()
        #proxies = {
        #    'http': f'http://{proxys_tr.login}:{proxys_tr.password}@{proxys_tr.ip}:50100',
        #    'https': f'https://{proxys_tr.login}:{proxys_tr.password}@{proxys_tr.ip}:50100'
#
        #}
        #print(proxies)
    except:
        proxys = db_sess.query(Proxy).all()
        for p in proxys:
            if db_sess.query(Trader).filter((Trader.proxy == p.ip)).first():
                pass
            else:
                trader_proxy = db_sess.query(Trader).filter((Trader.url == arg)).all()
                for x in trader_proxy:
                    x.proxy = p.ip
            try:
                db_sess.commit()
            except Exception:
                db_sess.rollback()
            break

            #trader_proxy = db_sess.query(Trader).filter((Trader.url == arg)).first()
            #proxys_tr = db_sess.query(Proxy).filter((Proxy.ip == trader_proxy.proxy)).first()



    while True:
        if db_sess.query(Trader).filter((Trader.url == arg)).first():
            print('поток', b)

            response = requests.get('http://jsonip.com', proxies={
                'http': f'http://{proxys_tr.login}:{proxys_tr.password}@{proxys_tr.ip}:50100',
                'https': f'https://{proxys_tr.login}:{proxys_tr.password}@{proxys_tr.ip}:50100'

            })
            ip = response.json()['ip']
            print('Your public IP is:', ip)

            json_data = {
                "encryptedUid": f'{arg}',
                "tradeType": 'PERPETUAL'
            }
            try:
                #print(proxies)
                #url = 'https://2ip.ru/'
                #response = requests.get(url, proxies=proxies)
#
                #print(response.text)

                response = requests.post(url, headers=headers, json=json_data, proxies={
                'http': f'http://{proxys_tr.login}:{proxys_tr.password}@{proxys_tr.ip}:50100',
                'https': f'https://{proxys_tr.login}:{proxys_tr.password}@{proxys_tr.ip}:50100'

            })



                if response.status_code != 200:
                    response.raise_for_status()
                data = json.loads(response.text)['data']['otherPositionRetList']
                #print(data)

                trader = db_sess.query(Trader).filter((Trader.url == arg)).all()
                orders_tr = []
                for i in data:
                    orders_tr.append(i['symbol'])
                    for j in trader:
                        orders = []


                        tr = db_sess.query(Orders).filter((Orders.id_users == j.id_acc)).all()
                        for n in tr:
                            orders.append(n.symbol)

                        if i['symbol'] in orders:
                            pass
                        else:
                            if 'USDT' in i['symbol']:

                                if j.stop == 'on':
                                    orders = Orders(
                                        id_users=j.id_acc,
                                        symbol=i['symbol'],
                                        url=arg,
                                        koef='fake',
                                        qty='fake',
                                        side='fake',
                                        fake='1'
                                    )

                                    db_sess.add(orders)

                                    try:
                                        db_sess.commit()
                                    except Exception:
                                        db_sess.rollback()
                                else:
                                    open_order(i['symbol'], i['leverage'], i['amount'], j.id_acc, i['amount'], arg)

                for c in trader:
                    if c.stop == 'on':
                        c.stop = '0'
                    try:
                        db_sess.commit()
                    except Exception:
                        db_sess.rollback()

                for v in trader:
                    tr2 = db_sess.query(Orders).filter((Orders.id_users == v.id_acc), (Orders.url == arg)).all()
                    for n2 in tr2:
                        if n2.symbol not in orders_tr:
                            if n2.fake == '1':
                                db_sess.query(Orders).filter((Orders.id_users == v.id_acc), (Orders.symbol == n2.symbol)).delete()
                            else:
                                close_order(v.id_acc, n2.symbol, n2.side)

                time.sleep(2)
            except Exception as e:
                print(e)
        else:
            db_sess.query(Thread_th).filter((Thread_th.url == arg)).delete()
            db_sess.query(Orders).filter((Orders.url == arg)).delete()
            try:
                db_sess.commit()
            except Exception:
                db_sess.rollback()
            sys.exit()





@application.route('/', methods=['GET', 'POST'])
@application.route('/index', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated == False:
        return redirect('/create-account')

    db_sess = Session()
    user = db_sess.query(User).filter((User.id == current_user.id)).first()
    traders = db_sess.query(Trader).filter((Trader.id_acc == current_user.id)).all()
    email = user.email
    if len(str(email)) > 10:
        email = email[0:10] + '...'
    else:
        pass
    return render_template('index.html', email=email, traders=traders)

@application.route('/delete_traders', methods=['GET', 'POST'])
def delete_traders():
    if current_user.is_authenticated == False:
        return redirect('/create-account')

    if request.method == 'POST':
        db_sess = Session()
        url5 = request.form['uidd']
        tr = db_sess.query(Trader).filter((Trader.id_acc == current_user.id), (Trader.url == url5))
        tr.delete()
        try:
            db_sess.commit()
        except Exception:
            db_sess.rollback()
        return redirect('/')
    else:
        return render_template('delete.html')


@application.route('/settings', methods=['GET', 'POST'])
def settings():
    if current_user.is_authenticated == False:
        return redirect('/create-account')

    if request.method == 'POST':
        db_sess = Session()
        uid = request.form['uid']
        procent = request.form['procent']
        tr = db_sess.query(Trader).filter((Trader.id_acc == current_user.id), (Trader.url == uid)).first()
        tr.procent = procent
        try:
            db_sess.commit()
        except Exception:
            db_sess.rollback()
        return redirect('/')
    else:
        return render_template('settings.html')


@application.route('/add_traders', methods=['GET', 'POST'])
def add_traders():
    if current_user.is_authenticated == False:
        return redirect('/create-account')

    if request.method == 'POST':
        print('Запустили1')
        db_sess = Session()
        url = request.form['url']
        procent = request.form['procent']
        value = request.form.get('check')

        if db_sess.query(Trader).filter((Trader.url == url)).first():
            trader = Trader(
                id_acc=current_user.id,
                url=url,
                procent=procent,
                stop=value
            )
            db_sess.add(trader)
            try:
                db_sess.commit()
            except Exception:
                db_sess.rollback()
            print('Запустили2')
            return redirect('/')
        else:
            trader = Trader(
                id_acc=current_user.id,
                url=url,
                procent=procent,
                stop=value
            )
            db_sess.add(trader)
            try:
                db_sess.commit()
            except Exception:
                db_sess.rollback()
            print('Запустили')
            b = threading.Thread(target=th1, args=(url, url))
            b.start()

            thd = Thread_th(url=url)
            db_sess.add(thd)
            try:
                db_sess.commit()
            except Exception:
                db_sess.rollback()
            return redirect('/')


    else:
        return render_template('add_traders.html')


@application.route('/proxy', methods=['GET', 'POST'])
def proxy():
    if current_user.is_authenticated == False:
        return redirect('/create-account')

    if request.method == 'POST':
        db_sess = Session()
        ip = request.form['ip']
        login = request.form['login']
        password = request.form['password']

        if db_sess.query(Proxy).filter((Proxy.ip == ip)).first():
            try:
                pr = db_sess.query(Proxy).filter((Proxy.ip == ip)).first()
                pr.login = login
                pr.password = password
                try:
                    db_sess.commit()
                except Exception:
                    db_sess.rollback()
            except Exception:
                pass

        else:

            proxy = Proxy(
                ip=ip,
                login=login,
                password=password
            )
            db_sess.add(proxy)
            try:
                db_sess.commit()
            except Exception:
                db_sess.rollback()
            return redirect('/proxy')


    else:
        return render_template('proxy.html')

@application.route('/api', methods=['GET', 'POST'])
def api():
    if current_user.is_authenticated == False:
        return redirect('/create-account')

    if request.method == 'POST':
        db_sess = Session()
        api = request.form['api-key']
        secret = request.form['secret-key']
        api_acc = User(id=current_user.id, api=api, secret=secret)
        try:
            if db_sess.query(User).filter((User.id == current_user.id)).all():
                user = db_sess.query(User).filter((User.id == current_user.id)).first()
                user.api = api
                user.secret = secret
                try:
                    db_sess.commit()
                except Exception:
                    db_sess.rollback()
                return redirect('/')
            db_sess.add(api_acc)
            try:
                db_sess.commit()
            except Exception:
                db_sess.rollback()
            return redirect('/')
        except Exception as e:
            print(e)
            return "При добавление api произошла ошибка"
    else:
        return render_template('api.html')

@application.route('/create-account', methods=['GET', 'POST'])
def register():
    return render_template('signup.html')


@application.route('/create', defaults={'referal': None} , methods=['POST'])
@application.route('/create/<referal>', methods=['POST'])
def create(referal):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        password_again = request.form['password_again']

        print(email)
        print(password)
        print(password_again)

        if password != password_again:
            return redirect('/create-account')
            #Пароли не совпадают
        error = pcheck(password)
        if not error:
            return redirect('/create-account')
        db_sess = Session()
        if db_sess.query(User).filter(User.email == email).first():
            return redirect('/create-account')
        user = User(
            email=email
        )
        user.set_password(password)
        db_sess.add(user)
        try:
            db_sess.commit()
        except Exception as e:
            print(e)
            db_sess.rollback()
        message = 'Вы зарегистрировались'
        return redirect('/login')
    else:
        return redirect('/create-account')

@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        email = request.form['email']
        password = request.form['password']

        db_sess = Session()
        user = db_sess.query(User).filter(User.email == email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect("/")
        print('не вошел')
        return redirect(url_for('login'))
    else:
        return render_template('login.html')



@application.route("/logout")
def logout():
    logout_user()
    return redirect("/login")

if __name__ == '__main__':
    db_sess = Session()
    thrs = db_sess.query(Thread_th).all()
    if db_sess.query(Thread_th).all():
        for i in thrs:
            b = threading.Thread(target=th1, args=(i.url, i.url))
            b.start()
    b = threading.Thread(target=dep_th)
    b.start()
    main()