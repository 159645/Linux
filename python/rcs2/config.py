#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from dire import msg

class getconfig(msg):

   """

       Il y a deux type de configuration:

       - poste servant a ajouter des fichiers et modeles de fichier a controler.

         ex: 	 TOP=/fakeroot
		 RCSLST=/etc/sysconfig/rcsctl.lst
        	 TEXTEDITOR=vim
       
       - poste "client" qui ne fera que recevoir les fichiers a partirs
         des modèles.

	 ex:	TOP=/fakeroot

          
       Ce qu'on va essayer de faire ici c'est récuperer la configuration.
       Lit la configuration du fichier configfile. Construit la liste des
       fichiers a controller a partir du fichier rcslst, si le poste sert
       a modifier les fichiers.
  
       Si le poste est un poste "client", on construit la liste des fichiers
       a partir des fichiers presents dans rcstop.

       self.configfile : chemin du fichier de configuration
       self.top        : chemin racine
       self.rcstop     : chemin ou on stocke les fichiers rcs
       self.rcslst     : chemin du fichier qui liste des fichiers a controler
       self.texteditor : editeur de texte a utiliser 
       self.filelist   : la liste des fichiers a traiter
       self.poste      : admin ou client,  

   """

   def __init__(self, configfile='/etc/rcsctl.conf', silent=False):
       
      self.silent = silent
      msg.__init__(self, self.silent) 
      self.step('lecture de la configuration')

      self.configfile = configfile
      self.top = None
      self.rcstop = None
      self.rcslst = None
      self.texteditor = None
      self.filelist = list()

      # recupere les parametres de configuration
      self._getconfig()

      # recupere la liste des fichiers
      if self.rcslst:
         self.poste = 'admin'
  
         self.filelist = self._readfilelist(self.rcslst)

      else:
        self.poste = 'client'

        # il n'y a pas de liste de fichier sur le poste,
        # on construit la liste des fichiers a partir des 
        # fichiers controllés dans rcstop
        self.filelist = self._buildfilelist()


   def __str__(self):
      return str("""
profil poste       : %s
config file        : %s
fille list         : %s
top dir            : %s
top rcs dir        : %s
texteditor         : %s
controlled files   : %d
             """) % (self.poste, os.path.abspath(self.configfile), self.rcslst, self.top, \
                    self.rcstop, self.texteditor, len(self.filelist))


   def _readconfig(self, filename):
      """ lit le fichier de configuration,
          si le fichier n'est pas lisible on quitte.
      """
      try:
         with open(self.configfile, 'r') as cf:
            conf = cf.read()
         return conf.splitlines()
      except IOError, e:
         print e
         sys.exit(e.errno)


   def _getconfig(self):

      # recupere les parametres 
      self._config = self._readconfig(self.configfile)
      for param in self._config:

         if param.startswith('TOP='):
            self.top = param.replace('TOP=','').strip('"\'')
            self.rcstop = os.path.join(self.top, 'RCS')

         elif param.startswith('RCSLST='):
            self.rcslst = param.replace('RCSLST=','').strip('"\'')

         elif param.startswith('TEXTEDITOR='):
            self.texteditor = param.replace('TEXTEDITOR=','').strip('"\'')
      

   def _readfilelist(self, filename):
      """ retourne la liste des fichiers a controller, 
          si le fichier n'est pas accessible on quitte.
      """
      files = []
      try:
         with open(filename, 'r') as f:
            # read first line
            line = f.readline()
            if not line: 
               return files
            else:
               while line:
                  line = f.readline()
                  files.append(line)

            # on supprimme les doublons de la liste
            # en la transformant en essemble
            files = set(files)

            # on itere sur une copie de l'enssemble
            # pour supprimmer des elements de l'original
            for line in files.copy():
               if not line.startswith('/'):
                  files.remove(line)
            files = list(files)

            for line in files:
               files[files.index(line)] = line.strip()

      except (IOError, TypeError):
         self.error('Impossible de recupérer la liste des fichiers')
         sys.exit(1)

      return files


   def _buildfilelist(self):
      """ le poste est "client" on n'ajoute pas de fichier a controller
          on se contente d'ecrasé les fichiers locaux par les fichiers controles
      """
      files =[]

      for root, dirs, files in os.walk(self.rcstop):

         files = [ os.path.join(root, file).replace(self.rcstop,'')\
                   .strip(',v') \
                   for file in files 
                 ]
 
      return files


# conf = getconfig()
