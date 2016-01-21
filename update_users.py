# this simple script updates the old DB format such that it is now able to deal with
# case-insensitive email addresses
import pymongo


def get_db():
    """
    Gets a reference to the HaploQA database
    :return: the DB
    """
    client = pymongo.MongoClient('localhost', 27017)
    return client.haploqa


def main():
    db = get_db()
    db.users.drop_indexes()
    for user in db.users.find({'email_address_lowercase': {'$exists': False}}, {'email_address': 1}):
        db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'email_address_lowercase': user['email_address'].strip().lower()}}
        )

    db.users.create_index('email_address_lowercase', unique=True)
    db.users.create_index('password_reset_hash')


if __name__ == '__main__':
    main()
