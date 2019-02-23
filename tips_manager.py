import MySQLdb
import configparser
from decimal import Decimal


# Reads the config file
config = configparser.ConfigParser()
config.read("tip_bot.cfg")

DB_USER = config.get("SQL", "user")
DB_PASS = config.get("SQL", "passwd")
DB_HOST = config.get("SQL", "host")
DB_DATABASE = config.get("SQL", "database")

INITIAL_ACCOUNT_AMOUNT = 20

class DbConnection(object):
    """
    DB connection class
    """
    connection = None
    cursor = None

    def __init__(self):
        self.connection = MySQLdb.connect(
            host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_DATABASE
        )
        self.cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)

def get_account(username):
    """
    gets the user's account
    :param username: the username elonging to the account that will be retrieved
    :return: the account table row identified by the username
    """
    db_connection = DbConnection()
    query = "SELECT * FROM account WHERE username = %s"
    db_connection.cursor.execute(query, [username])
    account = db_connection.cursor.fetchall()
    db_connection.connection.close()

    if account:
        return account[0]
    else:
        return None

def get_account_balance(username):
    account = get_account(username)
    return account['balance']

def initialize_account(username):
    """
    If the account doesnt exist then create it with the default balance
    :param username: username the account belongs to
    """

    account = get_account(username)

    if not account:
        db_connection = DbConnection()

        query = "INSERT INTO account (username, balance) VALUES (%s, %s)"
        db_connection.cursor.execute(query, [username, INITIAL_ACCOUNT_AMOUNT])

        db_connection.connection.commit()
        db_connection.connection.close()

def send_tip(to_user, from_user, amount, context):
    """
    sends a tip to to_user from from_user in the amount of amount
    :param to_user: user receiveing the tip
    :param from_user: user sending the tip
    :param amount: amount of tip being sent
    """
    if not has_sufficient_funds(from_user, amount):
        return False

    from_account = get_account(from_user)
    to_account = get_account(to_user)

    from_account_balance = Decimal(from_account["balance"])
    to_account_balance = Decimal(to_account["balance"])

    db_connection = DbConnection()
    update_account_query = "UPDATE account SET balance = %s WHERE username = %s"
    db_connection.cursor.execute(update_account_query, [to_account_balance + amount, to_user])
    db_connection.cursor.execute(update_account_query, [from_account_balance - amount, from_user])

    tip_transaction_query = "INSERT INTO tip_transaction (to_acct_id, from_acct_id, amount, context) VALUES (%s, %s, %s, %s)"
    db_connection.cursor.execute(tip_transaction_query, [to_account["acct_id"], from_account["acct_id"], amount, context])

    db_connection.connection.commit()
    db_connection.connection.close()

    return True

def has_sufficient_funds(username, amount):
    """
    Checks if the account owned by username has a balance >= amount
    :param username: owner of the account
    :param amount: the amount to check against the balance
    :return true if the account balance is >= amount
    """

    account = get_account(username)
    return account and Decimal(account["balance"]) >= Decimal(amount)

def get_total_tips_sent(username):
    """
    gets the total amount of tips the user sent
    :param username: the username we are getting the sent tips for
    :return: total tips sent by username
    """
    db_connection = DbConnection()
    query = "SELECT SUM(amount) as total FROM tip_transaction JOIN account on tip_transaction.from_acct_id = account.acct_id WHERE account.username = %s"
    db_connection.cursor.execute(query, [username])
    result = db_connection.cursor.fetchall()
    db_connection.connection.close()

    total = Decimal(0)
    if result and result[0]['total']:
        total = result[0]['total']

    return total

def get_total_tips_received(username):
    """
    gets the total amount of tips the user received
    :param username: the username we are getting the tips received for
    :return: total tips sent by username
    """
    db_connection = DbConnection()
    query = "SELECT SUM(amount) as total FROM tip_transaction JOIN account on tip_transaction.to_acct_id = account.acct_id WHERE account.username = %s"
    db_connection.cursor.execute(query, [username])
    result = db_connection.cursor.fetchall()
    db_connection.connection.close()

    total = Decimal(0)
    if result and result[0]['total']:
        total = result[0]['total']

    return total
