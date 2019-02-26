DROP SCHEMA IF EXISTS raffle_tip;
CREATE SCHEMA raffle_tip;
USE raffle_tip;

CREATE TABLE `account` (
  `acct_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `balance` DECIMAL(18,9) NOT NULL,
  `create_timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `update_timestamp` TIMESTAMP DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`acct_id`),
  UNIQUE KEY(`username`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `tip_transaction` (
  `trns_id` int(11) NOT NULL AUTO_INCREMENT,
  `to_acct_id` int(11) NOT NULL,
  `from_acct_id` int(11) NOT NULL,
  `amount` DECIMAL(18,9) NOT NULL,
  `context` varchar(400) NOT NULL,
  `parent_permalink` varchar(400) NOT NULL,
  `create_timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ,
  PRIMARY KEY (`trns_id`),
  FOREIGN KEY (`to_acct_id`)
        REFERENCES account(`acct_id`)
        ON DELETE CASCADE,
  FOREIGN KEY (`from_acct_id`)
        REFERENCES account(`acct_id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
