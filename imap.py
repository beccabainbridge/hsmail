#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Simple IMAP4 client which displays the subjects of all messages in a
particular mailbox.
"""

import os
import sys
import email

from twisted.internet import protocol
from twisted.internet import ssl
from twisted.internet import defer
from twisted.internet import stdio
from twisted.mail import imap4
from twisted.protocols import basic
from twisted.python import log


class SimpleIMAP4Client(imap4.IMAP4Client):
    """
    A client with callbacks for greeting messages from an IMAP server.
    """
    greetDeferred = None

    def serverGreeting(self, caps):
        self.serverCapabilities = caps
        if self.greetDeferred is not None:
            d, self.greetDeferred = self.greetDeferred, None
            d.callback(self)



class SimpleIMAP4ClientFactory(protocol.ClientFactory):
    usedUp = False

    protocol = SimpleIMAP4Client


    def __init__(self, username, onConn):
        self.ctx = ssl.ClientContextFactory()

        self.username = username
        self.onConn = onConn


    def buildProtocol(self, addr):
        """
        Initiate the protocol instance. Since we are building a simple IMAP
        client, we don't bother checking what capabilities the server has. We
        just add all the authenticators twisted.mail has.  Note: Gmail no
        longer uses any of the methods below, it's been using XOAUTH since
        2010.
        """
        assert not self.usedUp
        self.usedUp = True

        p = self.protocol(self.ctx)
        p.factory = self
        p.greetDeferred = self.onConn

        p.registerAuthenticator(imap4.PLAINAuthenticator(self.username))
        p.registerAuthenticator(imap4.LOGINAuthenticator(self.username))
        p.registerAuthenticator(
                imap4.CramMD5ClientAuthenticator(self.username))

        return p


    def clientConnectionFailed(self, connector, reason):
        d, self.onConn = self.onConn, None
        d.errback(reason)



def cbServerGreeting(proto, username, password):
    """
    Initial callback - invoked after the server sends us its greet message.
    """

    # Try to authenticate securely
    return proto.authenticate(password
        ).addCallback(cbAuthentication, proto
        ).addErrback(ebAuthentication, proto, username, password
        )


def ebConnection(reason):
    """
    Fallback error-handler. If anything goes wrong, log it and quit.
    """
    log.startLogging(sys.stdout)
    log.err(reason)
    return reason


def cbAuthentication(result, proto):
    """
    Callback after authentication has succeeded.

    Lists a bunch of mailboxes.
    """
    return proto.list("", "*"
        ).addCallback(cbMailboxList, proto
        )


def ebAuthentication(failure, proto, username, password):
    """
    Errback invoked when authentication fails.

    If it failed because no SASL mechanisms match, offer the user the choice
    of logging in insecurely.

    If you are trying to connect to your Gmail account, you will be here!
    """
    failure.trap(imap4.NoSupportedAuthentication)
    return defer.succeed("y"
        ).addCallback(cbInsecureLogin, proto, username, password
        )


def cbInsecureLogin(result, proto, username, password):
    """
    Callback for "insecure-login" prompt.
    """
    if result.lower() == "y":
        # If they said yes, do it.
        return proto.login(username, password
            ).addCallback(cbAuthentication, proto
            )
    return defer.fail(Exception("Login failed for security reasons."))


def cbMailboxList(result, proto):
    """
    Callback invoked when a list of mailboxes has been retrieved.
    """
    result = [e[2] for e in result]
    s = '\n'.join(['%d. %s' % (n + 1, m) for (n, m) in zip(range(len(result)), result)])
    if not s:
        return defer.fail(Exception("No mailboxes exist on server!"))
    return defer.succeed("1"
        ).addCallback(cbPickMailbox, proto, result
        )


def cbPickMailbox(result, proto, mboxes):
    """
    When the user selects a mailbox, "examine" it.
    """
    mbox = mboxes[int(result or '1') - 1]
    return proto.examine(mbox
        ).addCallback(cbExamineMbox, proto
        )


def cbExamineMbox(result, proto):
    """
    Callback invoked when examine command completes.

    Retrieve the subject header of every message in the mailbox.
    """
    return proto.fetchMessage('1:*').addCallback(cbFetch, proto)


def cbFetch(result, proto):
    """
    Finally, display headers.
    """
    if result:
        proto.messages = [(i, email.message_from_string(d['RFC822'])) for i, d in result.items()]
    else:
        print "Hey, an empty mailbox!"

    return proto


def cbClose(result):
    """
    Close the connection when we finish everything.
    """
    from twisted.internet import reactor
    reactor.stop()

def cbReturnMessage(proto):
    messages = proto.messages
    d = proto.logout()
    return d.addCallback(lambda x: messages)


def get_messages(username, password):
    hostname = 'imap.gmail.com'
    port = 993

    onConn = defer.Deferred(
        ).addCallback(cbServerGreeting, username, password
        ).addErrback(ebConnection
        ).addBoth(cbReturnMessage)

    factory = SimpleIMAP4ClientFactory(username, onConn)

    from twisted.internet import reactor
    reactor.connectSSL(hostname, port, factory, ssl.ClientContextFactory())

    return onConn

def print_messages(x):
    print x

def main():

    username = os.environ['EXAMPLE_GMAIL_ADDRESS']
    password = os.environ['EXAMPLE_GMAIL_PASSWORD']

    d = get_messages(username, password)
    d.addCallback(print_messages)
    d.addBoth(cbClose)

    from twisted.internet import reactor
    reactor.run()


if __name__ == '__main__':
    main()
