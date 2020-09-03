import praw
import os
from googletrans import Translator
from googletrans.constants import LANGUAGES as languageDict
import logging
from datetime import datetime
import sqlite3

class TranslationBot:

    def __init__(self):

        self.reddit = None
        self.translator = Translator()
        self.keyphrase = '!translate'
        self.introMessage = "Beep. boop. I'm a bot that translates. **Your translated text as follows!**"
        self.nextText = "Your text has been translated from {} to {}."
        self.conclusiveMessage = "If you liked this bot, please upvote this comment!"
        self.incorrectMessage = "Incorrect Format."
        self.languageUnavailable = "This language - {} is unavailable. Please use another."
        self.correctFormatV1 = "Use the format given here for if you want to **translate something specific** -> \n\n!translate french **(language you want)** how are you **(message you want to translate)**"
        self.correctFormatV2 = "Use the format given here if you want to **translate the parent comment** -> \n\n!translate french **(language you want)**"
        self.endMessage = self.correctFormatV1 + '\n\nOR\n\n' + self.correctFormatV2 + '\n\n' + self.conclusiveMessage

        self.databaseName = 'reddit'
        self.tableName = 'comments'

        self.insert_sql = "insert into " + self.tableName + " values(?,?,?) "
        self.select_idw_sql = "select * from " + self.tableName + " where id= ?"
        self.update_idwpc_sql = "update " + self.tableName + " set processedCount = ? " + " where id = ?"

        self.conn = sqlite3.connect(self.databaseName)
        self.c = self.conn.cursor()

        self.createTable = 'create table if not exists ' + self.tableName + ' (id text primary key, time timestamp, processedCount integer)'
        self.c.execute(self.createTable)


    def login(self):

        self.reddit = praw.Reddit("botLogin")

        if self.reddit is not None:
            logging.debug('Reddit Object created successfully')

    def fixingSubreddit(self):
        
        self.subreddit = self.reddit.subreddit('BotTest_for_coders')
        
        if self.subreddit is not None:
            logging.debug('Subreddit chosen')

    def streamingComments(self):


        me = self.reddit.user.me()
        for comment in self.subreddit.stream.comments():
            self.c.execute(self.select_idw_sql,(comment.id,))
            data = self.c.fetchall()
            if len(data) != 0:
                self.c.execute(self.update_idwpc_sql,(data[0][2]+1,comment.id,))
                logging.debug('Old element with id = {} has new count = {}'.format(comment.id, data[0][2] + 1))
            
            else:
                self.c.execute(self.insert_sql,(comment.id, datetime.now(),1))
                logging.debug('New element with id = {} added into table'.format(comment.id))

                if self.keyphrase in comment.body and comment.author != me:
                    try:
                        words = comment.body.split(' ', 2)
                        lengthWords = len(words)
                        if lengthWords == 3:
                            keyPhrase = words[0]
                            destLanguage = words[1]
                            phrase = words[2]
                            if self.keyphrase == keyPhrase.lower():
                                try:
                                    translatedText = self.translator.translate(phrase, dest=destLanguage)
                                    message = self.introMessage.format(destLanguage) + '\n\n' + translatedText.text + '\n\n' + \
                                        self.nextText.format(languageDict[translatedText.src], languageDict[translatedText.dest]) + '\n\n'
                                    comment.reply(message)
                                except Exception as e:
                                    logging.error(str(e) + '\n\n--Language - {} unavailable or unknown'.format(destLanguage))
                                    comment.reply(self.languageUnavailable.format(destLanguage) + '\n\n' + self.endMessage)
                            else:
                                logging.info(str(e) + '\n\n--Invalid request, possible format error!')
                                comment.reply(self.incorrectMessage + '\n\n' + self.endMessage)
                        
                        elif lengthWords == 2:
                            keyPhrase = words[0]
                            destLanguage = words[1]
                            if self.keyphrase == keyPhrase.lower():
                                if comment.parent_id.startswith('t1_'):
                                    parentId = comment.parent_id[3:]
                                    parentComment = self.reddit.comment(id = parentId)
                                    phrase = parentComment.body
                                    try:
                                        translatedText = self.translator.translate(phrase, dest=destLanguage)
                                        message = self.introMessage.format(destLanguage) + '\n\n' + translatedText.text + '\n\n' + \
                                            self.nextText.format(languageDict[translatedText.src], languageDict[translatedText.dest]) + '\n\n'
                                        comment.reply(message)
                                    except Exception as e:
                                        logging.error(str(e) + '\n\n--Language - {} unavailable or unknown'.format(destLanguage))
                                        comment.reply(self.languageUnavailable.format(destLanguage) + '\n\n' + self.endMessage)
                                else:
                                    logging.error(str(e) + '\n\n--No support for posts right now')
                                    comment.reply('Sorry, we don\'t post transaltion, yet, it would be out soon!' + '\n\n' + self.endMessage)

                            else:
                                logging.info(str(e) + '\n\n--Invalid request, possible format error!')
                                comment.reply(self.incorrectMessage + '\n\n' + self.endMessage)
                            

                    except Exception as e:
                        logging.error(str(e) + '\n\n--Invalid request')
                        comment.reply(self.incorrectMessage + '\n\n' + self.endMessage)
            
            self.conn.commit()
        
        self.conn.commit()
        self.c.close()

    def testFunction(self):

        comment = self.reddit.comment(id="g3tl2qo")
        print(type(comment), comment.body, comment.parent_id)

if __name__ == "__main__":
    if not os.path.isdir('logs'):
        os.mkdir('logs')

    logFile = 'logs/translatorBot+{}.log'.format(
        datetime.now().strftime("%d-%m-%y"))
    logForm = '%(asctime)s.%(msecs)03d %(levelname)s %(module)s -\
%(funcName)s: %(message)s'

    logging.basicConfig(filename=logFile,
                        filemode='a',
                        format=logForm,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    
    BOT = TranslationBot()
    BOT.login()
    BOT.fixingSubreddit()
    BOT.streamingComments()
