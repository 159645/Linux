#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
from dire import msg
from fichier import file

class todolist(msg):
   """ 
       En fonction de la liste des fichiers a traiter,

       self.silent : on affiche ou non les messages
       self.config : est une instance de la classe config

       self.files      : dictionnaire des fichiers et caracteristiques
       self.operations : dictionnaire des operations a entreprendre
            
   """

   def __init__(self, config, silent=False):

      # affichage des messages
      self.silent = silent
      msg.__init__(self, self.silent)

      # on affiche le resume de la configuration     
      self.config = config
      self.info(self.config)
      
      self.step('preparation ...')
   
      # dictionnaire des fichiers a controler, la clef est
      # le nom du fichier lui meme, la valeure est une liste
      # des attributs du fichier.
      self.files = dict()

      # dictionnaire qui resume les differentes actions
      # a entreprendre en fonction des fichiers a traiter
      self.operations = {
      
         # ...

         # chaque valeure est constituée d'une ou deux listes
         # self.operations[key] = [existant]
         # self.operations[key] = ([existant][a faire])

         # liste les fichiers qui ne seront pas a 
         # traiter, soit innexistants dans le systeme 
         # de fichier, soit le nom du fichier est invalide.

         'skips' : [],

         # liste des dossiers existants.
         # liste des dossiers a creer dans rcstop.

         'dirs' : ([],[]),

         # liste des liens existants valides.
         # listes des liens existants non valides,
         # et des liens a creer.

         'links' : ([],[]),

         # liste des fichiers marques pour check-in.
         # typiquement les nouveaux fichiers.
         # liste des fichiers marques pour check-out.
         # typiquement q<les fichiers qui ont deja subit
         # un check-in.

         'checks' : ([],[]),

         # liste des fichiers auquel on va tenter d'appliquer
         # un template.
       
         'template' : [],

      }

      # ignore list files
      self.skips = self.operations['skips']

      # directory list
      self.dirsok, self.dirsko = self.operations['dirs']

      # links list
      self.linksok, self.linksko = self.operations['links']

      # embarquement, debarquement
      self.cin, self.cout = self.operations['checks']

      # liste des fichiers qui ont besoin d'un remplacement
      # exemple : $HOSTNAME dans le fichier sera remplacé par
      # le nom de machine.
      self.template = self.operations['template']


      if len(config.filelist) > 0:

         # top doit exister si on veut continuer
         # un dossier RCS sera crée a cet emplacement qui contiendra
         # tous les fichiers de revision rcs.
         if not os.path.exists(self.config.top):
            self.error('[dir] %s innexistant' % self.config.top)
            sys.exit(1)

         # premier lancement rcstop est innexistant il faut le creer
         if not os.path.exists(self.config.rcstop):
               self.warn('[dir] %s innexistant' % self.config.rcstop)
               self.dirsko.append(self.config.rcstop)

      # construction des listes d'operations a traiter
      # pour chaque fichier on verifie que les conditions
      # sont bien reunies

         for f in config.filelist:
             
            # recupere les attributs du fichier
            self.__getattr(f)   

            # si le fichier est innexistant sur le systeme
            # on l'ignore
            self.__skips(f)   
 
            # dossier a creer ou pas
            self.__dirs(f)

            # lien a creer ou pas
            self.__links(f)

            # embarquement ou debarquement
            self.__checks(f)
 
            # besoin de remplacement
            self.__template(f)


   def __getattr(self, f):
      """ Attributs du fichier.
      """
      fo = file(f, rcstop=self.config.rcstop)
      self.files.update(fo.attr)
      return None


   def __skips(self, fichier):
      """
          Peuple self.operations['skips'],
          avec la liste des fichiers a ignorer.
      """
      
      f = fichier      
      fexist = self.files[f]['filexist']

      if not fexist:
         if f not in self.skips: 
            self.warn('[fic] %s, innexistant' % f)
            self.skips.append(f)
      else:
         self.info('[fic] %s, existe' % f)
         self.info('[fic] %s, revision initiale %s, derniere revision %s' % (f, self.files[f]['rcsfirstrev'], self.files[f]['rcslastrev']))
      return None


   def __dirs(self, fichier):
      """
          Peuple self.operations['dirs'] avec deux listes, 
          les dossiers existants et les dossiers a creer.
      """

      f = fichier

      d = self.files[f]['rcsdirname']      
      dexist = self.files[f]['rcsdirexist']

      # On recherche dans les fichiers existants,
      # si le dossier de rcstop existe
      if f not in self.skips:

            if dexist:
               self.info('[dir] %s, %s existe' % (f,d))
               
               # le dossier ne sera pas cree
               if d not in self.dirsok: 
                  self.dirsok.append(d)

            else:
               self.warn('[dir] %s, %s innexistant' % (f,d))

               # ajout du dossier a creer
               if d not in self.dirsko: 
                  self.dirsko.append(d)
      return None


   def __links(self, fichier):
      """ 
          Verifie pour ce fichier si un lien RCS  valide existe
          pointant vers rcstop. Peuple la liste des liens existants,
          et des liens a creer (self.operations['links']). 
      """
      f = fichier

      # un lien comprend une source et une destination
      src = self.files[f]['rcsdirname']
      dst = self.files[f]['rcslinkname']

      # on verifie si le lien existe et si il est valide
      lexist = self.files[f]['rcslinkexist']
      lok = self.files[f]['rcslinkisok']

      if f not in self.skips:
         if lexist:
            self.info('[lnk] %s, %s-->%s existe' % (f, src, dst))

            if lok:
               if (src, dst) not in self.linksok:
                  self.info('[lnk] %s, %s-->%s lien valide' % (f, src, dst))
                  self.linksok.append((src, dst))
            else:
               if (src, dst) not in self.linksko:
                  self.error('[lnk] %s, %s-->%s lien non valide' % (f, src, dst))
                  self.linksko.append((src, dst))
         else:
            if (src, dst) not in self.linksko:
               self.warn('[lnk] %s, %s-->%s innexistant' % (f, src, dst))
               self.linksko.append((src, dst))
      return None


   def __checks(self, fichier):
      """ 
          Enregistrement des fichiers au check-in ou check-out.
          Peuple les listes self.operations['checks'].
      """
      f = fichier

      # le fichier est deja controlle par rcs
      inrcs = self.files[f]['rcscontrolled']

      if f not in self.skips:

         if inrcs:
            if f not in self.cout:
               self.info('[fic] %s, check-out' % f)
               self.cout.append(f)
         else:
            if f not in self.cin:
               self.info('[fic] %s, check-in' % f)
               self.cin.append(f)
      return None


   def __template(self, fichier):
      """ Peulple self.operations['template']. 
      """
      f = fichier
      needtemplate = self.files[f]['needtemplate']

      if f not in self.skips:
        if needtemplate:
           self.template.append(f)
      return None           


if __name__ == '__main__':
   pass
