# LDAPtoCARDDAV

Решение обёрнуто в docker compose:
  * контейнеры:
    * baikal - CARDDAV сервер Baikal
    * baikal-mysql - внешняя БД MariaDB.
    * carddav-sync - контейнер с Pytnon3, который производит загрузку контактов из LDAP

* [Как это работает](#как-это-работает)
* [Установка](#установка)
  * [LDAP тонкая настройка](#ldap-тонкая-настройка)


## Как это работает

Основой служит Open Source продукт, CardDAV/CalDAV сервер [Baikal](https://sabre.io/baikal/) 

Контейнер `carddav-sync` - скрипт на Python периодически проверяющий LDAP, создает новые УЗ в БД. Создаёт и удаляет контакты из CARDDAV Server.

## Установка

1. Создайте структуру папок, запустив скрипт `preparing_for_installation.sh`:
      * /opt/baikal
        * /opt/baikal/apache
        * /opt/baikal/ssl
        * /opt/baikal/carddav-sync
        * /opt/baikal/db
        * /opt/baikal/config
        * /opt/baikal/Specific
        
2. Создайте файл и настройте своё окружение в файле .env:

    * `LDAP_CARDDAV_LDAP_URI` - URI LDAP (например, Active Directory) (должен быть доступен изнутри контейнера). URI указаны в синтаксисе `protocol://host:port`. Например, `ldap://localhost` или `ldaps://secure.domain.org`
    * `LDAP_CARDDAV_LDAP_BASE_DN` - base DN, здесь основной поиск пользователей для LDAP авторизации, например `"OU=Users,DC=contoso,DC=ru"`
    * `LDAP_CARDDAV_LDAP_BASE_DN_EXT` - расширяет поиск base DN, задаётся в формате строки с разделителем `;` если не одно OU, например `"OU=GPH,DC=contoso,DC=ru;OU=Services,DC=contoso,DC=ru"`
    * `LDAP_CARDDAV_LDAP_BIND_DN` - bind DN специальной учетной записи LDAP, которая будет использоваться для поиска пользователей
    * `LDAP_CARDDAV_LDAP_BIND_DN_PASSWORD` - пароль для учетной записи bind DN
    * `LDAP_CARDDAV_SYNC_INTERVAL` - интервал в секундах между синхронизациями LDAP
    * **Опционально** LDAP фильтрация:
        * `LDAP_CARDDAV_LDAP_FILTER` - Применяемый фильтр LDAP по умолчанию равен `(&(objectClass=user)(objectCategory=person))`
    * `BAIKAL_ADDRESSBOOK_URL` - базовый адрес carddav, например `http://172.16.130.68:8888/dav.php`
    * `BAIKAL_SERVERNAME` - внешнее имя сервера, например "dav.exite.ru"
    * `MYSQL_ROOT_PASSWORD` - пароль рута для БД 
    * `MYSQL_DATABASE` - имя БД
    * `MYSQL_USER` - имя пользователя для БД
    * `MYSQL_PASSWORD` - пароль пользователя для БД
    
3. Установка: `source .env; docker compose up -d`
4. Установите Baikal, пройдя по ссылке указанной в `BAIKAL_ADDRESSBOOK_URL` с окончанием /admin/. 
    В качестве базы данных укажите на контейнер БД `baikal-mysql` и переменные из окружения `MYSQL_DATABASE, MYSQL_USER ,MYSQL_PASSWORD`
5. После успешной настройки Baikal, перезапустите контейнер `carddav-sync` (`docker compose restart carddav-sync`)
6. Проверьте логи `docker compose logs carddav-sync`
7. Скрипт в контейнере carddav-sync работает while True, с периодичность указанной в .env. При необходимости можно перезапустить контейнер `docker compose restart carddav-sync`

### LDAP тонкая настройка