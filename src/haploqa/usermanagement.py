from email.mime.text import MIMEText
import flask
from haploqa.config import HAPLOQA_CONFIG
import haploqa.mongods as mds
from hashlib import sha512
from os import EX_USAGE
from smtplib import SMTP
import socket
from uuid import uuid4
import datetime
import logging

logging.basicConfig(level=logging.DEBUG)


def hash_str(s):
    return sha512(s.encode('utf-8')).hexdigest()


def noreply_address():
    return 'no-reply@' + socket.getfqdn()


def lookup_user(email_address, db):
    return db.users.find_one({
        'email_address_lowercase': email_address.strip().lower()
    }, {
        # exclude authentication data for added security (avoid the data leaking out)
        'password_hash': 0,
        'password_reset_hash': 0,
        'salt': 0,
    })


def lookup_salt(email_address, db):
    """
    lookup and return a user's password salt
    """
    salt_dict = db.users.find_one(
            {'email_address_lowercase': email_address.strip().lower(), 'salt': {'$exists': 1}},
            {'salt': 1})
    if salt_dict is not None:
        return salt_dict['salt']
    else:
        return None


def sendmail(msg):
    """
    Sends an email to the specified email address with the specified message content
    :param msg: the msg content (includes to, from, and subject)
    :return:
    """

    smtp_host = HAPLOQA_CONFIG['SMTP_HOST']
    smtp_port = HAPLOQA_CONFIG['SMTP_PORT']

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = SMTP(smtp_host, smtp_port)

    try:
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
    except Exception as e:
        logging.debug(e)
    finally:
        s.quit()


def switch_user_privs(email_address, user_type):
    """
    updates a users status
    :param email_address: the email address of the user to update
    :param user_type: regular, curator, admin
    :return: true on success, None upon failure
    """

    is_admin = True if (user_type == "administrator") else False
    is_curator = True if (user_type == "curator") else False

    db = mds.get_db()

    user = db.users.find_one({
        'email_address_lowercase': email_address.strip().lower(),
    })

    if user is not None:
        db.users.update_one({'_id': user['_id']},
                            {'$set': {
                                'administrator': is_admin,
                                'curator': is_curator
                            }}
                            )
        return True
    else:
        return None


def remove_user(email_address):
    """
    remove a user from the system
    :param email_address: the email address of the user to remove
    :return: true on success, None upon failure
    """

    db = mds.get_db()

    user = db.users.find_one({
        'email_address_lowercase': email_address.strip().lower(),
    })

    if user is not None:
        db.users.delete_one({'_id': user['_id']})
        return True
    else:
        return None


def authenticate_user(email_address, password, db):
    """
    Perform password authentication for a user
    :param email_address: the email address to authenticate
    :param password: the password to check
    :param db: the database
    :return: the user dict from mongo upon success and None upon failure
    """
    user = db.users.find_one({
        'email_address_lowercase': email_address.strip().lower(),
    }, {
        'password_reset_hash': 0,
    })
    if user is not None:
        password_hash = hash_str(password + user['salt'])
        if password_hash == user['password_hash']:
            # remove the password_hash to prevent it from leaking out
            user.pop('password_hash', None)
            user.pop('salt', None)
            # record login timestamp
            ts = '{:%m/%d/%Y %H:%M %p}'.format(datetime.datetime.now())
            db.users.update_one({'_id': user['_id']}, {'$set': {'last_login': ts}})
            return user
        else:
            return None
    else:
        return None


def authenticate_user_hash(email_address, hash_id, db):
    """
    Perform authentication for a user using a hash_id instead of password
    :param email_address: the email address to authenticate
    :param hash_id: the hash to check
    :param db: the database
    :return: the user dict from mongo upon success or None upon failure
    """
    user = db.users.find_one({
        'email_address_lowercase': email_address.strip().lower(),
    }, {
        'password_reset_hash': 0,
    })
    if user is not None:
        if hash_id == user['password_hash']:
            # remove the password_hash to prevent it from leaking out
            user.pop('password_hash', None)
            user.pop('salt', None)
            # record login timestamp
            ts = '{:%m/%d/%Y %H:%M %p}'.format(datetime.datetime.now())
            db.users.update_one(
                {'_id': user['_id']},
                {'$set': {
                    'last_login': ts
                }}
            )

            return user
        else:
            return None
    else:
        return None


def create_account(email_address, password, affiliation, db=None):
    """
    invite regular user
    :param email_address:
    :param password:
    :param affiliation
    :param db:
    :return:
    """
    if db is None:
        db = mds.get_db()

    email_address = email_address.strip()

    # check and see if user already exists first
    user = db.users.find_one({
        'email_address_lowercase': email_address.strip().lower(),
    })

    if user is None:
        ts = '{:%m/%d/%Y %H:%M %p}'.format(datetime.datetime.now())
        new_salt = str(uuid4())

        db.users.insert({
            'created': ts,
            'email_address': email_address,
            'email_address_lowercase': email_address.lower(),
            'affiliation': affiliation,
            'administrator': False,
            'salt': new_salt,
            'password_hash': hash_str(password + new_salt),
            'validated': False
        })

        send_validation_email(email_address, db)
        return True

    else:
        return None


def send_validation_email(email_address, db=None):
    new_account_msg_template = \
        '''An account for HaploQA has been created for this email address. ''' \
        '''If you have requested an account to be made, ''' \
        '''please follow this link to validate your account: {} ''' \
        '''If you did not request an account, please ignore this email.'''

    existing_account_msg_template = \
        '''Thank you for using HaploQA! We're asking all of our existing ''' \
        '''users to validate their account. To do this, simply follow this ''' \
        '''link: {} If you have any questions or concern about this request, ''' \
        '''let us know at haploqa@jax.org! If you do not have an account, ''' \
        '''please ignore this email.'''

    if db is None:
        db = mds.get_db()

    user = db.users.find_one({
        'email_address_lowercase': email_address.strip().lower(),
    })

    # double check that the user is legit
    if user is not None:
        msg_content = None
        subject = None

        # if user doesn't have a validated field, this indicates that it's an
        # existing account and send an existing account message
        if 'validated' not in user:
            msg_content = existing_account_msg_template
            subject = 'Validate your HaploQA Account'

        # if user isn't validated, this indicates that it's a new account
        # and send a new account message
        elif user['validated'] is False:
            msg_content = new_account_msg_template
            subject = 'Welcome to HaploQA'

        else:
            logging.debug('We are trying to validate an already validated account')

        msg = MIMEText(msg_content.format(flask.url_for('validate_account',
                                                        hash_id=user['password_hash'],
                                                        _external=True)))

        msg['Subject'] = subject
        msg['From'] = noreply_address()
        msg['To'] = email_address

        sendmail(msg)


def get_all_users(db=None):
    if db is None:
        db = mds.get_db()
    return db.users.find()


def invite_admin(email_address, db=None):
    """
    invite a new user with the given email address (sends out an invite email via an SMTP server)
    :param email_address: the address of the user to invite
    :param db: the mongo database
    """

    if db is None:
        db = mds.get_db()

    email_address = email_address.strip()

    user = db.users.find_one({
        'email_address_lowercase': email_address.strip().lower(),
    })

    if user is None:
        password_reset_id = str(uuid4())
        db.users.insert({
            'email_address': email_address,
            'email_address_lowercase': email_address.lower(),
            'administrator': True,
            'password_reset_hash': hash_str(password_reset_id),
        })

        msg_template = \
            '''You have been invited to create a HaploQA account. ''' \
            '''To validate your account and create a password, visit this link: {} ''' \
            '''Please ignore this message if it was sent in error.'''
        msg = MIMEText(msg_template.format(flask.url_for(
            'validate_reset',
            password_reset_id=password_reset_id,
            _external=True)))

        msg['Subject'] = 'Confirm HaploQA Account'
        msg['From'] = noreply_address()
        msg['To'] = email_address

        sendmail(msg)

    else:
        return None


def reset_password(email_address, db=None):
    """
    Reset password for user with the given email address (sends out a reset email via an SMTP
    server). If the user does not follow the link from the email that's sent out
    this should have no effect.
    :param email_address: the address of the user to invite
    :param db: the mongo database
    """

    if db is None:
        db = mds.get_db()

    password_reset_id = str(uuid4())
    user = db.users.find_one_and_update(
        {'email_address_lowercase': email_address.strip().lower()},
        {'$set': {'password_reset_hash': hash_str(password_reset_id)}}
    )
    if user is None:
        return None

    else:
        msg_template = \
            '''Someone has attempted to reset your password for the HaploQA application. ''' \
            '''To validate this request follow this link: {} ''' \
            '''Please ignore this message if it was sent in error.'''
        msg = MIMEText(msg_template.format(flask.url_for(
            'validate_reset',
            password_reset_id=password_reset_id,
            _external=True)))

        msg['Subject'] = 'Reset password request for HaploQA'
        msg['From'] = noreply_address()
        msg['To'] = user['email_address']

        sendmail(msg)
        return True


def _create_admin(email_address, password, db=None):
    """
    This method is just used to create the first admin user (all of the rest can be
    created by using the "invite admin" functionality of the web interface)
    :param email_address:
    :param password:
    :param db:
    :return:
    """
    if db is None:
        db = mds.get_db()

    email_address = email_address.strip()

    salt = str(uuid4())
    db.users.insert({
        'email_address': email_address,
        'email_address_lowercase': email_address.lower(),
        'administrator': True,
        'salt': salt,
        'password_hash': hash_str(password + salt),
    })


def main():
    """
    Use this main function for creating the 1st admin user. After the 1st user is
    created you can use the web interface to invite new users.
    """
    print('Creating a new admin user...')
    email = input('E-mail Address: ')
    password = input('password: ')
    if len(password) < HAPLOQA_CONFIG['MIN_PASSWORD_LENGTH']:
        print('Please use a password containing at least {} characters.'.format(HAPLOQA_CONFIG['MIN_PASSWORD_LENGTH']))
        exit(EX_USAGE)
    else:
        _create_admin(email, password)


if __name__ == '__main__':
    main()
