######################################################################################################
#
# Rebalancing BOT 
#
# VERSION 2.0.0  Latest Update 25/03/2022
#
# Developer Jirameth K.
#
######################################################################################################
######################################################################################################
#
# Updating note
#
# V1.0.0 Updated 18/03/2022 20:03
#		   - Percent rebalancing
# V1.1.0 Updated 19/03/2022 08:39
#		   - Added fee calculation feature
#          - fixing bug case small lot order
# V1.2.0 Updated 20/03/2022 18:59
#		   - Added notice account information
# V1.2.2 Updated 21/03/2022 11:27
#		   - Bug fixed and add some more notice information (account updating)
# V1.2.3 Updated 21/03/2022 13:55
#		   - Added discout fee
# V1.2.4 Updated 21/03/2022 17:17
#		   - Added number of trading
# V1.3.0 Updated 22/03/2022 12:30
#		   - Bug fixed minimum oreder
# V1.3.1 Updated 22/03/2022 13:11
#		   - Added new calculation of minimum order and added expected order calculation on notification
# V1.3.2 Updated 22/03/2022 18:14
#		   - Update notification and added %Growth
# V1.4.0 Updated 23/03/2022 17:10
#		   - Update notification structure add sticker line function
# V1.4.1 Updated 24/03/2022 01:14
#		   - Changed some emoji and changed pattern ontification
# V1.4.2 Updated 24/03/2022 12:00
#		   - Changed some emoji and changed ontification (Added account name)
# V2.0.0 Updated 25/03/2022 21:11
#		   - Preparing record data process
# V2.1.0 Updated 30/03/2022 18:04
#		   - Added sending data process to google sheet (Account, trading log)
#
######################################################################################################

import ccxt
import time
import requests
from datetime import datetime

# Function -------------------------------------------------------------------------------------------
def line_api_message(message,line_api_token):
	url = 'https://notify-api.line.me/api/notify'
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded',
		'Authorization': f'Bearer {line_api_token}'
	}
	requests.post(url=url, data={'message': message} ,headers=headers)

def line_api_sticker(sitcker_id,sticker_package_id,line_api_token):
	url = 'https://notify-api.line.me/api/notify'
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded',
		'Authorization': f'Bearer {line_api_token}'
	}
	sticker = {
		'message': ' ',
		'stickerPackageId': sticker_package_id,
		'stickerId': sitcker_id
	}
	requests.post(url=url, data = sticker ,headers=headers)

def notification_on_cosole(input_text):
	current_time = datetime.now()
	print(current_time.strftime('%Y-%m-%d %H:%M:%S | ') + input_text)

def define_order_size(asset1, asset2, asset1_ratio, price):
	asset1_term2 = asset1 * price                           					#Cal to check asset 1 in term of asset 2
	actual_ratio = ( asset1_term2 / ( asset1_term2 + asset2 ) ) * 100     		#Cal actual ratio before rebalancing
	asset1_target_term2 = ( asset1_term2 + asset2 ) * ( asset1_ratio / 100 )    #Cal target of asset 1
	size = asset1_target_term2 - asset1_term2                             #Cal order size to achieve the target
	return size

def place_order_marketprice(line_api,asset_1_currency,asset_2_currency,choosen_market,order_size,current_price_bid,current_price_ask,discout_fee):

	if order_size > 0 :
		market_type = 'buy'
		price_order = current_price_bid
		order_size = abs(order_size)
		emoji_order = '\U0001F7E2'
	else:
		market_type = 'sell'
		price_order = current_price_ask
		order_size = abs(order_size)
		emoji_order = '\U0001F534'

	str_notice = 'Order market price expected\n'\
				 f'{market_type} {asset_1_currency} : {(order_size/price_order):.8f} {asset_1_currency} ({order_size:.2f} {asset_2_currency})'
	notification_on_cosole(str_notice)
	line_api_message(str_notice,line_api)

	response = exchange.create_order(choosen_market ,'market',market_type,float(order_size)/float(price_order))
	a = response['info']['side']
	b = response['info']['size']
	order_size_calfee = float(str(f'{order_size:.4f}'))
	fee_est = cal_fee(float(order_size_calfee),'taker',discout_fee)

	str_notice = f'\U0001F514\U0001F514 Order market-price completed \U0001F514\U0001F514\n\n'\
				 \
				 'Details\n'\
				 'Order type : ' + emoji_order + ' ' + a + ' \n'\
				 f'\U0001F3F7 Price : market price (est.{price_order})\n'\
				 f'\U0001F3F7 Lot size : {float(b):.8f} {asset_1_currency} (est.{float(b)*price_order:.2f} {asset_2_currency})\n\n'\
				 \
				 f'\U0001F3F7 Fee estimate : {fee_est:.8f} {asset_2_currency}\n'

	notification_on_cosole(str_notice)
	line_api_message(str_notice,line_api)

def pending_complete(line_api,deploy_url,order_pending_complete,asset_1_currency,asset_2_currency,real_order_size,price,discout_fee,qty_trade):

	if order_pending_complete == 'buy' :
		emoji_order = '\U0001F7E2'
	elif order_pending_complete == 'sell' :
		emoji_order = '\U0001F534'

	fee = cal_fee(real_order_size,'maker',discout_fee)

	reponse = update_trading_googlesheet(deploy_url,order_pending_complete,price,real_order_size,fee,qty_trade)

	str_notice = f'\U0001F514\U0001F514{emoji_order}{emoji_order} Order pending completed {emoji_order}{emoji_order}\U0001F514\U0001F514\n\n'\
				 \
				 'Details\n'\
				 'Order type : ' + emoji_order + ' ' + order_pending_complete + ' \n'\
				 f'\U0001F3F7 Price : {price:.2f} {asset_2_currency}\n'\
				 f'\U0001F3F7 Lot size : {real_order_size:.8f} {asset_1_currency} ({(real_order_size*price):.2f} {asset_2_currency})\n\n'\
				 \
				 f'\U0001F3F7 Fee : {fee:.8f} {asset_2_currency}\n\n'\
				 \
				 f'\U00002601 Update on google sheet - reponse : {reponse}\n'

	notification_on_cosole(str_notice)
	line_api_message(str_notice,line_api)

def place_pending_order(line_api,asset_1_currency,asset_2_currency,choosen_market,order_type,order_size,price,discout_fee):

	response = exchange.create_order(choosen_market,'limit',order_type,float(abs(order_size))/float(price),float(price))
	a = response['info']['side']
	b = response['info']['size']
	c = response['info']['price']
	order_size_calfee = float(str(f'{order_size:.4f}'))
	fee_est = cal_fee(order_size_calfee,'maker',discout_fee)

	if order_type == 'buy':
		emoji_order = '\U0001F7E2'
	elif order_type == 'sell':
		emoji_order = '\U0001F534'


	str_notice = '\U0001F514\U0001F514 Placed pending order \U0001F514\U0001F514\n\n'\
				 \
				 'Details\n'\
				 'Order type : pending ' + emoji_order + ' ' + a + '\n'\
				 '\U0001F3F7 Price : ' + c + '\n'\
				 f'\U0001F3F7 Lot size : {float(b):.8f} {asset_1_currency} ({float(b)*float(c):.2f} {asset_2_currency})\n'\
				 f'Lot expected : {(float(abs(order_size))/float(price)):.8f} {asset_1_currency} ({abs(order_size):.2f} {asset_2_currency})\n\n'\
				 \
				 f'\U0001F3F7 Fee estimate : {fee_est:.8f} {asset_2_currency}\n'

	notification_on_cosole(str_notice)
	line_api_message(str_notice,line_api)

	return float(b),float(c)

def update_accout(account_name,broker_name,line_api,deploy_url,asset1,asset2,f1_asset1,f1_asset2,current_asset1,current_asset2,f1_price_bid,f1_price_ask,current_price_bid,current_price_ask,qty_trade):

	percent_asset1 = ((float(current_asset1)/float(f1_asset1)) - 1)*100
	percent_asset2 = ((float(current_asset2)/float(f1_asset2))- 1)*100
	f1_price_avg = (float(f1_price_bid)+float(f1_price_ask))/2
	current_price_avg = (float(current_price_bid)+float(current_price_ask))/2
	price_diff = current_price_avg-f1_price_avg
	percent_price_diff = ( ( current_price_avg / f1_price_avg )- 1 ) * 100
	asset1_term2 = float(current_asset1)*current_price_avg
	total_value_asset = asset1_term2+current_asset2
	ratio1 = (asset1_term2/total_value_asset)*100
	ratio2 = (current_asset2/total_value_asset)*100

	growth_asset1 = current_asset1 - f1_asset1
	growth_asset2 = current_asset2 - f1_asset2
	f1_total_value_asset = (float(f1_asset1)*f1_price_avg)+f1_asset2
	total_value_asset_base = (float(current_asset1)*f1_price_avg)+current_asset2
	growth_cashflow = total_value_asset_base - f1_total_value_asset
	growth_cashflow_percent = (growth_cashflow/f1_total_value_asset)*100

	if growth_cashflow >= 0:
		emoji_cashflow = '\U0001F7E2'
	elif growth_cashflow < 0:
		emoji_cashflow = '\U0001F534'

	current_total_diff = total_value_asset - f1_total_value_asset
	percent_total_growth = (current_total_diff/f1_total_value_asset)*100

	if current_total_diff >= 0:
		emoji_profit = '\U0001F7E2'
	elif current_total_diff < 0:
		emoji_profit = '\U0001F534'

	reponse = update_account_googlesheet(deploy_url,qty_trade,current_asset1,current_asset2,current_price_bid,current_price_ask)

	str_notice = f'\U0001F4CB Account information \U0001F4CB\n\n'\
				 \
				 f'Trading account \U0001F4BC\n'\
				 f'\U0001F4B3 Account name : {account_name}\n'\
				 f'\U0001F4BC Broker name : {broker_name}\n\n'\
				 \
				 f'Assets detail \U0001F4B0\n'\
				 f'\U0001F4B0 {asset1} : {current_asset1:.8f} {asset1} ({asset1_term2:.2f} {asset2})\n'\
				 f'\U0001F4B4 {asset2} : {current_asset2:.2f} {asset2}\n'\
				 f'Total asset : {total_value_asset:.2f} {asset2}\n'\
				 f'Ratio : {ratio1:.2f} % / {ratio2:.2f} %\n\n'\
				 \
				 f'Growth detail \U0001F4CA\n'\
				 f'\U0001F4B0{asset1} : {growth_asset1:.8f} {asset1} ({percent_asset1:.2f} %)\n'\
				 f'\U0001F4B4{asset2} : {growth_asset2:.4f} {asset2} ({percent_asset2:.2f} %)\n'\
				 f'Total asset diff : {emoji_profit} {current_total_diff:.2f} {asset2} ({percent_total_growth:.2f} %)\n\n'\
				 \
				 f'Cashflow detail \U0001F4C8\n'\
				 f'\U0001F4D9 Assets start ({f1_price_avg:.2f} {asset2}) : {f1_total_value_asset:.2f} {asset2}\n'\
				 f'\U0001F4D8 Assets current ({f1_price_avg:.2f} {asset2}) : {total_value_asset_base:.2f} {asset2}\n'\
				 f'Growth cashflow : {emoji_cashflow} {growth_cashflow:.4f} {asset2} ({growth_cashflow_percent:.4f} %)\n\n'\
				 \
				 f'Price detail \U0001F4C8\n'\
				 f'\U0001F4D9 Start price : {f1_price_bid:.2f} - {f1_price_ask:.2f} {asset2}\n'\
				 f'\U0001F4D8 Current price : {current_price_bid:.2f} - {current_price_ask:.2f} {asset2}\n'\
				 f'Price diff (avg.) : {price_diff:.2f} ({percent_price_diff:.2f} %)\n\n'\
				 \
				 f'Trading detail \U0001F9FE\n'\
				 f'Transaction : {qty_trade} times\n\n'\
				 \
				 f'\U00002601 Update on google sheet - reponse : {reponse}\n'

	notification_on_cosole(str_notice)
	line_api_message(str_notice,line_api)

def cal_fee(size_of_order,taker_maker,discout_fee):
	discout_factor = 1 - (discout_fee/100)
	if size_of_order <= 2000000 :
		if taker_maker == 'taker' :
			fee = 0.070
		elif taker_maker == 'maker' :
			fee = 0.020
	elif size_of_order <= 5000000 :
		if taker_maker == 'taker' :
			fee = 0.060
		elif taker_maker == 'maker' :
			fee = 0.015
	elif size_of_order <= 10000000 :
		if taker_maker == 'taker' :
			fee = 0.055
		elif taker_maker == 'maker' :
			fee = 0.010
	elif size_of_order <= 25000000 :
		if taker_maker == 'taker' :
			fee = 0.050
		elif taker_maker == 'maker' :
			fee = 0.005
	elif size_of_order <= 50000000 :
		if taker_maker == 'taker' :
			fee = 0.045
		elif taker_maker == 'maker' :
			fee = 0.000
	elif size_of_order > 50000000 :
		if taker_maker == 'taker' :
			fee = 0.040
		elif taker_maker == 'maker' :
			fee = 0.000
	return fee * discout_factor

def update_account_googlesheet(deploy_url,qty_trade,current_asset1,current_asset2,current_price_bid,current_price_ask):
	command = '?numre=' + str(qty_trade) + '&'\
			  'crt_price_bid=' + str(current_price_bid) + '&'\
			  'crt_price_ask=' + str(current_price_ask) + '&'\
			  'crt_asset1=' + str(current_asset1) + '&'\
			  'crt_asset2=' + str(current_asset2)

	url = deploy_url + command
	response = requests.get(url)
	return response

def update_trading_googlesheet(deploy_url,order_pending_complete,price,real_order_size,fee,qty_trade):
	command = '?numre=' + str(qty_trade) + '&'\
			  'type=' + str(order_pending_complete) + '&'\
			  'price=' + str(price) + '&'\
			  'size=' + str(real_order_size) + '&'\
			  'fee=' + str(fee)

	url = deploy_url + command
	response = requests.get(url)
	return response

# ----------------------------------------------------------------------------------------------------

# From developer -------------------------------------------------------------------------------------
bot_type = 'Percentage rebalancing'
verson_bot = '2.1.0'
update_on = '30/03/2022 18:04 (GMT+7)'
developer_name = 'Jirameth K.'
email_developer = 'meth.jirameth@gmail.com'
copyright_name = 'Jirameth Kaewsuwan'
# ----------------------------------------------------------------------------------------------------

# Information from exchange --------------------------------------------------------------------------
api_key    = 'API-KEY' 
secret_key    = 'SECRET-KEY'
password  = ''
account_name  = ''
# Bot 			- 	WQcg3NDcTzQdHKgpfv3pb02tIY7g8KHww76Sx6UpM6h
# Developer01	-	8lSE990kfBTl3NYdLkZf4EOKLItzGVfzmVlOq4QIYSc
line_api = 'LINE-NOTIFY-API-KEY'
account_googlesheet_url = 'GOOGLE-SHEET-URL'
trading_googlesheet_url = 'GOOGLE-SHEET-URL'
broker_name = 'FTX'
# ----------------------------------------------------------------------------------------------------

# Optimazing parameter -------------------------------------------------------------------------------
asset_1_currency = 'BTC'
asset_2_currency = 'USD'
asset_1_ratio = 50
order_size_percent = 1
order_size_value = 3.5          #haven't implemented
delay_time = 10
loading_delay = 2
minimum_order_asset1 = 0.0001
discout_fee = 5
# ----------------------------------------------------------------------------------------------------

# Initial parameter ----------------------------------------------------------------------------------
market_type = ''
choosen_market = asset_1_currency + '/' + asset_2_currency
asset_2_ratio = 100 - asset_1_ratio
f1_remember = False
f1_asset1 = 0
f1_asset2 = 0
total_fee_est = 0
qty_trade = 0
read_price_data = True
read_account_data = True
read_order_data = True
error_clear = True
pending_buy_lot = 0
pending_sell_lot = 0
pending_buy_price = 0
pending_sell_price = 0
pending_buy_openning = False
pending_sell_openning = False
# ----------------------------------------------------------------------------------------------------

line_api_sticker(16581276,8522,line_api)

str_notice = f'{bot_type} bot version {verson_bot} has been activated.'

notification_on_cosole(str_notice)
line_api_message(str_notice,line_api)

str_notice = f'\U0001F4CB Bot information \U0001F4CB\n\n'\
			 \
			 f'\U0001F5A5 Bot : {bot_type}\n'\
			 f'\U0001F5A5 Version : {verson_bot}\n'\
			 f'\U0000231A Updated on : {update_on}\n'\
			 f'\U0001F408 Developer : {developer_name}\n'\
			 f'\U0001F4E7 Email : {email_developer}\n\n'\
			 \
			 f'\U000000A9 Copyright by {copyright_name}.\n'

notification_on_cosole(str_notice)
line_api_message(str_notice,line_api)

str_notice = f'\U00002699 Setting parameters \U00002699\n\n'\
			 \
			 f'Detail\n'\
             f'\U0001F4B0 Market : {choosen_market}\n'\
             f'\U0001F4B0 Ratio : {asset_1_currency} ({asset_1_ratio}%) / {asset_2_currency} ({asset_2_ratio}%)\n'\
             f'\U0001F3F7 % Rebalance : {order_size_percent} %\n'\
             f'\U0001F3F7 Minimum order : {minimum_order_asset1} {asset_1_currency}\n'\
             f'\U0001F3F7 % Discount fee : {discout_fee} %\n'\
             f'\U000023F1 Period : {delay_time} seconds\n'\
             f'\U000023F3 loading time : {loading_delay} seconds\n'

notification_on_cosole(str_notice)
line_api_message(str_notice,line_api)

# Prepare API ----------------------------------------------------------------------------------------
exchange = ccxt.ftx({'apiKey' : api_key ,'secret' : secret_key ,'password' : password ,'enableRateLimit': True})
if account_name == '' :
	account_name = 'Main account'
	
else:
	exchange.headers = {'ftx-SUBACCOUNT': account_name,}
	
# ----------------------------------------------------------------------------------------------------
str_notice = f'\U0001F4BC Account trading account \U0001F4BC\n\n'\
			 \
			 f'\U0001F4B3 Account name : {account_name}\n'\
			 f'\U0001F4BC Broker name : {broker_name}\n'

notification_on_cosole(str_notice)
line_api_message(str_notice,line_api)

## Cancle openning order ------------------------------------
#response = exchange.cancel_all_orders(choosen_market)
#notification_on_cosole(response)
#line_api_message(response,line_api)
#pending_buy_openning = False
#pending_sell_openning = False
## ----------------------------------------------------------

# Get account information -----------------------------------------
while read_account_data == True:
	try:
		account_info = exchange.fetch_balance()
	except:

		str_notice = '\U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8 Error!! \U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8\n\n'\
					 \
					 'Detail\n'\
					 'Could not get account data from exchange. The system is still getting data.\n'

		notification_on_cosole(str_notice)
		line_api_message(str_notice,line_api)
		error_clear = True
	else:
		if error_clear == False:

			str_notice = '\U00002705 Solved!!\n\n'\
						 \
						 'Detail\n'\
						 'The system has gotten account data.\n'

			notification_on_cosole(str_notice)
			line_api_message(str_notice,line_api)
			error_clear = True

		read_account_data = False

read_account_data = True

#Update balances of all assets
balance_asset1 = account_info[asset_1_currency]['total']
balance_asset2 = account_info[asset_2_currency]['total']
# -----------------------------------------------------------------

time.sleep(loading_delay)

# Get price from exchange -----------------------------------------
while read_price_data == True:
	try:
		current_price = exchange.fetch_ticker(choosen_market)
	except:

		str_notice = '\U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8 Error!! \U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8\n\n'\
					 \
					 'Detail\n'\
					 'Could not get price data from exchange. The system is still getting data.\n'

		notification_on_cosole(str_notice)
		line_api_message(str_notice,line_api)
		error_clear = True
	else:
		if error_clear == False:

			str_notice = '\U00002705 Solved!!\n\n'\
						 \
						 'Detail\n'\
						 'The system has gotten price data.\n'

			notification_on_cosole(str_notice)
			line_api_message(str_notice,line_api)
			error_clear = True

		read_price_data = False

read_price_data = True

#Update current price
current_price_bid = current_price['bid']
current_price_ask = current_price['ask']
# -----------------------------------------------------------------

#Remember account information before trading ----------------------
if f1_remember == False :
	f1_asset1 = balance_asset1
	f1_asset2 = balance_asset2
	f1_price_bid = current_price_bid
	f1_price_ask = current_price_ask
	update_accout(account_name,broker_name,line_api,account_googlesheet_url,asset_1_currency,asset_2_currency,f1_asset1,f1_asset2,balance_asset1,balance_asset2,f1_price_bid,f1_price_ask,current_price_bid,current_price_ask,qty_trade)
	f1_remember = True
# -----------------------------------------------------------------

# --------------------------------------------------------------------------------------------------

while True:

	# Delay
	time.sleep(delay_time)

	# Check openning order -----------------------------------------
	while read_order_data == True:
		try:
			check_order = exchange.fetch_open_orders(choosen_market)
		except:

			str_notice = '\U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8 Error!! \U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8\n\n'\
						 \
						 'Detail\n'\
						 'Could not get number of openning order from exchange. The system is still getting data.\n'

			notification_on_cosole(str_notice)
			line_api_message(str_notice,line_api)
			error_clear = False
		else:
			if error_clear == False:

				str_notice = '\U00002705 Solved!!\n\n'\
							 \
							 'Detail\n'\
							 'The system has gotten number of openning order.\n'

				notification_on_cosole(str_notice)
				line_api_message(str_notice,line_api)
				error_clear = True

			read_order_data = False

	read_order_data = True

  	# Count number of order
	count_pending = len(check_order) 
	# --------------------------------------------------------------

	if count_pending != 2 :

		if count_pending == 0 :

			try:
				# Place order market price
				order_size = define_order_size(balance_asset1,balance_asset2,asset_1_ratio,current_price_bid)
				place_order_marketprice(line_api,asset_1_currency,asset_2_currency,choosen_market,order_size,current_price_bid,current_price_ask,discout_fee)
			except:
				# Cancle openning order ------------------------------------
				response = exchange.cancel_all_orders(choosen_market)
				notification_on_cosole(response)
				line_api_message(response,line_api)

				pending_buy_openning = False
				pending_sell_openning = False
				# ---------------------------------------------------------
			else:
				qty_trade = qty_trade + 1

			# Delay
			time.sleep(delay_time)

		elif count_pending > 0 :

			qty_trade = qty_trade + 1

			# Notice complete pending order --------------------------------------
			if pending_buy_openning == True and pending_sell_openning == True :

				order_pending_openning = check_order[0]['side']

				if order_pending_openning == 'buy' :
					order_pending_complete = 'sell'
					pending_complete(line_api,trading_googlesheet_url,order_pending_complete,asset_1_currency,asset_2_currency,pending_sell_lot,pending_sell_price,discout_fee,qty_trade)

				elif order_pending_openning == 'sell' :
					order_pending_complete = 'buy'
					pending_complete(line_api,trading_googlesheet_url,order_pending_complete,asset_1_currency,asset_2_currency,pending_buy_lot,pending_buy_price,discout_fee,qty_trade)
			else :
				str_notice = '\U000026A0\U000026A0 There is no pending data record \U000026A0\U000026A0\n\n'\
							 \
							 'There are 2 pending orders were being opened before program execution'
				notification_on_cosole(str_notice)
				line_api_message(str_notice,line_api)

			# --------------------------------------------------------------------

			# Cancle openning order ------------------------------------
			response = exchange.cancel_all_orders(choosen_market)
			notification_on_cosole(response)
			line_api_message(response,line_api)

			pending_buy_openning = False
			pending_sell_openning = False

			# ----------------------------------------------------------

		# Get account information -----------------------------------------
		while read_account_data == True:
			try:
	  			account_info = exchange.fetch_balance()
			except:

				str_notice = '\U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8 Error!! \U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8\n\n'\
							 \
							 'Detail\n'\
							 'Could not get account data from exchange. The system is still getting data.\n'

				notification_on_cosole(str_notice)
				line_api_message(str_notice,line_api)
				error_clear = False
			else:
				if error_clear == False:

					str_notice = '\U00002705 Solved!!\n\n'\
								 \
								 'Detail\n'\
								 'The system has gotten account data.\n'

					notification_on_cosole(str_notice)
					line_api_message(str_notice,line_api)
					error_clear = True

				read_account_data = False

		read_account_data = True

	  	#Update balances of all assets
		balance_asset1 = account_info[asset_1_currency]['total']
		balance_asset2 = account_info[asset_2_currency]['total']
	  	# -----------------------------------------------------------------

		time.sleep(loading_delay)

		# Get price from exchange -----------------------------------------
		while read_price_data == True:
			try:
	  			current_price = exchange.fetch_ticker(choosen_market)
			except:

				str_notice = '\U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8 Error!! \U0001F6A8\U0001F6A8\U0001F6A8\U0001F6A8\n\n'\
							 \
							 'Detail\n'\
							 'Could not get price data from exchange. The system is still getting data.\n'

				notification_on_cosole(str_notice)
				line_api_message(str_notice,line_api)
				error_clear = False
			else:
				if error_clear == False:

					str_notice = '\U00002705 Solved!!\n\n'\
								 \
								 'Detail\n'\
								 'The system has gotten price data.\n'

					notification_on_cosole(str_notice)
					line_api_message(str_notice,line_api)
					error_clear = True

				read_price_data = False

		read_price_data = True

	  	#Update current price
		current_price_bid = current_price['bid']
		current_price_ask = current_price['ask']
	  	# -----------------------------------------------------------------

		update_accout(account_name,broker_name,line_api,account_googlesheet_url,asset_1_currency,asset_2_currency,f1_asset1,f1_asset2,balance_asset1,balance_asset2,f1_price_bid,f1_price_ask,current_price_bid,current_price_ask,qty_trade)

		# Cal pending price  buy/sell pending order ----------------
		buy_pending_price = current_price_bid * (1-(order_size_percent/100))
		sell_pending_price = current_price_ask * (1+(order_size_percent/100))
		# ----------------------------------------------------------

		try:
			# Place pending buy ----------------------------------------
			order_size = define_order_size(balance_asset1,balance_asset2,asset_1_ratio,buy_pending_price)
			pending_buy_lot,pending_buy_price = place_pending_order(line_api,asset_1_currency,asset_2_currency,choosen_market,'buy',order_size,buy_pending_price,discout_fee)
			pending_buy_openning = True
			# ----------------------------------------------------------
		except:

			minimum_order = (float(minimum_order_asset1) * float(buy_pending_price)) + 0.01

			str_notice = f'\U0001F6A8\U0001F6A8 Error!! \U0001F6A8\U0001F6A8\n\n'\
						 \
						 'Detail\n'\
						 f'\U0001F7E2 Order buy ({order_size:.4f} {asset_2_currency}) was too small.\n\n'\
						 \
						 f'Current price\n'\
						 f'Price bid : \U0001F7E2 {current_price_bid:.2f} {asset_2_currency}.\n'\
						 f'Price ask : \U0001F534 {current_price_ask:.2f} {asset_2_currency}.\n\n'\
						 \
						 f'Pending detail\n'\
						 f'Pending buy : \U0001F7E2 {buy_pending_price:.2f} {asset_2_currency}.\n'\
						 f'Pending sell : \U0001F534 {sell_pending_price:.2f} {asset_2_currency}.\n\n'\
						 \
						 f'\U00002705 Order has been set to \U0001F3F7 {minimum_order_asset1} {asset_1_currency} ({minimum_order:.4f} {asset_2_currency}).\n'
						 
			notification_on_cosole(str_notice)
			line_api_message(str_notice,line_api)
		 	
			order_size = minimum_order

			# Place pending buy ----------------------------------------
			pending_buy_lot,pending_buy_price = place_pending_order(line_api,asset_1_currency,asset_2_currency,choosen_market,'buy',order_size,buy_pending_price,discout_fee)
			pending_buy_openning = True
			# ----------------------------------------------------------



		try:
			# Place pending sell ---------------------------------------
			order_size = define_order_size(balance_asset1,balance_asset2,asset_1_ratio,sell_pending_price)
			pending_sell_lot,pending_sell_price = place_pending_order(line_api,asset_1_currency,asset_2_currency,choosen_market,'sell',order_size,sell_pending_price,discout_fee)
			pending_sell_openning = True
			# ----------------------------------------------------------
		except:

			minimum_order = (float(minimum_order_asset1) * float(sell_pending_price)) + 0.01

			str_notice = f'\U0001F6A8\U0001F6A8 Error!! \U0001F6A8\U0001F6A8\n\n'\
						 \
						 'Detail\n'\
						 f'\U0001F534 Order sell ({order_size:.4f} {asset_2_currency}) was too small.\n\n'\
						 \
						 f'Current price\n'\
						 f'Price bid : \U0001F7E2 {current_price_bid:.2f} {asset_2_currency}.\n'\
						 f'Price ask : \U0001F534 {current_price_ask:.2f} {asset_2_currency}.\n\n'\
						 \
						 f'Pending detail\n'\
						 f'Pending buy : \U0001F7E2 {buy_pending_price:.2f} {asset_2_currency}.\n'\
						 f'Pending sell : \U0001F534 {sell_pending_price:.2f} {asset_2_currency}.\n\n'\
						 \
						 f'\U00002705 Order has been set to \U0001F3F7 {minimum_order_asset1} {asset_1_currency} ({minimum_order:.4f} {asset_2_currency}).\n'

			notification_on_cosole(str_notice)
			line_api_message(str_notice,line_api)

			order_size = minimum_order

			# Place pending sell ---------------------------------------
			pending_sell_lot,pending_sell_price = place_pending_order(line_api,asset_1_currency,asset_2_currency,choosen_market,'sell',order_size,sell_pending_price,discout_fee)
			pending_sell_openning = True
			# ----------------------------------------------------------


