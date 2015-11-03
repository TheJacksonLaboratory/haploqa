from email.mime.text import MIMEText
import flask
import haploqa.mongods as mds
from hashlib import sha512
from os import EX_USAGE
import smtplib
import socket
from uuid import uuid4


MIN_PASSWORD_LENGTH = 8


def hash_str(s):
    return sha512(s.encode('utf-8')).hexdigest()


# def app_server_name():
#     # try to look up the server name using flask's configuration
#     server_name = None
#     if app is not None:
#         server_name = app.config['SERVER_NAME']
#
#     # if that fails we can look up the fully qualified domain name
#     if not server_name:
#         server_name = socket.getfqdn()
#
#     return server_name


def noreply_address():
    return 'no-reply@' + socket.getfqdn()


def lookup_user(email_address, db):
    return db.users.find_one({
        'email_address': email_address
    }, {
        # exclude authentication data for added security
        'password_hash': 0,
        'password_reset_hash': 0,
        'salt': 0,
    })


def lookup_salt(email_address, db):
    salt_dict = db.users.find_one({'email_address': email_address, 'salt': {'$exists': 1}}, {'salt': 1})
    if salt_dict is not None:
        return salt_dict['salt']
    else:
        return None


def authenticate_user(email_address, password, db):
    user = db.users.find_one({
        'email_address': email_address
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


def invite_admin(email_address, db=None):
    if db is None:
        db = mds.get_db()

    password_reset_id = str(uuid4())
    db.users.insert({
        'email_address': email_address,
        'administrator': True,
        'password_reset_hash': hash_str(password_reset_id),
    })

    msg_template = \
        '''You have been invited by to be an administrator of the HaploQA application. ''' \
        '''To validate your account and create a password, visit this link: {} ''' \
        '''Please ignore this message if it was sent in error.'''
    msg = MIMEText(msg_template.format(flask.url_for('validate_reset', password_reset_id=password_reset_id)))

    from_addr = noreply_address()
    msg['Subject'] = 'Confirm HaploQA Account'
    msg['From'] = from_addr
    msg['To'] = email_address

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_addr, [email_address], msg.as_string())
    s.quit()


def reset_password(email_address, db=None):
    if db is None:
        db = mds.get_db()

    password_reset_id = str(uuid4())
    db.users.update_one(
        {'email_address': email_address},
        {'$set': {'password_reset_hash': hash_str(password_reset_id)}}
    )

    msg_template = \
        '''Someone has attempted to reset your password for the HaploQA application. ''' \
        '''To validate this request follow this link: {} ''' \
        '''Please ignore this message if it was sent in error.'''
    msg = MIMEText(msg_template.format(flask.url_for('validate_reset', password_reset_id=password_reset_id)))

    from_addr = noreply_address()
    msg['Subject'] = 'Reset password request for HaploQA'
    msg['From'] = from_addr
    msg['To'] = email_address

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_addr, [email_address], msg.as_string())
    s.quit()


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

    salt = str(uuid4())
    db.users.insert({
        'email_address': email_address,
        'administrator': True,
        'salt': salt,
        'password_hash': hash_str(password + salt),
    })


def main():
    print('Creating a new admin user...')
    email = input('E-mail Address: ')
    password = input('password: ')
    if len(password) < MIN_PASSWORD_LENGTH:
        print('Please use a password containing at least {} characters.'.format(MIN_PASSWORD_LENGTH))
        exit(EX_USAGE)
    else:
        _create_admin(email, password)

if __name__ == '__main__':
    main()