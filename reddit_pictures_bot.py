import telegram, praw
import configparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# Use configparser to red the ini files and fetch the credentials to access TG and reddit
cf_parser = configparser.ConfigParser()

# The objects that the telegram bot needs to work
# Telegram bot name: Reddit_pictures_bot
cf_parser.read('telegram.ini')
bot_token = cf_parser['CREDENTIALS']['bot_token']
updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

# Read the reddit credentials from the .ini file
cf_parser.read('reddit.ini')

# Create an instance of reddit (connect to account)
reddit = praw.Reddit(client_id = cf_parser['CREDENTIALS']['client_id'], 
	client_secret = cf_parser['CREDENTIALS']['client_secret'], 
	username = cf_parser['CREDENTIALS']['username'], 
	password = cf_parser['CREDENTIALS']['password'],
	user_agent = cf_parser['CREDENTIALS']['user_agent'] )

# Minimum amount of upvotes by default to download an image
cf_parser.read('config.ini')
MINUPS = int(cf_parser['REDDIT_FILTERS']['min_ups'])

# ----------------------------------------------------------------------------------------------
# Verify that the credentials are correct and the ini files work.
# Will add that later.

# ----------------------------------------------------------------------------------------------

# MENUS FOR THE BOT ----------------------------------------------------------------------------
# Main menu for the bot
main_menu = [
	[InlineKeyboardButton("Send memes", callback_data="memes")],
	[InlineKeyboardButton("Suggestions", callback_data="suggest"),
		InlineKeyboardButton("Other subreddit", callback_data="other")],
	[InlineKeyboardButton("Advanced", callback_data="advanced"),
		InlineKeyboardButton("Return", callback_data="return")]
]

# -----------------------------------------------------------------------------------------------
# Get the list of suggested subs from the suggestions.txt textfile
# In the file, each subreddit is written in a line (they all form a column)
def GetSuggestionsList():
	suggestions_list = []
	with open('suggestions.txt', 'r') as textfile:
		for line in textfile:
			suggestions_list.append(line.strip())

	return suggestions_list

# -----------------------------------------------------------------------------------------------
# Function that takes a list of suggested subreddits and makes a menu with buttons and
# unique callback data (the name of the sub) with it.
def SuggestionsMenu(suggestions, columns=2):
	rows = []
	full_rows = int(len(suggestions)/columns)
	buttons_last_row = len(suggestions) - full_rows*columns

	# Add the complete rows
	for row in range(full_rows):
		new_row = []
		this_row_suggestions = suggestions[row*columns:(row+1)*columns]
		for current_suggestion in this_row_suggestions:
			new_row.append(telegram.InlineKeyboardButton(current_suggestion,
				callback_data=current_suggestion))
		rows.append(new_row)

	# Add the last row
	last_row = []
	# Go <buttons_last_row> into the back of the list, and advance until the end of it.
	# (advance backwards because we're working with negative indexes --> back of the list)
	for i in range(buttons_last_row, 0, -1):
		last_row.append(telegram.InlineKeyboardButton(suggestions[-i],
			callback_data=suggestions[-i]))
	if len(last_row):
		rows.append(last_row)

	# Create the menu that this function will return (Inline Keyboard Markup)
	return telegram.InlineKeyboardMarkup(rows)

# ----------------------------------------------------------------------------------------------

# Function that generates a quantity menu for any given sub. This way the menus don't have to be 
# hardcoded one by one.
def QuantityMenu(sub, columns=2, quantities=[1, 5, 10, 20, 30, 50]):
	rows = [] # A certain amount of rows with full collumns, then add 1 row with the leftovers.
	full_rows = int(len(quantities)/columns)
	buttons_last_row = len(quantities) - full_rows*columns

	# Add the complete rows
	for row in range(full_rows):
		new_row = []
		this_row_quantities = quantities[row*columns:row*columns+columns]
		for current_quantity in this_row_quantities:
			new_row.append(telegram.InlineKeyboardButton(current_quantity, 
				callback_data="{} {}".format(sub, current_quantity)))
		rows.append(new_row)

	# Add the last row
	last_row = []
	# Go <buttons_last_row> into the back of the list, and advance until the end of it.
	# (advance backwards because we're working with negative indexes --> back of the list)
	for i in range(buttons_last_row, 0, -1):
		last_row.append(telegram.InlineKeyboardButton(quantities[-i], 
			callback_data="{} {}".format(sub, quantities[-i])))
	if len(last_row):
		rows.append(last_row)

	# Create the menu (inline keyboard Markup)
	return telegram.InlineKeyboardMarkup(rows)
# -----------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------
# Function that returns a list of urls for the pictures on a given sub (max = quantity)
# min_ups stands for the minimum amount of upvotes that a post needs to be valid.
def GetUrlsList(quantity, sub, min_ups=MINUPS):
	hot_generator = reddit.subreddit(sub).hot()
	counter = 0
	urls_list = []
	for post in hot_generator:
		if counter<quantity and post.url != None and post.ups>min_ups and not post.stickied:
			urls_list.append(post.url)
			counter += 1
		elif counter >= quantity:
			break # break the for loop and stop adding urls
	print("Got total amount of {} urls.".format(len(urls_list)))
	print("")
	return urls_list

# ---------------------------------------------------------------------------
# Function that makes telegram download and send photos, takes a list of urls
# And the callback function that calls it has to pass on update and context.
def SendPhotos(update, context, the_urls):
	for url in the_urls:
		try:
			context.bot.send_photo(chat_id=update.effective_chat.id, photo=url)
		except:
			print("Exception, could not sent url: {}".format(url))

# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# /start directly displays the GUI.
def start(update, context):
	print("Received start command from chat_id: {}".format(update.effective_chat.id))
	reply_markup = InlineKeyboardMarkup(main_menu)
	context.bot.send_message(chat_id=update.effective_chat.id, text="Sending menu. Select:", 
		reply_markup=reply_markup)
	
dispatcher.add_handler(CommandHandler("start", start))

# ------------------------------------------------------------------------------------------------
def send(update, context):
	chat_id = update.effective_chat.id
	print("Received request to send images from {} in chat {}".format(context.args[0], chat_id))
	quantity = int(context.args[1])
	# The subreddit is the first parameter of the command (n_ 0)
	sub = context.args[0]
	SendPhotos(update, context, GetUrlsList(quantity, sub))

dispatcher.add_handler(CommandHandler("send", send))

# ------------------------------------------------------------------------------------------------
def advSend(update, context):
	try:
		print("User using the advanced mode (chat ID {})".format(update.effective_chat.id))
		sub = context.args[0]
		amount = int(context.args[1])
		min_ups = int(context.args[2])
		print("\tRequested {} images from {} with min_ups {}.".format(amount, sub, min_ups))
		SendPhotos(update, context, GetUrlsList(amount, sub, min_ups=min_ups))
	except:
		print("Advanced mode went wrong.")
		context.bot.send_message(chat_id=update.effective_chat.id, text="Incorrect parameters.")

dispatcher.add_handler(CommandHandler("advsend", advSend))

# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------

# When a button is pressed, this function is called. It evaluates the callback_data and responds
# depending on it. Edit message means that it removes the menu that was there before.
def OnButtonPress(update, context):
	query = update.callback_query
	# List of suggested subreddits
	suggestions_list = GetSuggestionsList()
	# Get config data to format menus correctly
	cf_parser.read('config.ini')

	# Based on the callback_data (query.data / update.callback_query.data), determine action.
	if query.data == "other":
		# Redirect user to command /send <subreddit> <amount>
		other_explanation = """
		-----------------
		Use /send <subreddit> <amount> to receive the <amount> top imagesfrom <subreddit>.\n
		By default this filters out everything under {} upvotes, use advanced mode to change this.
		-----------------
		""".format(MINUPS)
		context.bot.send_message(chat_id=update.effective_chat.id, text=other_explanation)

	elif query.data == "advanced":
		# Redirect user to /advSend <subreddit> <amount> <min_ups>
		adv_string = """
		-----------------
		Use /advsend <subreddit> <amount> <min.upvotes> to receive <amount> images from <subreddit>, filtering out everything below <min.upvotes> upvotes. \n
		Example: /advsend memes 15 5000 would send the 15 top images from r/memes filtering out those below 5000 upvotes. \n
		-----------------
		"""
		context.bot.send_message(chat_id=update.effective_chat.id, text=adv_string)

	elif query.data == "suggest":
		print("User requested suggestions menu.")
		suggestion_menu_columns = int(cf_parser['MENUS_OPTIONS']['suggestions_columns'])
		suggest_menu_markup = SuggestionsMenu(GetSuggestionsList(), columns=suggestion_menu_columns)
		query.edit_message_text(text="Options:", reply_markup=suggest_menu_markup)
		print("Suggestions menu shown in chat {}.".format(update.effective_chat.id))

	elif query.data == "return":
		query.edit_message_text(text="Closing. Use /start to open menu again if needed.")

	# If this comes from suggestions or "send memes", open menu to choose amount
	elif query.data in suggestions_list or query.data == "memes":
		quantity_menu_columns = int(cf_parser['MENUS_OPTIONS']['quantities_columns'])
		query.edit_message_text(text="Amount?",
			reply_markup=QuantityMenu(query.data, columns=quantity_menu_columns))

	# If it isn't any of the above, it's something to choose quantity for something from suggestions.
	# Callback data will be a string, "sub <space> amount"
	else:
		try:
			suggested_sub = str(query.data.split()[0])
			chosen_amount = int(query.data.split()[1])
			print("Sending: \n\tSub = {} \n\tamount = {}".format(suggested_sub, chosen_amount))
			print("\t(Chat ID = {})".format(update.effective_chat.id))
			minUps = int(cf_parser['REDDIT_FILTERS']['min_ups'])
			SendPhotos(update, context, GetUrlsList(chosen_amount, suggested_sub, min_ups=minUps))
		except:
			print("Exception!")
			print("Couldn't do anything with callback data. Callback data: {}".format(query.data))
			print("")


dispatcher.add_handler(CallbackQueryHandler(OnButtonPress))

# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------

# Start the bot ----------------------------------------------------------------------------------
print("Bot starting to poll")
updater.start_polling()
print("")