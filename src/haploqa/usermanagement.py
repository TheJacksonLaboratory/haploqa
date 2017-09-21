from email.mime.text import MIMEText
import flask
from haploqa.config import HAPLOQA_CONFIG
import haploqa.mongods as mds
from hashlib import sha512
from os import EX_USAGE
import smtplib
import socket
from uuid import uuid4


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
            return user
        else:
            return None
    else:
        return None

def invite_user(email_address, db=None):
    '''
    invite regular user
    :param email_address:
    :param db:
    :return:
    '''
    if db is None:
        db = mds.get_db()

    email_address = email_address.strip()

    #check and see if user already exists first
    user = db.users.find_one({
        'email_address_lowercase': email_address.strip().lower(),
    })

    if user is None:
        password_reset_id = str(uuid4())
        db.users.insert({
            'email_address': email_address,
            'email_address_lowercase': email_address.lower(),
            'administrator': False,
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

        from_addr = noreply_address()
        msg['Subject'] = 'Confirm HaploQA Account'
        msg['From'] = from_addr
        msg['To'] = email_address

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        '''s = smtplib.SMTP(HAPLOQA_CONFIG['SMTP_HOST'], HAPLOQA_CONFIG['SMTP_PORT'])
        s.sendmail(from_addr, [email_address], msg.as_string())
        s.quit()'''
        print(msg)
        return True
    else:
        return None

def get_all_users(db=None):
    if db is None:
        db = mds.get_db()
    #check for admin here
    return db.users.find()


#TODO: should probably change this method to allow user type to invite
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

        from_addr = noreply_address()
        msg['Subject'] = 'Confirm HaploQA Account'
        msg['From'] = from_addr
        msg['To'] = email_address

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP(HAPLOQA_CONFIG['SMTP_HOST'], HAPLOQA_CONFIG['SMTP_PORT'])
        s.sendmail(from_addr, [email_address], msg.as_string())
        s.quit()
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

        from_addr = noreply_address()
        msg['Subject'] = 'Reset password request for HaploQA'
        msg['From'] = from_addr
        msg['To'] = user['email_address']

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        '''s = smtplib.SMTP(HAPLOQA_CONFIG['SMTP_HOST'], HAPLOQA_CONFIG['SMTP_PORT'])
        s.sendmail(from_addr, [user['email_address']], msg.as_string())
        s.quit()'''
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