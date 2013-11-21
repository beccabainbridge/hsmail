try:
    from cStringIO import cStringIO as StringIO
except ImportError:
    from StringIO import StringIO

import os

from OpenSSL.SSL import SSLv3_METHOD

from email.mime import Multipart
from email.mime import Text 

from urlparse import parse_qsl


from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor


def createMessage(fromEmail, toEmail, subject, body):
    msg = Multipart.MIMEMultipart()
    msg['From'] = fromEmail
    msg['To'] = toEmail
    msg['Subject'] = subject

    body = Text.MIMEText(body)
    msg.attach(body)

    return str(msg)


def sendmail(username, password, smtpHost, smtpPort, fromEmail, toEmail, subject, body):
    resultDeferred = Deferred()
    contextFactory = ClientContextFactory()
    contextFactory.method = SSLv3_METHOD

    msg = createMessage(fromEmail, toEmail, subject, body)
    senderFactory = ESMTPSenderFactory(
        username,
        password,
        fromEmail,
        toEmail,
        StringIO(msg),
        resultDeferred,
        contextFactory=contextFactory)
    
    reactor.connectTCP(smtpHost, smtpPort, senderFactory)
    return resultDeferred


def cbSentMessage(result):
    print "Message sent"


def ebSentMessage(err):
    err.printTraceback()
