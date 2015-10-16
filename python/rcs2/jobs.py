#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
from dire import msg
from check import rcsoperation

class dothejob(msg):
   """
       self._createdirs  : creation des nouveaux dossiers dans rcstop
       self._createlinks : creation des nouveaux liens dans le systeme de fichier
       self._rcsoperation: check-in des nouveaux fichiers a controler
                           checkout des fichiers deja controlés

       todolist est une instance de la classe du meme nom.
       
   """
   def __init__(self, todolist, action=None, dryrun=False, silent=False):     
      # affichage des messages
      self.silent = silent
      msg.__init__(self, self.silent)

      self.step('do the job')
      self.todolist = todolist
      self.action = action
      self.dryrun = dryrun
      
      self.doit()
      self.undoit() 


   def doit(self):
      """
          Verification des dossiers dans rcstop et creation
          si necessaire.
          Verification des liens et creation si necessaire,
          check-in et check-out des fichiers.
      """
      if self.action == 'do':

         self._createdirs()
         self._createlinks()
     
         for f in self.todolist.cin + self.todolist.cout:
            self._rcsoperation(f)


   def undoit(self):
      """
          Checkout des fichiers dans leur revision initiale,
          suppression des liens dans le systeme de fichier.
          Nettoyage de rcstop.
      """
      if self.action == 'undo':

         for f in self.todolist.files.keys():
            if f not in self.todolist.skips :
               first_rev = self.todolist.files[f]['rcsfirstrev']
               rcsfilename = self.todolist.files[f]['rcsfilename']
               rcsdirname = self.todolist.files[f]['rcsdirname']

               # check out de la version initiale
               if first_rev != 0:
                  self._rcsoperation(f, first_rev)
               
               # suppression du fichier de revision rcs
               os.unlink(rcsfilename)
               if not os.path.isfile(rcsfilename):   
                  self.infob('[fic] %s suppression' % rcsfilename)
               else:
                  self.errorb('[fic] %s suppression' % rcsfilename)
          
               # suppression du dossier, tant qu'il reste un fichier
               # dans le dossier rmdir raise OSError, ne supprimme
               # que les dossiers vides.
               try:
                  os.rmdir(rcsdirname)
                  self.infob('[dir] %s suppression' % rcsdirname)
               except OSError:
                  pass   
               
         # delete system files links
         self._uncreatelinks()
   
      
   def _createdirs(self):
      """ Creation des dossiers dans rcstop.
      """
      for d in self.todolist.dirsko:
         
         if not os.path.isdir(d):
            if not self.dryrun:
               os.makedirs(d, 0o600)

            if os.path.isdir(d) or self.dryrun:
               self.infob('[dir] création de %s' % d) 
            else:
               self.errorb('[dir] création de %s' % d)
         else:
            
            self.infob('[dir] existe %s' % d)


   def _createlinks(self):
      """ Creation des liens dans le systeme de fichier.
      """
      for links in self.todolist.linksko:
         src, dst = links        
         
         # si un lien ou un fichier existe a ce stade,
         # il est marque comme non valide on essaye de le supprimmer   
         if os.path.islink(dst) or os.path.exists(dst):
            try: 
               os.unlink(dst)
   
               self.infob('[lnk] suppression de %s' % dst)                     
            except:
               self.errorb('[lnk] suppression de de %s' % dst)

         # creation des liens
         if os.path.isdir(src):
            if not self.dryrun:
               os.symlink(src, dst)
            if os.path.islink(dst) or self.dryrun:
 
               self.infob('[lnk] création de %s --> %s' % (src,dst))
            else:
               self.errorb('[dir] création de %s --> %s' % (src,dst))
         else:
            self.errorb('[lnk] innexistant de %s' % src)


   def _uncreatelinks(self):
      """ Suppression des liens dans le fs.
      """     
      for links in self.todolist.linksok:
         src, dst = links

         if not self.dryrun:
            if os.path.islink(dst):
               os.unlink(dst)
         if not os.path.islink(dst) or self.dryrun:
            self.infob('[lnk] supression de %s --> %s' % (src,dst))
         else:
            self.errorb('[lnk] supression de %s --> %s' % (src,dst))


   def _rcsoperation(self, fichier, rev=''):
      """ Check-in ou check-out des fichiers. 
      """

      fop = rcsoperation(fichier)

      if fichier in self.todolist.cin:
         # check-in du fichier

         if not fop._checkin('initial check-in'):
            self.infob('[fic] %s check-in' % fichier) 
         else:
            self.errorb('[fic] %s check-in' % fichier)

      elif fichier in self.todolist.cout:
         # check-out du fichier

         if not fop._checkout(rev=rev):
            self.infob('[fic] %s check-out' % fichier)
     
            # on applique le template apres le check-out
            if fichier in self.todolist.template:
               self.infob('[fic] %s template' % fichier)
               fop._template()
         else:
            self.errorb('[fic] %s check-out' % fichier)

