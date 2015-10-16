#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, re
from check import rcsoperation

class file:
   """ caracteristiques d'un fichier
       self.filename : le nom complet du fichier
       self.name : le nom du fichier sans le chemin d'acces
       self.dirname : le nom du chemin d'acces
       self.filexist: le fichier existe sur le systeme
       self.rcsdirname : le chemin ou rcs stokera les modifications du fichier
       self.rcsfilename : le chemin complet du fichier utilisé par rcs pour les stocker
       self.rcsname : le nom du fichier utilisé par rcs pour les stocker
       self.rcsdirexist : le dossier rcs existe
       self.rcscontrolled : le fichier est controllé par rcs
       self.rcsfirstrev : numero de la premiere revision du fichier 1.1
       self.rcslastrev : numéro de la derniere revision du fichier 
       self.needtemplate : le fichier a besoin de changements
   """
   def __init__(self, filename, rcstop='/root/RCS'):
      self.rcstop = rcstop
      self.filename = filename
      self.fileshortname = os.path.basename(self.filename)
      self.filedirname = os.path.dirname(self.filename)
      self.rcslinkname = os.path.join(self.filedirname, 'RCS')
      self.rcsdirname = os.path.normpath(self.rcstop + self.filedirname)
      self.rcsfilename = os.path.join(self.rcsdirname, self.fileshortname + ',v')
      self.rcsshortname = os.path.basename(self.rcsfilename)
      self.__rcsrevlist = []
      self.rcsfirstrev = 0
      self.rcslastrev = 0
      self.filexist = self.__filexist()
      self.rcslinkexist = self.__rcslinkexist()
      self.rcsdirexist = self.__rcsdirexist()
      self.rcslinkisok = self.__rcslinkisok()
      self.rcscontrolled = self.__rcscontrolled()
      self.needtemplate = self.__needtemplate()

      if self.rcscontrolled:
         self.__rcsrevlist = self.__revlist()
         if len(self.__rcsrevlist) >= 1:
            self.rcsfirstrev = self.__rcsrevlist[len(self.__rcsrevlist)-1]
            self.rcslastrev = self.__rcsrevlist[0]

      self.attr = self.__getfileattr()

   def __str__(self):
      print('%15s : %s' % ('filename', self.filename))
      for key in self.attr[self.filename].keys():
         print('%15s : %s' % (key, self.attr[self.filename][key]))
      return str()


   def __getfileattr(self):
      """
          dictionnaire des fichiers et attributs 
      """
      fileattr = dict()
      fileattr[self.filename] = {

             'fileshortname' : self.fileshortname,
             'filedirname'   : self.filedirname,
             'filexist'      : self.filexist,
             'rcslinkname'   : self.rcslinkname,
             'rcslinkexist'  : self.rcslinkexist,
             'rcslinkisok'   : self.rcslinkisok,
             'rcsdirname'    : self.rcsdirname,
             'rcsfilename'   : self.rcsfilename,
             'rcsshortname'  : self.rcsshortname,
             'rcsdirexist'   : self.rcsdirexist,
             'rcscontrolled' : self.rcscontrolled,
             'rcsfirstrev'   : self.rcsfirstrev,
             'rcslastrev'    : self.rcslastrev,
             'needtemplate'  : self.needtemplate,

      }

      return fileattr

   def __revlist(self):
      revlist = []
      if self.rcscontrolled:
         fop = rcsoperation(self.filename)
         revlist = fop.revs()
      return revlist

   def __filexist(self):
      return os.path.isfile(self.filename)

   def __rcsdirexist(self):
      return os.path.isdir(self.rcsdirname)

   def __rcscontrolled(self):
      return os.path.isfile(self.rcsfilename)

   def __rcslinkexist(self):
      return os.path.islink(self.rcslinkname)

   def __rcslinkisok(self):
      if self.__rcslinkexist():
         if os.readlink(self.rcslinkname) == self.rcsdirname:
            return True
      return False

   def __needtemplate(self):
      if re.search('\$[A-Z]+', open(self.filename).read()):
         return True
      return False 

if __name__ == '__main__':

   pass
