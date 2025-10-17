import sqlite3

conn = sqlite3.connect('data/cameronpad_dev.db')
cur = conn.cursor()

print('=== STOCKS TABLE ===')
stocks = cur.execute('SELECT symbol, enabled FROM stocks').fetchall()
print(f'Total stocks: {len(stocks)}')
for row in stocks:
    print(f'  {row[0]}: enabled={row[1]}')

print('\n=== LATEST_PRICES TABLE ===')
prices = cur.execute('SELECT * FROM latest_prices').fetchall()
print(f'Total price records: {len(prices)}')
if len(prices) > 0:
    for row in prices:
        print(f'  Symbol: {row[0]}, Price: ${row[1]}, High: ${row[2]}, Low: ${row[3]}, TS: {row[4]}')
else:
    print('  NO DATA IN TABLE - Need to start stock service to fetch prices!')

conn.close()
