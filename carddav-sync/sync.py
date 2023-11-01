import os
import logging
import sys
import time
import traceback
import ldap3
from datetime import datetime
from editdb import EditDB
import carddavutil.carddav as carddav
import carddavutil.carddavutil as carddavutil


logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d.%m.%y %H:%M:%S', level=logging.INFO)


def main():
    global config
    config = read_config()

    while (True):
        sync()
        interval = int(config['SYNC_INTERVAL'])
        logging.info(f"Sync finished, sleeping {interval} seconds before next cycle")
        time.sleep(interval)


def ldap_connection():
    try:
        ldap_server = ldap3.Server(config['LDAP_URI'])
        ldap_connector = ldap3.Connection(ldap_server, user=config['LDAP_BIND_DN'],
                                          password=config['LDAP_BIND_DN_PASSWORD'])
        ldap_connector.bind()
        return ldap_connector
    except:
        ldap_results = []
        raise LdapConnection("Error connecting or generating a list of search results") from None


def ldap_search(dn):
    ldap_connector = ldap_connection()
    ldap_connector.search(search_base=dn, search_filter=config['LDAP_FILTER'],
                          search_scope=ldap3.SUBTREE,
                          attributes=['sAMAccountName', 'mail', 'sn', 'cn', 'userAccountControl', 'company',
                                      'department', 'extensionAttribute10', 'givenName', 'telephoneNumber',
                                      'mobile', 'title'])
    return ldap_connector.entries


def sync():
    ldap_results = []
    for DN in config['LDAP_BASE_DN']:
        ldap_results += ldap_search(DN)

    ad_users = [i for i in ldap_results if
                'Service' not in i.entry_dn and (False if int(i['userAccountControl'][0]) & 0b10 else True)]

    edit_db = EditDB(config)
    edit_db.add_users(ad_users)

    for ad_user in ldap_results:
        sam = ad_user['sAMAccountName'][0]
        company = ad_user['company'][0] if ad_user['company'] else ''
        birthday = ad_user['extensionAttribute10'][0] if ad_user['extensionAttribute10'] else ''
        givenName = ad_user['givenName'][0] if ad_user['givenName'] else ''
        telephoneNumber = ad_user['telephoneNumber'][0] if ad_user['telephoneNumber'] else ''
        mail = ad_user['mail'][0].lower()
        mobile = ad_user['mobile'][0] if ad_user['mobile'] else ''
        sn = ad_user['sn'][0] if ad_user['sn'] else ''
        cn = ad_user['cn'][0] if ad_user['sn'] else ''
        title = ad_user['title'][0] if ad_user['title'] else ''

        filename = f"/carddav/vcf/{sam}.vcf"
        #filename = f"./vcf/{sam}.vcf"
        if birthday:
            birthday = datetime.strptime(birthday, '%d.%m.%Y')
            birthday = datetime.strftime(birthday, '%Y-%m-%d')

        contact = {
            "givenName": givenName,
            "sn": sn,
            "cn": cn,
            "mail": mail,
            "telephoneNumber": telephoneNumber,
            "bday": birthday,
            "company": company,
            "title": title,
            "mobile": mobile
        }
        add_contact(filename, contact)

    for ad_user in ad_users:
        user_sam = ad_user['sAMAccountName'][0]
        logging.info(f"Наполняем адресную книгу для {user_sam}")

        params = {
            'url': f"{config['BAIKAL_ADDRESSBOOK_URL']}/addressbooks/{user_sam}/default/",
            'user': user_sam,
            'passwd': config['BAIKAL_AUTH_ADDRESSBOOK_PASSWORD'],
            'verify': 'True',
            'auth': 'basic'
        }

        params_abook = {
            'resource': f"{config['BAIKAL_ADDRESSBOOK_URL']}/addressbooks/{user_sam}/default/",
            'user': user_sam,
            'passwd': config['BAIKAL_AUTH_ADDRESSBOOK_PASSWORD'],
            'write_support': True
        }
        dav = carddav.PyCardDAV(**params_abook)
        abook = dav.get_abook()

        for ad_contact in ldap_results:
            contact_sam = ad_contact['sAMAccountName'][0]
            contact_mail = ad_contact['mail'][0].lower()
            contact_ldap_active = False if int(ad_contact['userAccountControl'][0]) & 0b10 else True
            params['filename'] = f"./vcf/{contact_sam}.vcf"
            try:
                if contact_ldap_active:
                    if contact_sam.upper() not in [i.split('/')[-1].replace('.vcf', '').upper() for i in abook.keys()]:
                        carddavutil.upload(contact_sam, **params)
                        logging.info(f"Контакт {contact_mail} загружен")
                    # else:
                    #     carddavutil.fixFN(contact_sam, **params)
                    #     logging.info(f"Контакт‚ {contact_mail} обновлён")

                else:
                    if contact_sam.upper() in [i.split('/')[-1].replace('.vcf', '').upper() for i in abook.keys()]:
                        card = [(href, etag) for href, etag in abook.items() if contact_sam in href]
                        dav.delete_vcard(card[0][0], card[0][1])
                        logging.info(f"Контакт‚ {contact_mail} удалён")

            except Exception as e:
                logging.info(f'ошибка загрузки контакта {contact_sam} в книгу {user_sam}')
                logging.error(traceback.format_exc())


def read_config():
    required_config_keys = [
        'LDAP_CARDDAV_LDAP_URI',
        'LDAP_CARDDAV_LDAP_BASE_DN',
        'LDAP_CARDDAV_LDAP_BIND_DN',
        'LDAP_CARDDAV_LDAP_BIND_DN_PASSWORD',
        'LDAP_CARDDAV_SYNC_INTERVAL',
        'BAIKAL_ADDRESSBOOK_URL',
        'MYSQL_ROOT_PASSWORD',
        'MYSQL_DATABASE',
        'MYSQL_USER',
        'MYSQL_PASSWORD'
    ]

    config = {}

    for config_key in required_config_keys:
        if config_key not in os.environ:
            sys.exit(f"Required environment value {config_key} is not set")

        config[config_key.replace('LDAP_CARDDAV_', '')] = os.environ[config_key]

    config['LDAP_FILTER'] = os.environ[
        'LDAP_CARDDAV_LDAP_FILTER'] if 'LDAP_CARDDAV_LDAP_FILTER' in os.environ else '(&(objectClass=user)(objectCategory=person))'

    config['LDAP_BASE_DN'] = config['LDAP_BASE_DN'].split(";")
    if os.environ['LDAP_CARDDAV_LDAP_BASE_DN_EXT']:
        config['LDAP_BASE_DN'] += os.environ['LDAP_CARDDAV_LDAP_BASE_DN_EXT'].split(";")


    # При создании в БД пользователей используется хеш нижеприведённого пароля
    config['BAIKAL_AUTH_ADDRESSBOOK_PASSWORD'] = "5VmFw@8ZGulM"

    return config


def add_contact(filename, contact):
    with open(filename, 'w', encoding="utf8") as file:
        text = [
            f"BEGIN:VCARD",
            f"VERSION:3.0",
            f'N:{contact["givenName"]};{contact["sn"]};',
            f'FN:{contact["cn"]}',
            f'EMAIL;TYPE=INTERNET:{contact["mail"]}',
            f'TEL;WORK;VOICE:{contact["telephoneNumber"]}',
            f'TEL;cell:{contact["mobile"]}',
            f'URL:https://docrobot.ru',
            f'BDAY:{contact["bday"]}',
            f'ORG:{contact["company"]}',
            f'LOGO;VALUE=uri:https://www.docrobot.ru/images/mail/logo.png',
            f'TITLE:{contact["title"]}',
            f'END:VCARD'
        ]
        for line in text:
            file.write(line + "\n")


class LdapConnection(Exception):
    pass


if __name__ == '__main__':
    main()
