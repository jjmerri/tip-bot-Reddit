# Reddit TIPs Bot

## User Guide

#### What is a TIP?
A TIP is a Totaly Imaginary Point. They have no monetary value and they exist solely to show appreciation for comments and posts on Reddit.

#### What is the point of the Reddit TIP Bot?
The Reddit TIP Bot was made so you can show your appreciation for a user's post or comment when an upvote is not enough and Reddit Gold is too much. Simply tag the bot with the amount you want tip and that amount will come out of your account and transfer to the user you tipped.

#### How do I get more TIPs?
Everyone starts off with an account containing 20 TIPs. You get more tips by receiving them from other users. Once a week your account balance will be set back to 20 TIPs if your account contains less than 20 TIPs. This currently happens on Monday night at 8PM EST.

#### Commands
##### /u/RedditTIPsBot +{amount}
This is the main command. Use it by making a comment with the command in it. The command does not have to be the only text in the comment but it can be. It will deduct the amount of TIPs specified from your account and send that amount to the user you are making a comment to.

Example:

    /u/RedditTIPsBot +2

##### !ACCOUNT
The Account command retrieves information about your account. Use it by sending a PM to RedditTIPsBot. It returns balance information as well is information on how many TIPs you have sent and received.

Example:

    !ACCOUNT

## Technical Stuff

#### Version Requirements

Python = 3.6.4

PRAW = 5.4

#### Configuration

tip_bot.cfg contains all usernames and passwords as well as environment specific configurations needed to run the Python scripts. When the environment is set to DEV some functionality is turned off in order to avoid processing real data. When the environment is set to DEV the .running files will be removed before startup. It is expected that your DEV database is different than your production database.

#### tip_bot.py

This script is responsible for finding comments and PMs that should be processed by the bot. If the comment contains a tip command then it will attempt to make the TIPs transfer, record it in the database, and send a confirmation reply.

On startup this script checks for a .running file and if found, immediately terminates to prevent multiple instances from running in parallel. If no .running file is found then it creates one and begins normal processing. It will stay running until the .running file is removed at which time it will shut down gracefully.

#### tips_manager.py

This script contains the helper methods that interact with a user's account.

#### schema.sql

This file contains the database schema. It is to be run only on database initialization to create the necessary objects. It drops the current database if it exists so it should never be run in production except on database creation.

#### Database

A MySql database with the following objects:

* Tables
	* account - contains the accounts and balances
	* tip_transaction - contains records of the tip transactions
