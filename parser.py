import asyncio
import requests
from asyncpg import Connection
from bs4 import BeautifulSoup
from loader import db
from datetime import datetime, timedelta



class DBCommand:
    pool: Connection = db
    GET_VALUES_DB = 'SELECT * FROM birzha;'
    ADD_VALUE = 'INSERT INTO birzha (ticker, owner, relationship, date, cost, shares, value, transaction, shares_total, status) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);'
    GET_SALE_TICKET = 'SELECT ticket FROM ticket_sale;'


    async def add_value_db(self, ticker, owner, relationship, date, cost, shares, value, transaction, shares_total, status):
        args = ticker, owner, relationship, date, cost, shares, value, transaction, shares_total, status
        await self.pool.execute(self.ADD_VALUE, *args)

    async def get_values_db(self):
        return await self.pool.fetch(self.GET_VALUES_DB)

    async def get_sale_ticket(self):
        return await self.pool.fetch(self.GET_SALE_TICKET)

db = DBCommand()



async def get_html(link):
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
    }
    html = requests.get(link, headers=HEADERS).text
    return html

async def parse_html(soup, find='BUY', sell_arr=None):
    all_values = await db.get_values_db()
    trs = soup.find('table', class_='body-table').find_all('tr')[1:]

    t = datetime.today()
    today = datetime(t.year, t.month, t.day)


    for i in trs:
        tds = i.find_all('td')

        Ticker = tds[0].text.strip()
        Owner = tds[1].text.strip()
        Relationship = tds[2].text.strip()
        Date = tds[3].text.strip()
        Transaction = tds[4].text.strip()
        Cost = float(tds[5].text.strip())
        Shares = int(tds[6].text.strip().replace(',', ''))
        Value = int(tds[7].text.strip().replace(',', ''))
        shares_total = int(tds[8].text.strip().replace(',', ''))
        sec_form = tds[9].text.strip()

        # Работа с датой
        date = datetime.strptime(str(today.year) + Date, '%Y%b %d')

        # print(date >= today + timedelta(days=-2))
        # print(f'{Ticker} - {Owner} - {Relationship} - {Date} - {Transaction} - {Cost} - {Shares} - {Value} - {shares_total} - {sec_form}')


        if find == 'BUY':
            if Value >= 1000000 and date >= today + timedelta(days=-4) and date <= today + timedelta(days=1):

                adoption = True
                for item in all_values:
                    if item[1] == Ticker and item[2] == Owner and item[3] == Relationship and item[4] == Date and item[
                        5] == Cost and item[6] == Shares and item[7] == Value and item[9] == shares_total:
                        # print('Точно такая же запись')
                        adoption = False
                        break
                if adoption:
                    await db.add_value_db(Ticker, Owner, Relationship, Date, Cost, Shares, Value,Transaction, shares_total, 'New')

        if find == 'SELL':
            ad = False
            for i in sell_arr:
                if Ticker == i[0].strip() and date >= today + timedelta(days=-4) and date <= today + timedelta(days=1):
                    ad = True
            if ad:
                adoption = True

                for item in all_values:
                    if item[1] == Ticker and item[2] == Owner and item[3] == Relationship and item[4] == Date and item[
                        5] == Cost and item[6] == Shares and item[7] == Value and item[9] == shares_total:
                        adoption = False
                        break
                if adoption:
                    await db.add_value_db(Ticker, Owner, Relationship, Date, Cost, Shares, Value, Transaction, shares_total, 'New')

async def parse():
    link = 'https://finviz.com/insidertrading.ashx?tc=1'
    html = await get_html(link)
    soup = BeautifulSoup(html, 'html.parser')
    await parse_html(soup)



    sale_tickets = await db.get_sale_ticket()
    if sale_tickets == []:
        pass
    else:
        link_sell = 'https://finviz.com/insidertrading.ashx?tc=2'
        html = await get_html(link_sell)
        soup = BeautifulSoup(html, 'html.parser')
        await parse_html(soup, find='SELL', sell_arr=sale_tickets)




if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(parse())