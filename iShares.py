import requests
import requests_cache
import json
import codecs
import os
import csv
from datetime import date, timedelta
import pandas_datareader.data as web


# Cache our web requests for 24 hours since we don't want to bother any of the servers
# we're talking to more than we have to
requests_cache.install_cache('ishares_cache', backend='sqlite', expire_after=86400)


# iSharesProductDataRow
#
# class
#
# represent one row of the table from:
# https://www.ishares.com/us/products/etf-product-list#!type=ishares&tab=overview&view=list
class iSharesProductDataRow:
    def __init__(self, column_indices, raw_row):
        self.column_indices = column_indices
        self.raw_row = raw_row

    def get_ticker_symbol(self):
        return self.raw_row[self.column_indices['localExchangeTicker']]

    def get_portfolio_id(self):
        return self.raw_row[self.column_indices['portfolioId']]

    def get_name(self):
        return self.raw_row[self.column_indices['fundShortName']]

    def get_holdings_csv_url(self):
        return 'https://www.ishares.com/us/products/%s/ishares-phlx-semiconductor-etf/1467271812596.ajax?fileType=csv&fileName=SOXX_holdings&dataType=fund' % self.get_portfolio_id()


# Loads product metadata (equivelent to loading the table from https://www.ishares.com/us/products/etf-product-list#!type=ishares&tab=overview&view=list)
def get_ishares_product_data_json():
    r = requests.get('https://www.ishares.com/us/products/etf-product-list/1522815705927.ajax?fileType=json')
    data = json.loads(codecs.decode(r.text.encode(), encoding='utf-8-sig'))

    column_indices = {}

    i = 0
    for col in data['columns']:
        column_indices[col['name']] = i
        i += 1

    return column_indices, data


# Loads a single iSharesProductDataRow by ticker symbol
def get_ishares_product_data_row_for_ticker(ticker_symbol):
    column_indices, product_data = get_ishares_product_data_json()

    for row in product_data['data']:
        if row[column_indices['localExchangeTicker']] == ticker_symbol:
            return iSharesProductDataRow(column_indices, row)

    raise RuntimeError('No iShares ETF found for symbol %s. Try searching at https://www.ishares.com/us/products/etf-product-list')


# Utility function to name cached holdings csv files
def get_holdings_csv_file_for_ticker(ticker):
    cwd = os.getcwd()
    destination = os.path.join(cwd, ticker + '_holdings.csv')
    return destination


# Downloads a csv holding file for an etf with a given ticker symbol
#  (we download the csv data to files so that we can cache it instead of bothering the server ever time)
def download_ishares_csv_holdings_for_ticker_to_file(ticker_symbol):
    print('Downloading metadata for ticker symbol %s...' % ticker_symbol, end='')
    product = get_ishares_product_data_row_for_ticker(ticker_symbol)
    print('Done.')

    print('\n')

    print('Name:\t%s' % product.get_name())
    print('Symbol:\t%s' % product.get_ticker_symbol())
    print('Id:\t%s' % product.get_portfolio_id())
    print('CSV URL:\t%s' % product.get_holdings_csv_url())

    print('\n')

    print('Downloading csv holdings data for ticker symbol %s...'% ticker_symbol, end='')
    r = requests.get(product.get_holdings_csv_url())
    print('Done.')

    destination = get_holdings_csv_file_for_ticker(product.get_ticker_symbol())

    print('Writing data to CSV file...', end='')
    with open(destination, 'wb') as f:
        f.write(r.content)
    print('Done.')

    print('\n')

    print('Holdings data is now located at: %s' % destination)


# iSharesHolding
#
# class
#
# represents a single row in the "holdings" csv file
class iSharesHolding:
    def __init__(self, column_indices, raw_row):
        self.column_indices = column_indices
        self.raw_row = raw_row

    def get_ticker_symbol(self):
        return self.raw_row[self.column_indices['Ticker']]

    def get_name(self):
        return self.raw_row[self.column_indices['Name']]

    def get_weight(self):
        return float(self.raw_row[self.column_indices['Weight (%)']]) / 100

    def get_share_count(self):
        return int(float(self.raw_row[self.column_indices['Shares']].replace(',','')))


# Parses an array of "holding" objects from a cached CSV file for a given ticker symbol
#  downloads the CSV file if it doesn't exist
def get_ishares_csv_holdings_for_ticker(ticker_symbol):
    print('Downloading metadata for ticker symbol %s...' % ticker_symbol, end='')
    product = get_ishares_product_data_row_for_ticker(ticker_symbol)
    print('Done.')

    print('\n')

    print('Name:\t%s' % product.get_name())
    print('Symbol:\t%s' % product.get_ticker_symbol())
    print('Id:\t%s' % product.get_portfolio_id())
    print('CSV URL:\t%s' % product.get_holdings_csv_url())

    print('\n')

    local_csv_file = get_holdings_csv_file_for_ticker(product.get_ticker_symbol())

    if not os.path.isfile(local_csv_file):
        download_ishares_csv_holdings_for_ticker_to_file(ticker_symbol)

    with open(local_csv_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        column_indicies = {}
        holdings = []

        for line in csv_reader:
            if len(line) > 3:
                if 'ticker' in line[0].lower():
                    i = 0
                    for cell in line:
                        column_indicies[cell] = i
                        i += 1
                else:
                    holdings.append(iSharesHolding(column_indicies, line))

        return holdings


# Returns the metadata from the top few rows of the csv file as a dictionary object
def get_ishares_csv_metadata_for_ticker(ticker_symbol):
    print('Downloading metadata for ticker symbol %s...' % ticker_symbol, end='')
    product = get_ishares_product_data_row_for_ticker(ticker_symbol)
    print('Done.')

    print('\n')

    print('Name:\t%s' % product.get_name())
    print('Symbol:\t%s' % product.get_ticker_symbol())
    print('Id:\t%s' % product.get_portfolio_id())
    print('CSV URL:\t%s' % product.get_holdings_csv_url())

    print('\n')

    local_csv_file = get_holdings_csv_file_for_ticker(product.get_ticker_symbol())

    if not os.path.isfile(local_csv_file):
        download_ishares_csv_holdings_for_ticker_to_file(ticker_symbol)

    with open(local_csv_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        data = {}

        for line in csv_reader:
            if len(line) == 2:
                data[line[0]] = line[1]

        return data


# returns true if standard lookups will fail for this equity
def is_not_normal_equity(ticker_symbol):
    if ticker_symbol == 'XTSLA':
        return True
    if ticker_symbol == 'UBFUT':
        return True
    if ticker_symbol == 'ESH9':
        return True
    return False


# returns equity prices for equities that are "non normal"
#  these are cash funds and futures contracts that tend to represent
#  very small holdings for etfs - these values would cause inaccurate valuations
#  if etfs held large numbers of futures contracts
def get_price_for_non_normal_equity(ticker_symbol):
    if ticker_symbol == 'XTSLA':
        return 1
    if ticker_symbol == 'UBFUT':
        return 100
    if ticker_symbol == 'ESH9':
        return 2594.10
    raise RuntimeError('invalid cash fund')


# sometimes people use a period in a ticker symbol; sometimes they don't
#  we have to convert back and forth manually sometimes
def format_ticker_symbol_for_data_reader(ticker_symbol):
    if ticker_symbol == 'BRKB':
        return 'BRK.B'
    if ticker_symbol == 'BFB':
        return 'BF.B'
    return ticker_symbol


# queries the internet for a current stock price
def get_stock_price_for_ticker(ticker_symbol, source='iex'):
    if is_not_normal_equity(ticker_symbol):
        return get_price_for_non_normal_equity(ticker_symbol)
    yesterday = date.today() - timedelta(1)
    today = date.today()
    res = web.DataReader(format_ticker_symbol_for_data_reader(ticker_symbol), source, yesterday, today)
    print(res)
    return res.loc[yesterday.strftime('%Y-%m-%d')]['close']


# estimates the underlying equity value of an iShares etf with a given ticker price
def estimate_value_for_ticker(ticker_symbol):
    holdings = get_ishares_csv_holdings_for_ticker(ticker_symbol)

    total = 0
    i = 0
    for holding in holdings:
        price = get_stock_price_for_ticker(holding.get_ticker_symbol())
        net_value = price * holding.get_share_count()
        total += net_value
        print('(%d of %d) %s\t%s\t%f\t%d\t%s' % (i+1, len(holdings), holding.get_ticker_symbol(), holding.get_name(), price, holding.get_share_count(), '{:,}'.format(net_value)))
        i += 1

    return total


if __name__ == '__main__':
    symbol = input('Ticker Symbol of iShares ETF: ')
    # symbol = 'IVV'
    estimated_value = estimate_value_for_ticker(symbol)
    metadata = get_ishares_csv_metadata_for_ticker(symbol)
    shares_outstanding = metadata['Shares Outstanding']
    price = get_stock_price_for_ticker(symbol)
    market_cap = int(float(shares_outstanding.replace(',', ''))) * float(price)
    print('\n')
    print('Estimated holdings value of %s:\t%s' % (symbol, '{:,}'.format(estimated_value)))
    print('Estimated market capitalization of %s:\t%s' % (symbol, '{:,}'.format(market_cap)))

    difference = market_cap - estimated_value

    if difference > 0:
        print('Overcapitalization:\t%s' % '{:,}'.format(-1 * market_cap))
    elif difference < 0:
        print('Undercapitalization:\t%s' % '{:,}'.format(market_cap))

    print("Ratio:\t%f" % (abs(difference)/market_cap))