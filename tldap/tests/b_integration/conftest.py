from ldap3.core import exceptions
import pytest
from pytest_bdd import given, when, then, parsers

import tldap
import tldap.tests.database
from tldap import transaction
import tldap.backend
import tldap.database
import tldap.test.slapd
from tldap.tests.database import Account


@pytest.fixture
def LDAP(step_login):
    LDAP = {
        'default': {
            'ENGINE': 'tldap.backend.fake_transactions',
            'URI': 'ldap://localhost:38911/',
            'USER': step_login[0],
            'PASSWORD': step_login[1],
            'USE_TLS': False,
            'TLS_CA': None,
            'LDAP_ACCOUNT_BASE': 'ou=People, dc=python-ldap,dc=org',
            'LDAP_GROUP_BASE': 'ou=Groups, dc=python-ldap,dc=org'
        }
    }

    tldap.backend.setup(LDAP)
    server = tldap.test.slapd.Slapd()
    server.set_port(38911)

    server.start()

    yield tldap.backend.connections['default']

    server.stop()


@pytest.fixture
def LDAP_ou(LDAP):
    organizationalUnit = tldap.tests.database.OU({
        'dn': "ou=People, dc=python-ldap,dc=org"
    })
    tldap.database.insert(organizationalUnit)

    organizationalUnit = tldap.tests.database.OU({
        'dn': "ou=Groups, dc=python-ldap,dc=org"
    })
    tldap.database.insert(organizationalUnit)


@pytest.fixture
def DN():
    return "cn=Manager,dc=python-ldap,dc=org"


@pytest.fixture
def password():
    return "password"


@pytest.fixture
def context():
    return {}


@given(parsers.cfparse('we login as {DN} using {password}'))
def step_login(DN, password):
    """ Test if we can logon correctly with correct password. """
    return (DN, password)


@when('we enter a transaction')
def step_start_transaction(LDAP_ou):
    transaction.enter_transaction_management()


@when('we commit the transaction')
def step_commit_transaction(LDAP_ou):
    transaction.commit()
    transaction.leave_transaction_management()


@when('we rollback the transaction')
def step_rollback_transaction(LDAP_ou):
    transaction.rollback()
    transaction.leave_transaction_management()


@then('we should be able to search')
def step_search(LDAP_ou):
    """ Test we can search. """
    list(tldap.database.search(Account))


@then('we should not be able to search')
def step_not_search(LDAP):
    """ Test we can search. """
    with pytest.raises(exceptions.LDAPInvalidCredentialsResult):
        list(tldap.database.search(Account))


@then(parsers.cfparse(
    'we should be able confirm the {attribute} attribute is {value}'))
def step_confirm_attribute(context, attribute, value):
    actual_value = context['obj'][attribute]
    assert str(actual_value) == value, attribute
