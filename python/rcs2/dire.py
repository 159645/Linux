#!/usr/bin/python
# -*- coding: utf-8 -*-

class msg:
   """ affichage des messages sur le terminal

       self.info('info message')

       self.warn('warning message')

       self.error('error message')

       self.succes('succes message')

   """
   def __init__(self, silent=False):

      self.silent = silent

      self.succesc = '\033[94m'
      self.errorc = '\033[91m'
      self.warnc = '\033[90m'
      self.jobc = '\033[92m'
      self.endc = '\033[0m'
      self.bold = '\033[1m'

   def info(self, say):
      if not self.silent: print ("[ii]..%s" % str(say))

   def infob(self, say):
      if not self.silent: print ("%s%s[ii]..%s %s" % (self.bold, self.succesc, str(say), self.endc))

   def warn(self, say):
      if not self.silent: print ("%s[ww]..%s %s" % (self.warnc, str(say), self.endc))

   def error(self, say):
      if not self.silent: print ("%s[ko]..%s %s" % (self.errorc, str(say), self.endc))

   def errorb(self, say):
      if not self.silent: print ("%s%s[ko]..%s %s" % (self.bold, self.errorc, str(say), self.endc))

   def succes(self, say):
      if not self.silent: print ("%s[ok]..%s %s" % (self.succesc, str(say), self.endc))

   def step(self, say):
      if not self.silent: print ("%s%s[**]..%s %s" % (self.bold, self.jobc, str(say), self.endc))


