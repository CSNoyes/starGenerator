# built in
from urlparse import urljoin
from random import randint as randNum
import random
import string
import time
import json
import StringIO
from urllib import urlencode

# outside dependencies
import pycurl
from bs4 import BeautifulSoup
import stem.process
from stem import Signal
from stem.connection import connect
from stem.util import term
from faker import Faker


class userInfo:

    users = {}
    fake = Faker()
    def __init__(self, numberUsers):
        for user in range(numberUsers):
            tempInfo = self.fakedData()
            self.users[tempInfo[0]] = tempInfo[1]
        print self.users

    def id_generator(self, size=7, chars=string.digits + string.ascii_lowercase):
        return (''.join(random.choice(chars) for _ in range(size))) + '1'

    def fakedData(self):
        randUsername = self.fake.first_name_male() + self.fake.last_name_male() + str(randNum(0,99))
        randPassword = self.id_generator(10)
        return [randUsername,randPassword]

    def getUsers(self):
        return self.users

    def __str__(self):
        return str(self.users)


class torHandler:
    controlPort = 9051
    socksPort = 7051
    def __init__(self, torLocation):
        self.torLocation = torLocation
        self.torProcess = stem.process.launch_tor_with_config(
            tor_cmd = self.torLocation,
            config = {'SocksPort' : str(self.socksPort),
                    'ControlPort' : str(self.controlPort)},
            init_msg_handler = self.printBootstrapLines,
            take_ownership = True)

    def printBootstrapLines(self, line):
      if "Bootstrapped " in line:
        print(term.format(line, term.Color.BLUE))

    def getNewRoute(self):
        controller = connect()
        controller.authenticate()
        time.sleep(controller.get_newnym_wait())
        controller.signal(Signal.NEWNYM)

    def killProc(self):
        self.torProcess.kill()


class infoGatherer:
    fake = Faker()
    GITHUB_API = 'https://api.github.com'
    GITHUB = 'https://github.com'
    GITHUB_REPO = ''
    GITHUB_USER= ''
    torDirectory = ''
    users = {}

    def __init__(self):
        self.torHandler = torHandler(self.torDirectory)

    def getPubIP(self):
        self.output = StringIO.StringIO()
        self.query = pycurl.Curl()
        self.query.setopt(pycurl.URL, 'http://ip.42.pl/raw')
        self.query.setopt(pycurl.PROXY, 'localhost')
        self.query.setopt(pycurl.PROXYPORT, self.torHandler.socksPort)
        self.query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
        self.query.setopt(pycurl.WRITEFUNCTION, self.output.write)
        self.query.perform()
        self.query.close()
        return self.output.getvalue()

    def getNewIP(self):
        print (term.format("Getting new IP", term.Color.BLUE))
        self.torHandler.getNewRoute()

    def close(self):
        self.torHandler.killProc()

    def createPassword(self, size=7, chars=string.digits + string.ascii_lowercase):
        return (''.join(random.choice(chars) for _ in range(size))) + '1'

    def createUsername(self):
        firstName = self.fake.first_name_male()
        lastName = self.fake.last_name_male()
        username = firstName + lastName + str(randNum(0,99))
        self.users[username] = firstName + ' ' + lastName
        return username

    def masterProc(self):
        self.forThread()

    def forThread(self):
        self.numSuccesses = 0
        self.numFails = 0
        while True:
            self.username = self.createUsername()
            self.password = str(self.createPassword())
            self.email = self.username + "@sharklasers.com"
            self.token = self.goToJoin()
            self.postData = {
                'utf8' : 'â',
                'authenticity_token' : self.token,
                'user[login]' : self.username,
                'user[email]' : self.email,
                'user[password]' : self.password,
                'user[password_confirmation]' : self.password,
                'source_label' : 'Detail Form'
            }


            try:
                self.createUser(self.postData)
                self.token = self.goToPlan()
                self.postDataPlan = {
                        'utf8' : 'â',
                        'authenticity_token' : self.token,
                        'plan' : 'free'}
                self.selectPlan(self.postDataPlan)
                self.starRepo(self.username,self.password)
                self.followUser(self.username,self.password)
                self.numSuccesses += 1
                self.makeRealistic(self.username,self.password)
                if random.random() < 0.1:
                    self.getNewIP()
                print "Success #" + str(self.numSuccesses)

            except Exception as e:
                print e
                self.numFails += 1
                print "Failure #" + str(self.numFails)


    def goToJoin(self):
        self.output = StringIO.StringIO()
        self.query = pycurl.Curl()
        self.url = urljoin(self.GITHUB,'join')
        self.query.setopt(pycurl.URL, self.url)
        self.query.setopt(pycurl.PROXY, 'localhost')
        self.query.setopt(pycurl.PROXYPORT, self.torHandler.socksPort)
        self.query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
        self.query.setopt(pycurl.WRITEFUNCTION, self.output.write)
        self.query.setopt(pycurl.COOKIEJAR, 'cookieJarUser.txt')
        self.query.perform()
        self.query.close()
        self.html = self.output.getvalue()
        self.soup = BeautifulSoup(self.html)
        self.token = self.soup.find("meta",{"name" : "csrf-token"})['content']
        return self.token

    def goToPlan(self):
        self.output = StringIO.StringIO()
        self.query = pycurl.Curl()
        self.url = urljoin(self.GITHUB, 'join/plan')
        self.query.setopt(pycurl.URL, self.url)
        self.query.setopt(pycurl.PROXY, 'localhost')
        self.query.setopt(pycurl.PROXYPORT, self.torHandler.socksPort)
        self.query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
        self.query.setopt(pycurl.WRITEFUNCTION, self.output.write)
        self.query.setopt(pycurl.COOKIEFILE, 'cookieJarPackages.txt')
        self.query.setopt(pycurl.COOKIEJAR, 'cookieJarPlan.txt')
        self.query.perform()
        self.query.close()
        self.html = self.output.getvalue()
        self.soup = BeautifulSoup(self.html)
        self.token = self.soup.find("meta",{"name" : "csrf-token"})['content']
        return self.token

    def createUser(self, postData):
        self.output = StringIO.StringIO()
        self.stats = StringIO.StringIO()
        self.query = pycurl.Curl()
        self.query.setopt(pycurl.URL, 'https://github.com/join')
        self.query.setopt(pycurl.PROXY, 'localhost')
        self.query.setopt(pycurl.PROXYPORT, self.torHandler.socksPort)
        self.query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
        self.query.setopt(pycurl.WRITEFUNCTION, self.output.write)
        self.query.setopt(pycurl.COOKIEFILE, 'cookieJarUser.txt')
        self.query.setopt(pycurl.COOKIEJAR, 'cookieJarPackages.txt')
        self.query.setopt(pycurl.POSTFIELDS, urlencode(postData))
        self.query.setopt(pycurl.POST, 1)
        self.query.setopt(pycurl.HEADERFUNCTION, self.stats.write)
        self.query.setopt(pycurl.FOLLOWLOCATION,1)
        self.query.perform()
        self.query.close()

    def selectPlan(self, postData):
        output = StringIO.StringIO()
        stats = StringIO.StringIO()
        query = pycurl.Curl()
        query.setopt(pycurl.URL, 'https://github.com/join')
        query.setopt(pycurl.PROXY, 'localhost')
        query.setopt(pycurl.PROXYPORT, self.torHandler.socksPort)
        query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
        query.setopt(pycurl.WRITEFUNCTION, output.write)
        query.setopt(pycurl.COOKIEFILE, 'cookieJarPlan.txt')
        query.setopt(pycurl.POSTFIELDS, urlencode(postData))
        query.setopt(pycurl.POST, 1)
        query.setopt(pycurl.HEADERFUNCTION, stats.write)
        query.setopt(pycurl.FOLLOWLOCATION,1)
        query.perform()
        query.close()

    def starRepo(self, user, password):
        url = (self.GITHUB_API + '/user/following/{username}'.format(
              username=self.GITHUB_USER))
        output = StringIO.StringIO()
        query = pycurl.Curl()
        query.setopt(pycurl.URL, url)
        query.setopt(pycurl.PROXY, 'localhost')
        query.setopt(pycurl.PROXYPORT, self.torHandler.socksPort)
        query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
        query.setopt(pycurl.WRITEFUNCTION, output.write)
        query.setopt(pycurl.CUSTOMREQUEST, "PUT")
        query.setopt(pycurl.USERPWD, user + ':' + password)
        query.perform()
        query.close()

    def followUser(self, user, password):
        url = 'https://api.github.com/user/starred/{owner}/{repo}'.format(
              owner=self.GITHUB_USER,
              repo=self.GITHUB_REPO)
        output = StringIO.StringIO()
        query = pycurl.Curl()
        query.setopt(pycurl.URL, url)
        query.setopt(pycurl.PROXY, 'localhost')
        query.setopt(pycurl.PROXYPORT, self.torHandler.socksPort)
        query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
        query.setopt(pycurl.WRITEFUNCTION, output.write)
        query.setopt(pycurl.CUSTOMREQUEST, "PUT")
        query.setopt(pycurl.USERPWD, user + ':' + password)
        query.perform()
        query.close()

    def makeRealistic(self, user, password):
        url = urljoin(self.GITHUB_API,'user')
        postData = {
          "name": self.users[user],
          "location": self.fake.city(),
          "hireable": True
        }
        if random.random() < 0.3:
            postData["company"] = self.fake.company()
        output = StringIO.StringIO()
        query = pycurl.Curl()
        query.setopt(pycurl.URL, url)
        query.setopt(pycurl.PROXY, 'localhost')
        query.setopt(pycurl.PROXYPORT, self.torHandler.socksPort)
        query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
        query.setopt(pycurl.WRITEFUNCTION, output.write)
        query.setopt(pycurl.CUSTOMREQUEST, "PATCH")
        query.setopt(pycurl.POSTFIELDS, json.dumps(postData))
        query.setopt(pycurl.USERPWD, user + ':' + password)
        query.perform()
        query.close()
        print output.getvalue()