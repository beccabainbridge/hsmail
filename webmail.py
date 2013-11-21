import cgi

from klein import Klein

from mailclient import sendmail

from twisted.python.components import registerAdapter
from twisted.internet import reactor
from twisted.web.server import Session

from urlparse import parse_qsl

from zope.interface import Interface, Attribute, implements

from imap import get_messages

app = Klein()


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
        return ('''
        <!DOCTYPE html>
         <html>
           <head>
            <style>
              label {display:block;}
            </style>
           </head>
           <body>
           <br/>
           ''' +

           '<br/>'.join(m['Date'] for i, m in messages) +

           '''
           <br/>
             <form method="post" action="/">
               <p>
                 <label for="to">To:</label>
                 <input type="text" id="to" name="to"></input>
               </p>
               <p>
                 <label for="subject">Subject</label>
                 <input type="text" id="subject" name="subject"></input>
               </p>
               <p>
                 <label for="message">Message</label>
                 <textarea rows="10" cols="50" id="message" name="message"></textarea>
               </p>
               <input type="Submit"></input>
             </form>
           </body>
         </html>
         ''')

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


    return """
    <!DOCTYPE html>
      <html>
        <head>
         <style>
           label {display:block;}
         </style>
        </head>
          <body>
            <form method="post" action="/login">
              <p>
                <label for="email">Email</label>
                <input type="text" id="email" name="email"></input>
              </p>
              <p>
                <label for="password">Password</label>
                <input type="password" id="password" name="password"></input>
              </p>
              <input type="Submit"></input>
            </form>
          </body>
        </html>
        """


@app.route('/success')
def success(request):
    return 'Your message was sent!!!!!!!!!!!!!!!!!!'

app.run('localhost', 8080)

