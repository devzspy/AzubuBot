#!/usr/bin
import sys
import socket
import string
import re
import codecs
import urlmarker
import time
import thread
import random
import pickle
from time import sleep

reload(sys)
sys.setdefaultencoding("utf-8")

# -*- coding: utf8 -*-

NETWORK = 'servercentral.il.us.quakenet.org'
PORT = 6667
NICK = 'Azubot'
CHAN = ['#FalconSpy']
IDENTD = 'azubot'
REALNAME = '\x039Azubu Bot'
CONNECTED = False
AUTH = 'your user'
PASSWORD = 'your pass'

s = socket.socket()


'''
    Sub Functions
'''
################################################################
def removeApproved(user, op, channel, admins, approved_users):
    if(op in admins[channel]):
        flag = True
        while flag:
            time.sleep(60)
            approved_users.remove(user)
            flag = False
    else:
        try:
            s.send("PRIVMSG %s :Sorry you are not allowed to use that command\r\n" % op)
        except:
            return

    return approved_users

def authQ(QAUTH, QPASSWORD):
    try:
        s.send("PRIVMSG Q@CServe.quakenet.org :auth %s %s\r\n" % (QAUTH, QPASSWORD))
        s.send("MODE %s +x\r\n" % NICK)
    except:
        return

def grabAdmins(channel, ops, admins):
    if(channel in admins):
        for admin in ops:
            if(admin not in admins[channel]):
                admins[channel].append(admin)
    else:
        admins[channel] = ops

    return admins

def grabVoices(channel, voices, voiced):
    if(channel in voiced):
        for voice in voices:
            if(voice not in voiced[channel]):
                voiced[channel].append(voice)
    else:
        voiced[channel] = voices

    return voiced

def removeAdmin(channel, op, admins):
    admins[channel].remove(op)

    return admins

def addWord(channel, word, banned_words):
    if(channel in banned_words):
        for words in word:
            if(words not in banned_words[channel]):
                banned_words[channel].append(words)
    else:
        banned_words[channel] = word
        
    return banned_words

def removeWord(channel, word, banned_words, user):
    if(channel in banned_words):
        for words in word:
            if(words in banned_words[channel]):
                banned_words[channel].remove(words)
    else:
        s.send("PRIVMSG %s :Sorry, unable to find word in blacklisted database\r\n" % user)

    return banned_words

def grabChanlevs(channel):
    try:
        s.send("PRIVMSG Q :chanlev %s\r\n" % (channel))
    except:
        return

def load_Startup_Channel(CHANNELS_LIST, CURRENTCHANNELS):
    for channel in CHANNELS_LIST:
        try:
            s.send("JOIN %s\r\n" % channel)
            CURRENTCHANNELS += 1
        except:
            continue

    return CURRENTCHANNELS

def joinChannel(admin, channel, CURRENTCHANNELS, MAXCHANNELS):
    if(CURRENTCHANNELS <= MAXCHANNELS):
        try:
            s.send("JOIN %s\r\n" % channel)
            s.send("PRIVMSG %s :I joined %s\r\n" % (admin,channel))
            CURRENTCHANNELS += 1
        except:
            return

    return CURRENTCHANNELS

def partChannel(admin, channel, CURRENTCHANNELS):
    if(CURRENTCHANNELS >= 0):
        try:
            s.send("PART %s\r\n" % channel)
            s.send("PRIVMSG %s :I left %s\r\n" % (admin,channel))
            CURRENTCHANNELS -= 1
        except:
            return

    return CURRENTCHANNELS

def userWhois(user):
    try:
        s.send("WHOIS %s\r\n" % user)
    except:
        return
##################################################################################

'''
    Main Function
'''
##################################################################################
def main(NETWORK, NICK, CHAN, PORT):
    flag = True
    readbuffer = ""
    admins = {}
    voiced = {}
    raffle_starters = {}
    global_mods = []
    staff = []
    approved_users = []
    current_raffle = {}
    global_banned = []
    broadcaster_channel = ""
    broadcaster = ""
    raffle_user = ""
    keyword = ""
    authed_as = ""
    raffle_flag = ""
    raffle_execute = ""
    banned_words = pickle.load(open('bannedwords.p', 'rb'))

    #MAXCHANNELS = 20
    MAXCHANNELS = 5
    CURRENTCHANNELS = 0
    global CONNECTED

    s.connect((NETWORK,PORT))
    s.send("NICK %s\r\n" % NICK)
    s.send("USER %s %s bla :%s\r\n" % (IDENTD, NETWORK, REALNAME))
    
    while(flag):
        readbuffer = readbuffer + s.recv(4096)  

        #print readbuffer

        temp = string.split(readbuffer, "\n")
        readbuffer = temp.pop()

        for line in temp:
            line = string.rstrip(line)
            line = string.split(line)
            line = [re.sub("^:", "", rep) for rep in line]
            line = [x.decode('utf-8') for x in line]

            if("PING" not in line and CONNECTED == True and "PRIVMSG" in line):
                user = line[0].split("!", 1)
                user = user[0] 
                channel = line[2]
                msg = line[3:]
                print "[IN][%s][%s]%s" % (user, channel, ' '.join(msg))

            try:
                if(line[0] == "PING"):
                    s.send("PONG %s\r\n" % line[1])
                    #print "PONG :%s" % line[1]

                ########################################################
                '''
                    On connect
                '''
                ########################################################
                if("MODE" in line and NICK in line and "+i" in line):
                    CONNECTED = True
                    s.send("PRIVMSG #FalconSpy :Azubu bot version 1.1 loaded.\r\n")
                    authQ(AUTH, PASSWORD)
                    sleep(5)
                    CURRENTCHANNELS = load_Startup_Channel(CHAN, CURRENTCHANNELS)
                #######################################################

                ###########################################
                '''
                    User privilege logic
                '''
                ###########################################
                if("353" in line and NICK in line):
                    if(re.findall("@.+", ' '.join(line[5:]))):
                        channel = line[4]
                        users = line[5:]
                        ops = []

                        for user in users:
                            if(re.findall("@.+", user)):
                                user = user.lstrip("@")
                                ops.append(user)

                        admins = grabAdmins(channel, ops, admins)
                        grabChanlevs(channel)
                    elif(not re.findall("@.+", ' '.join(line[5:]))):
                        channel = line[4]
                        ops = []
                        admins = grabAdmins(channel, ops, admins)
                        grabChanlevs(channel)
                    
                    if(re.findall("\+.+", ' '.join(line[5:]))):
                        channel = line[4]
                        users = line[5:]
                        voices = []

                        for user in users:
                            if(re.findall("\+.+", user)):
                                user = user.lstrip("+")
                                voices.append(user)

                        voiced = grabVoices(channel, voices, voiced)
                    elif(not re.findall("\+.+", ' '.join(line[5:]))):
                        channel = line[4]
                        voices = []
                        voiced = grabVoices(channel, voices, voiced)

                if("MODE" in line and "+o" in line):
                    channel = line[2]
                    user = [line[-1]]
                    admins = grabAdmins(channel, user, admins)

                if("MODE" in line and "-o" in line):
                    channel = line[2]
                    user = line[-1]
                    admins = removeAdmin(channel, user, admins)

                if(line[0] == "Azubu!Azubu@QuakeNet.Partner" and "PRIVMSG" in line and NICK not in line and "Staff" in line and "joined:" in line):
                    user = line[-1]
                    if(user not in staff):
                        staff.append(user)
                    continue
                elif(line[0] == "Azubu!Azubu@QuakeNet.Partner" and "PRIVMSG" in line and NICK not in line and (("Global" in line and "moderator" in line and "joined:" in line) or ("Administrator" in line and "joined:" in line))):
                    user = line[-1]
                    if(user not in global_mods):
                        global_mods.append(user)
                    continue
                ##############################################################################

                ##############################################################################
                '''
                    Commands
                '''
                ##############################################################################
                if(line[0] == "FalconSpy!FalconSpy@staff.quakenet.org" and line[3].lower() == "quit"):
                    s.close()
                    print "quit received, closed socket\n"
                    readbuffer = ""
                    flag = False
                    break

                if("?approve" in line):
                    op = line[0].split("!", 1)
                    op = op[0] 
                    user = line[4]
                    channel = line[2]

                    if(user not in approved_users):
                        approved_users.append(user)
                        thread.start_new_thread(removeApproved, (user, op, channel, admins, approved_users))

                    continue 

                if("?addword" in line):
                    user = line[0].split("!", 1)
                    user = user[0]
                    channel = line[2]
                    word = line[-1]
                    word = [word]
                    if(user in admins[channel]):
                        banned_words = addWord(channel, word, banned_words)
                        pickle.dump(banned_words, open("bannedwords.p", "wb"))

                    continue

                if("?removeword" in line):
                    user = line[0].split("!", 1)
                    user = user[0]
                    channel = line[2]
                    word = line[-1]
                    word = [word]
                    if(user in admins[channel]):
                        banned_words = removeWord(channel, word, banned_words, user)
                        pickle.dump(banned_words, open("bannedwords.p", "wb"))

                    continue

                if(line[0] == "FalconSpy!FalconSpy@staff.quakenet.org" and "?join" in line):
                    admin = line[0].split("!", 1)
                    admin = admin[0]                
                    channel = line[4]
                    CURRENTCHANNELS = joinChannel(admin,channel, CURRENTCHANNELS, MAXCHANNELS)  
                    continue 

                if(line[0] == "FalconSpy!FalconSpy@staff.quakenet.org" and "?part" in line):
                    admin = line[0].split("!", 1)
                    admin = admin[0]
                    channel = line[4]
                    CURRENTCHANNELS = partChannel(admin,channel, CURRENTCHANNELS) 
                    continue
                #################################################################

                ###################################################################
                '''
                    URL / BANNED WORD Removal
                '''
                if(line[1] == "PRIVMSG" and re.search("#azubu\..*\..*", line[2]) and line[2] != NICK and not(re.search("(Azubu!Azubu@QuakeNet.Partner)", line[0]))):
                    user = line[0].split("!", 1)
                    user = user[0]                
                    channel = line[2]

                    if(user not in admins[channel] and user not in global_mods and user not in staff):
                        if(re.findall(urlmarker.URL_REGEX, ' '.join(line[3:])) or (''.join([x for x in banned_words[channel] if x in ' '.join(line[3:])])) or (''.join([x for x in banned_words['global'] if x in ' '.join(line[3:])]))): #if any part of the iterable in the search is true, return true for whole iterable

                            s.send("PRIVMSG %s :.clear %s\r\n" % (channel,user))
                            print "[OUT][%s][%s].clear %s" % (NICK, channel, user)

            except:
                continue

main(NETWORK, NICK, CHAN, PORT)
