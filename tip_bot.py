#!/usr/bin/env python3.6

# =============================================================================
# IMPORTS
# =============================================================================
import praw
import datetime
import re
from decimal import Decimal
import configparser
import logging
import time
import os
import sys
from email.mime.text import MIMEText
import smtplib
from enum import Enum
import tips_manager

# =============================================================================
# GLOBALS
# =============================================================================

# Reads the config file
config = configparser.ConfigParser()
config.read("tip_bot.cfg")

bot_username = config.get("Reddit", "username")
bot_password = config.get("Reddit", "password")
client_id = config.get("Reddit", "client_id")
client_secret = config.get("Reddit", "client_secret")

# Reddit info
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=bot_password,
                     user_agent='Tip Bot by /u/BoyAndHisBlob',
                     username=bot_username)

ENVIRONMENT = config.get("TIP_BOT", "environment")
DEV_EMAIL = config.get("TIP_BOT", "dev_email")
DEV_USER_NAME = config.get("TIP_BOT", "dev_user")

EMAIL_SERVER = config.get("Email", "server")
EMAIL_USERNAME = config.get("Email", "username")
EMAIL_PASSWORD = config.get("Email", "password")

RUNNING_FILE = "tip_bot.running"

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('tip_bot')
logger.setLevel(logging.INFO)

documentation_link = "https://github.com/jjmerri/tip-bot-reddit"
reply_footer = '\n\n---\n\n[^(Account Info)](https://www.reddit.com/message/compose/?to={bot_username}&subject=Account%20Info&message=!ACCOUNT) ^| [^(Give Feedback)](https://www.reddit.com/message/compose/?to={DEV_USER_NAME}&subject=Feedback) ^| [^(Bot Info)]({documentation_link}) ^| [^(Tip {DEV_USER_NAME})](https://blobware-tips.firebaseapp.com)\n\n^(This bot is maintained and hosted by {DEV_USER_NAME}.)' \
    .format(
    DEV_USER_NAME=DEV_USER_NAME,
    documentation_link=documentation_link,
    bot_username=bot_username
)



# =============================================================================
# CLASSES
# =============================================================================
class ParseMessageStatus(Enum):
    SUCCESS = 1
    SYNTAX_ERROR = 2


class CommandType(Enum):
    SEND_TIP = 1
    UNKNOWN = 2
    ACCOUNT_INFO = 3


class CommandRegex:
    send_tip_regex = r'/?u/{bot_username}[ ]+\+(?P<amount>([\d]*\.?[\d]+))'.format(bot_username=bot_username)
    account_info_regex = r'!account'

def send_dev_pm(subject, body):
    """
    sends a PM to the dev's Reddit account
    :param subject: subject of the PM
    :param body: body of the PM
    """
    reddit.redditor(DEV_USER_NAME).message(subject, body)


def send_email(subject, body, email_addresses):
    """
    sends an email
    :param subject: subject of the email
    :param body: body of the email
    :param email_addresses: recipient email addresses
    """
    sent_from = DEV_EMAIL

    msg = MIMEText(body.encode('utf-8'), 'plain', 'UTF-8')
    msg['Subject'] = subject

    server = smtplib.SMTP_SSL(EMAIL_SERVER, 465)
    server.ehlo()
    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    server.sendmail(sent_from, email_addresses, msg.as_string())
    server.close()


def check_mentions():
    """
    go through the comments mentioning the bot process them
    """
    for message in reddit.inbox.unread(limit=None):
        # Mark Read first in case there is an error we dont want to keep trying to process it
        message.mark_read()
        tips_manager.initialize_account(message.author.name)
        if message.was_comment:
            tips_manager.initialize_account(message.parent().author.name)
            process_mention(message)
        else:
            process_pm(message)

def process_pm(message):
    """
    process the command in the message by determining the command and delegating the processing
    :param message: the Reddit comment containing the command
    """
    command = get_command(message.body)

    if CommandType.ACCOUNT_INFO == command:
        process_account_info_command(message)


def process_mention(mention):
    """
    process the command in the mention by determining the command and delegating the processing
    :param mention: the Reddit comment containing the command
    """
    command = get_command(mention.body)

    if CommandType.SEND_TIP == command:
        process_send_tip_command(mention)
    elif mention.parent().author.name != bot_username:
        mention.reply("I could not find a valid command in your comment. Please try again with the correct syntax.\n\n"
                      "Example:\n\n    /u/{bot_username} +2{reply_footer}".format(bot_username=bot_username, reply_footer=reply_footer))

def process_account_info_command(message):
    """
    retreives the user's account info and sends it to the user
    :param message: the Reddit PM containing the command
    """
    account_balance = tips_manager.get_account_balance(message.author.name)
    total_sent = tips_manager.get_total_tips_sent(message.author.name)
    total_received = tips_manager.get_total_tips_received(message.author.name)

    message.reply('Account Balance: {account_balance}\n\n'
                  'Total Sent: {total_sent}\n\n'
                  'Total Received: {total_received}{reply_footer}'.format(account_balance=format(account_balance, '.2f'),
                                                            total_sent=format(total_sent, '.2f'),
                                                            total_received=format(total_received, '.2f'),
                                                            reply_footer=reply_footer))

def process_send_tip_command(mention):
    """
    parses the Reddit comment in mention and send the tip if applicable
    :param mention: the Reddit comment containing the tip command
    """
    send_tip_match = re.search(CommandRegex.send_tip_regex, mention.body, re.IGNORECASE)

    parentcomment = mention.parent()

    if parentcomment and parentcomment.author and mention.author and send_tip_match and send_tip_match.group("amount"):
        try_send_tip(mention, parentcomment.author.name, mention.author.name, Decimal(send_tip_match.group("amount")))


def try_send_tip(mention, to_user, from_user, amount):
    """
    send tip amount to to_user from from_user
    :param mention: the Reddit comment containing the tip command
    :param to_user: username of the person who is receiving the tip
    :param from_user: username of the person who is sending the tip
    :param amount: amount of tip being sent
    """
    if to_user == from_user:
        mention.reply("You can tip yourself all you want in the comfort of your own home but I won't allow it here. "
                      "**Request DENIED!**{reply_footer}".format(reply_footer=reply_footer)
                      )
        return
    elif amount < Decimal(".1"):
        mention.reply("Way to dig deep there big spender! All tips must be >= .1 TIPs. "
                      "**Request DENIED!**{reply_footer}".format(reply_footer=reply_footer)
                      )
        return
    elif amount > 10:
        mention.reply("Easy there big fella! All tips must be 10 TIPs or less. "
                      "We don't want to dilute the market and make these TIPs even more worthless. **Request DENIED!**"
                      "{reply_footer}".format(reply_footer=reply_footer)
                      )
        return

    if tips_manager.send_tip(to_user, from_user, amount, mention):
        total_sent = tips_manager.get_total_tips_sent(from_user)
        total_received = tips_manager.get_total_tips_received(to_user)
        mention.reply('Thanks {from_user}, you have sent **{amount}** TIPs to **{to_user}**.\n\n'
                      'You have sent a total of {total_sent} TIPs.\n\n'
                      '{to_user} has received a total of {total_received} TIPs.{reply_footer}'
            .format(
                to_user=to_user,
                from_user=from_user,
                amount=str(amount),
                reply_footer=reply_footer,
                total_sent=format(total_sent, '.2f'),
                total_received=format(total_received, '.2f')
            )
        )
    else:
        mention.reply('You do not have sufficient funds to send that tip. How embarrassing for you.{reply_footer}'
                        .format(reply_footer=reply_footer)
                    )

def get_command(mention_text):
    """
    parses mention_text to find out what command it contains
    :param mention_text: the text to be searched for a command
    :return returns a CommandType representing the command in the mention_text
    """
    send_tip_match = re.search(CommandRegex.send_tip_regex, mention_text, re.IGNORECASE)
    account_info_match = re.search(CommandRegex.account_info_regex, mention_text, re.IGNORECASE)

    if send_tip_match:
        return CommandType.SEND_TIP
    elif account_info_match:
        return CommandType.ACCOUNT_INFO
    else:
        return CommandType.UNKNOWN


def create_running_file():
    """
    creates a file that exists while the process is running
    """
    running_file = open(RUNNING_FILE, "w")
    running_file.write(str(os.getpid()))
    running_file.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    start_process = False
    logger.info("start")

    if ENVIRONMENT == "DEV" and os.path.isfile(RUNNING_FILE):
        os.remove(RUNNING_FILE)
        logger.info("running file removed")

    if not os.path.isfile(RUNNING_FILE):
        create_running_file()
        start_process = True
    else:
        logger.error("tip bot already running! Will not start.")

    try:
        if datetime.datetime.today().weekday() == 0:
            logger.info("Topping off accounts")
            tips_manager.top_off_accounts()
    except Exception as err:
        logger.exception("Unknown Exception topping off accounts")
        try:
            send_email("Unknown Exception topping off accounts", "Error: {exception}".format(exception=str(err)),
                       [DEV_EMAIL])
            send_dev_pm("Unknown Exception topping off accounts", "Error: {exception}".format(exception=str(err)))
        except Exception as err:
            logger.exception("Unknown error sending dev pm or email")

    while start_process and os.path.isfile(RUNNING_FILE):
        logger.info("Start Main Loop")
        try:
            check_mentions()
            logger.info("End Main Loop")
        except Exception as err:
            logger.exception("Unknown Exception in Main Loop")
            try:
                send_email("Unknown Exception in Main Loop", "Error: {exception}".format(exception=str(err)),
                           [DEV_EMAIL])
                send_dev_pm("Unknown Exception in Main Loop", "Error: {exception}".format(exception=str(err)))
            except Exception as err:
                logger.exception("Unknown error sending dev pm or email")
        time.sleep(300)

    logger.info("end")

    sys.exit()


# =============================================================================
# RUNNER
# =============================================================================

if __name__ == '__main__':
    main()
