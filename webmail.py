import cgi
from urlparse import parse_qsl

from klein import Klein
from twisted.python.components import registerAdapter
from twisted.internet import reactor
from twisted.web.server import Session
from zope.interface import Interface, Attribute, implements
from jinja2 import Environment, FileSystemLoader

from mailclient import sendmail
from imap import get_messages

app = Klein()
env = Environment(loader=FileSystemLoader('templates'))

def render_template(filename, **kwargs):
    template = env.get_template(filename)
    return template.render(**kwargs)

class ILogin(Interface):
    email = Attribute("user's email address")
    password = Attribute("user's email password")

class Login(object):
    implements(ILogin)
    def __init__(self, session):
        self.email = ''
        self.password = ''


registerAdapter(Login, Session, ILogin)

def getFieldDict(request):
    content = (cgi.escape(request.content.read()))
    return dict(parse_qsl(content))


@app.route('/', methods = ['GET', 'POST'])
def home(request):

    def cbSentMessage(result):
        print 'success'

    def ebSentMessage(error):
        error.printTraceback()

    session = request.getSession()

    login = ILogin(session)
    if not login.email or not login.password:
        return request.redirect('/login')


    if request.method == 'POST':
        qs_dict = getFieldDict(request)

        to = qs_dict['to']
        subject = qs_dict['subject']
        message = qs_dict['message']

        mailDeferred = sendmail(login.email, login.password, 'smtp.gmail.com', 587, login.email, to, subject, message)
        mailDeferred.addCallbacks(cbSentMessage, ebSentMessage)

        return request.redirect('/')

    d = get_messages(login.email, login.password)

    def mainpage(messages):
        return render_template('mailview.html', messages=messages)

    d.addCallback(mainpage)
    return d


@app.route('/login', methods=['GET', 'POST'])
def login(request):

    if request.method == 'POST':
        qs_dict = getFieldDict(request)

        email = qs_dict['email']
        password = qs_dict['password']
        session = request.getSession()

        login = ILogin(session)
        login.email = email
        login.password = password

        return request.redirect('/')

    return render_template('login.html')



@app.route('/success')
def success(request):
    return 'Your message was sent!!!!!!!!!!!!!!!!!!'

app.run('localhost', 8080)
