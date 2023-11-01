from datetime import datetime
import logging
from sqlalchemy import insert, create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d.%m.%y %H:%M:%S', level=logging.INFO)


class EditDB:
    def __init__(self, config):
        self.db_engine = create_engine(
            f"mysql+mysqlconnector://{config['MYSQL_USER']}:{config['MYSQL_PASSWORD']}@172.20.0.2:3306/{config['MYSQL_DATABASE']}")
        Session = sessionmaker()
        Session.configure(bind=self.db_engine)
        self.session = Session()
        self.session_time = datetime.now()

        metadata = MetaData()
        self.users = Table('users', metadata, autoload_with=self.db_engine)
        self.principals = Table('principals', metadata, autoload_with=self.db_engine)
        self.addressbooks = Table('addressbooks', metadata, autoload_with=self.db_engine)
        self.cards = Table('cards', metadata, autoload_with=self.db_engine)

    def add_users(self, user_list):
        users = self.get_users()
        users = [user[1].decode('utf-8') for user in users]
        execute_users = [{"username": f"{i['sAMAccountName'][0]}".encode('utf-8'),
                          "digesta1": "ebc4d2b939b59d813e2a30feb59d2c07".encode('utf-8')} for i in user_list if
                         i['sAMAccountName'][0] not in users]
        execute_principals = [{"uri": f"principals/{i['sAMAccountName'][0]}".encode('utf-8'),
                               "email": f"{i['mail'][0]}".encode('utf-8'),
                               "displayname": i['cn'][0]} for i in user_list if i['sAMAccountName'][0] not in users]
        execute_addressbooks = [{"principaluri": f"principals/{i['sAMAccountName'][0]}".encode('utf-8'),
                                 "displayname": "Docrobot",
                                 "uri": "default".encode('utf-8'),
                                 "description": "Default Address Book"} for i in user_list if
                                i['sAMAccountName'][0] not in users]
        if execute_users:
            self.session.execute(insert(self.users), execute_users)
            self.session.execute(insert(self.principals), execute_principals)
            self.session.execute(insert(self.addressbooks), execute_addressbooks)
        self.session.commit()

    def add_user(self, sam, mail, displayname):
        self.session.execute(
            insert(self.users),
            [
                {"username": f'{sam}'.encode('utf-8'),
                 "digesta1": "ebc4d2b939b59d813e2a30feb59d2c07".encode('utf-8')},
            ],
        )
        self.session.execute(
            insert(self.principals),
            [
                {"uri": f"principals/{sam}".encode('utf-8'),
                 "email": f"{mail}".encode('utf-8'),
                 "displayname": f"{displayname}"},
            ],
        )
        self.session.execute(
            insert(self.addressbooks),
            [
                {"principaluri": f"principals/{sam}".encode('utf-8'),
                 "displayname": "Docrobot",
                 "uri": "default".encode('utf-8'),
                 "description": "Default Address Book",
                 },
            ],
        )

        self.session.commit()
        logging.info(f"{sam} загружен в Baikal DB")

    def get_users(self, sam=''):
        if not sam:
            users = self.session.query(self.users).all()
        else:
            users = self.session.query(self.users).filter_by(username=f"{sam}".encode('utf-8')).all()
        return users

    def get_contacts(self, sam):
        addressbook = self.session.query(self.addressbooks).filter_by(
            principaluri=f"principals/{sam}".encode('utf-8')).all()
        contacts = self.session.query(self.cards).filter_by(addressbookid=addressbook[0][0]).all()
        contacts_array = [contact[3].decode("utf-8").replace(".vcf", "") for contact in contacts]
        return contacts_array
