#!/usr/bin/python
# -*- coding: utf-8 -*-
# Revision Control System
# permet de conserver l'historique de fichiers individuels.
# RCS est adapté pour gérer l'historique et le controle d'acces
# pour des fichiers de configuration. Pour chaque fichier controlé
# RCS en conserve l'historique et l'état (verouillé ou non) dans un 
# fichier du même nom suivit d'un suffixe ",v". Ce fichier est placé
# dans le répertoire courant ou dans ./RCS.
#
# @run:  Creation de RCSTOP si innexistant 
#        pour chaque fichier de la liste creation de l'arborescence 
#        des dossiers et sous dossiers dans RCSTOP.
#        Creation des liens symboliques dans le système de fichier
#        pointant sur le dossier de RCSTOP correspondant et checkin 
#        des nouveaux fichiers.
#        Checkout des fichiers deja controles par RCS.
#        dryrun affiche un resumé des action mais ne fait rien
#
# @change: Permet d'editer un fichier et d'enregistrer les modifica
#          tions dans rcs.
#
#

import os
import sys
import string
import subprocess
try: 
   import pexpect
except ImportError:
   sys.exit(1)

# racine de rcs
TOP=os.environ['PWD']
RCSTOP=os.path.join(TOP, 'RCS')

# liste des fichiers a controler par rcs
RCSLST='/etc/sysconfig/rcs'

# editeur de texte
TEXTEDITOR='vim'

# afficher les messages
VERBOSE=True

class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    KORED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def info(message, verbose=VERBOSE, status=''):
   if verbose:
      if (status == 'ok'): color = bcolors.OKBLUE + bcolors.BOLD     
      elif (status == 'ko'): color = bcolors.KORED + bcolors.BOLD
      else: color=''
      print str(color + message + bcolors.ENDC)   

def run(top=RCSTOP, lst=[], dryrun=False):
   ''' Creation de l'arborescence dans top, pour chaque fichier controlé.
       @systemfile: chemin complet du fichier a controler ex:"/etc/hosts"
       @systemfilename: nom du fichier a controler ex:"hosts"
       @systemdir: repertoire du fichier a controler ex:"/etc"
       @rcsdir: repertoire du fichier de revision rcs ex:"top/etc"
       @rcsfile: chemin du fichier de revision rcs ex:"top/etc/hosts,v"
       @rcsfilename: nom du fichier de revision rcs ex:"hosts,v"
       @rcslink: chemin du lien vers top ex:"/etc/RCS" 
   '''
   rcsbase = dict()
 
   if not os.path.isdir(top):
      if not dryrun:
         os.mkdir(top, 0o600)
      info('[dir][++] creation de %s' % top)
   else:
      info('[dir][..] existe %s' % top)

   for filename in lst:
      if not filename.startswith('/'): 
         continue
      systemfile = filename.strip()
      systemfilename = os.path.basename(systemfile)
      systemdir = os.path.dirname(systemfile) 
      rcsdir  = os.path.normpath(top + systemdir)
      rcsfile = os.path.join(rcsdir, systemfilename + ',v')
      rcsfilename = os.path.basename(rcsfile)
      rcslink = os.path.join(systemdir, 'RCS')

      # verification des dossiers dans TOPRCS
      if not os.path.isdir(rcsdir):
         if not dryrun:
            os.makedirs(rcsdir, 0o600)
         info('[dir][++] creation de %s' % rcsdir)
      else:
         info('[dir][..] existe %s' % rcsdir)
      # verification des liens dans le systeme
      if not os.path.islink(rcslink):
         if not dryrun:
            os.symlink(rcsdir, rcslink)
         info('[lnk][++] creation de %s --> %s' % (rcsdir, rcslink))
      else:
         info('[lnk][..] existe %s --> %s' % (rcsdir, rcslink))
      # check in des nouveaux fichiers
      if not os.path.isfile(rcsfile):
         if dryrun:
            exitstatus = 0   
         else:
            checkin = pexpect.spawn('ci -u %s' % systemfile)
            checkin.expect('>> ')
            checkin.sendline('fichier initial')
	    checkin.sendline('.')
            checkin.expect(pexpect.EOF)
            checkin.close()
            exitstatus = checkin.exitstatus
         if exitstatus == 0:
            info('[cin][ok] ajout de %s dans rcs' % systemfile, status='ok')
         else:
            info('[cin][ko] ajout de %s dans rcs' % systemfile, status='ko')
      # check out des fichiers controles
      else:
         if dryrun:
            exitstatus = 0
         else:
            # checkout = subprocess.call(co, stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT )
            checkout = pexpect.spawn('co -u %s' % systemfile)
 	    checkout.expect(pexpect.EOF)
	    checkout.close()
            exitstatus = checkout.exitstatus
         if exitstatus == 0:
            info('[out][ok] restauration de %s depuis rcs' % systemfile, status='ok')
         else:
            info('[out][ko] restauration de %s depuis rcs' % systemfile, status='ko')

      rcsbase[systemfile] = (systemdir, systemfilename, rcsdir, rcsfilename)

   if dryrun:
      print rcsbase
   return rcsbase


def change(lst=[], fichier=None, notification='modification'):
   if fichier + '\n' in lst:
      # extraction du fichier (rajoute son droit en ecriture)
      # si le fichier est verouille on passe outre.
      checkout = pexpect.spawn('co -l %s' % fichier)
      i = checkout.expect(['.*(n).*', pexpect.TIMEOUT, pexpect.EOF], 
          timeout=3)
      if i == 0:
         checkout.sendline('y')
         checkout.expect(pexpect.EOF)
         checkout.close()
      if i == 1:
         print(checkout.before, checkout.after)
         sys.exit(1)  
      if i == 2:
         checkout.close()
      if checkout.exitstatus == 0:
         info('[edt][ok] accessible en ecriture %s' % fichier, status='ok')
      else:
         info('[edt][ko] acessible en ecriture %s' % fichier, status='ko')
         sys.exit(1)
      # edition du fichier
      # os.system('xterm -e %s %s' % (TEXTEDITOR, fichier))
      edit = pexpect.spawn('xterm -e %s %s' % (TEXTEDITOR, fichier))
      edit.expect(pexpect.EOF)
      edit.close()
      # enregistrement du fichier et checkin
      checkin = pexpect.spawn('ci -u %s' % fichier)
      i = checkin.expect(['>> ', pexpect.TIMEOUT, pexpect.EOF], timeout=3)
      if i == 0:
         # le fichier a ete modifié
         checkin.sendline('%s' % notification)
         checkin.sendline('.')
         checkin.expect(pexpect.EOF)
         checkin.close()
      if i == 1:
         print(checkin.before, checkin.after)
         sys.exit(1)
      if i == 2:
         checkin.close()
      if checkin.exitstatus == 0:
         info('[cin][ok] ajout de %s dans rcs' % fichier, status='ok')
      else:
         info('[cin][ko] ajout de %s dans rcs' % fichier, status='ok')
   else:
      info('[edt][ko] le fichier n\'est pas controle par rcs', status='ko')
      sys.exit(1)


if __name__ == '__main__':
   usage = ('''
{0} run <option>
{0} change <fichier> <raison_du_changement>

Options:
  -d | --dryrun

'''.format(sys.argv[0]))

   try:
      os.chdir(TOP)
   except OSError, e:
      print e
      sys.exit(e.errno)
   try:
      with open(RCSLST, 'r') as liste:
        files = liste.readlines()
   except IOError, e:
      print e
      sys.exit(e.errno)

   if len(sys.argv) > 1:
      if sys.argv[1] == 'run':
         if '-d' in sys.argv or '--dryrun' in sys.argv:
            run(lst=files, dryrun=True)
         else:
            run(lst=files)       
      elif sys.argv[1] == 'change':
         if len(sys.argv) < 3:
            print usage
            sys.exit(1)
         fichier = sys.argv[2]
         notification= sys.argv[3:]
         change(lst=files, fichier=fichier, notification=notification)
   else:
      print usage
      sys.exit(1)
   sys.exit(0)
