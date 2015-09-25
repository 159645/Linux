#!/usr/bin/python
# -*- coding: utf-8 -*-
# Revision Control System
# permet de conserver l'historique de fichiers individuels.
# rcs est adapté pour gérer l'historique et le controle d'acces
# pour des fichiers de configuration. Pour chaque fichier controlé
# rcs en conserve l'historique et l'état (verouillé ou non) dans un 
# fichier du même nom suivit d'un suffixe ",v". Ce fichier est placé
# dans le répertoire courant ou dans ./RCS.
# Dans chaque dossier ou un fichier est controlé par rcs on va créer
# un lien symbolique dossier/RCS vers RCSTOP/dossier, ce qui permet 
# de centraliser les fichier de configuration dans un endroit du système 
# ou sur une zone reseau. Avec une tache cron on pourra regulièrement 
# extraire la dernière révision du fichier vers le fichier d'origine.
# si on veut gerer par exemple /etc/hosts
# creation de RCSTOP/etc 
# creation d'un lien symbolique /etc/RCS --> RCSTOP/etc
# le fichier de revision sera stocke dans RCSTOP/etc/hosts,v
#
# Utiliser rcs:
# ajouter un fichier a controler:
# $ ci -u /etc/hosts
# la commande a pour effet de créer le fichier RCS/hosts.v
# le fichier /etc/hosts a perdu son droit en ecriture.
# modifier un fichier: 
# $ co -l /etc/hosts
# l'option -l permet d'eviter une autre extraction durant la modification
# apporter les modifications au fichier
# $ ci -u /etc/hosts
# voir l'historique des modification:
# $ rlog /etc/hosts
#
# Utiliser le script:
# /etc/rcsctl
# modifier la valeur de TOP pour indiquer ou stocker les fichier controlés 
# modifier la valeur de RCSLST pour indiquer l'emplacement de la liste des
# fichiers a controler.
# modifier la valeur de TEXTEDITOR pour indiquer l'editeur de texte a util
# iser pour la modification des fichiers controles.
# 
# <...
# TOP=/root
# RCSLST=/etc/sysconfig/rcsctl
# TEXTEDITOR=vim
# ...>
#
# /etc/sysconfig/rcsctl
# pour chaque fichier a controler ajouter une ligne au fichier avec le nom
# complet du fichier
#
# <...
# # check itself
# /etc/sysconfig/rcs
# # ajouter les fichiers a controler ci-dessous
#
# ...> 
#
# @run:  Creation de RCSTOP si innexistant 
#        pour chaque fichier de /etc/sysconfig/rcsctl creation de l'arborescence 
#        des dossiers et sous dossiers dans RCSTOP.
#        Creation des liens symboliques dans le système de fichier pointant sur le 
#        dossier de RCSTOP correspondant. 
#        Enregistrement des nouveaux fichiers dans rcs.
#        Checkout des fichiers deja controles par RCS.
#        dryrun affiche un resumé des action mais ne fait rien
#
# @change: Permet d'editer un fichier et d'enregistrer les modifica
#          tions dans rcs.
#
import os
import sys
import string
import subprocess
try: 
   import pexpect
except ImportError:
   print 'yum -y install pexpect.noarch'
   sys.exit(1)

usage = ('''
{0} run <option>

option:
  -d | --dryrun    : ne fait rien affiche juste les action 
  -k | --dryrunko  : idem si tout va mal
  -b | --back      : on annule


{0} print <item>   : affiche les elements demande ou tous

item:
  dir : affiche les dossiers de RCSTOP
  fic : affiche les fichiers controlés par rcs 
  lnk : affiche les liens ajoutés au systeme
  cin : affiche les fichiers qui seront ajoutes a rcs 
  cout: affiche les fichiers a extraire de rcs

{0} rlog <fichier> : affiche l'historique des modifications

{0} change <fichier> <raison_du_changement>

modifier un fichier et enregistre les modifications dans rcs

'''.format(sys.argv[0]))

class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    KORED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def info(message, verbose=True, status=''):
   if verbose:
      if (status == 'ok'): color = bcolors.OKBLUE + bcolors.BOLD     
      elif (status == 'ko'): color = bcolors.KORED + bcolors.BOLD
      else: color=''
      print str(color + message + bcolors.ENDC)   

def printstat(lst=[], items=[]):
   ''' affiche les elements dir, fic, lnk, cin, cout ou all
   '''
   data = run(lst=lst, dryrun=True, verbose=False)
   if len(items) == 0: 
      items.append('all')
   for k in data.keys():
      if k in items or 'all' in items:
         if k == 'cin' or k == 'cout':
            for e in set(data[k]):
               try: info('[%s] %s %s' % (k, e[0], e[1]), status=e[1])
               except IndexError: pass
         else:
            for e in set(data[k]): info('[%s] %s' % (k,e))

def run(top=None, lst=[], dryrun=False, dryrunko=False, verbose=True):
   ''' Creation de l'arborescence dans top, pour chaque fichier controlé.
       @systemfile: chemin complet du fichier a controler ex:"/etc/hosts"
       @systemfilename: nom du fichier a controler ex:"hosts"
       @systemdir: repertoire du fichier a controler ex:"/etc"
       @rcsdir: repertoire du fichier de revision rcs ex:"top/etc"
       @rcsfile: chemin du fichier de revision rcs ex:"top/etc/hosts,v"
       @rcsfilename: nom du fichier de revision rcs ex:"hosts,v"
       @rcslink: chemin du lien vers top ex:"/etc/RCS" 
   '''
   #rcsbase = dict()
   rcsbase = {'dir':[], 'fic':[], 'lnk':[], 'cin':[()], 'cout':[()]} 

   if not os.path.isdir(top):
      if not dryrun:
         os.mkdir(top, 0o600)
      info('[dir][++] creation de %s' % top, verbose=verbose)
   else:
      info('[dir][..] existe %s' % top, verbose=verbose)
      rcsbase['dir'].append(top)

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

      if not os.path.isfile(systemfile):
         info('[fic][??] innexistant %s' % systemfile, status='ko', verbose=verbose)
         continue
      info('[fic][..] existe %s' % systemfile, verbose=verbose)
      rcsbase['fic'].append(systemfile)
      # verification des dossiers dans TOPRCS
      if not os.path.isdir(rcsdir):
         if not dryrun:
            os.makedirs(rcsdir, 0o600)
         info('[dir][++] creation de %s' % rcsdir, verbose=verbose)
      else:
         info('[dir][..] existe %s' % rcsdir, verbose=verbose)
      rcsbase['dir'].append(rcsdir)
      # verification des liens dans le systeme
      if not os.path.islink(rcslink):
         if not dryrun:
            os.symlink(rcsdir, rcslink)
         info('[lnk][++] creation de %s --> %s' % (rcsdir, rcslink), verbose=verbose)
      else:
         info('[lnk][..] existe %s --> %s' % (rcsdir, rcslink), verbose=verbose)
      rcsbase['lnk'].append(rcslink) 
      # check in des nouveaux fichiers
      if not os.path.isfile(rcsfile):
         if dryrun: exitstatus = 0
         elif dryrunko: exitstatus = 1
         else:
            checkin = pexpect.spawn('ci -u %s' % systemfile)
            checkin.expect('>> ')
            checkin.sendline('fichier initial')
	    checkin.sendline('.')
            checkin.expect(pexpect.EOF)
            checkin.close()
            exitstatus = checkin.exitstatus
         if exitstatus == 0:
            info('[cin][ok] ajout de %s dans rcs' % systemfile, status='ok', verbose=verbose)
            rcsbase['cin'].append((systemfile, 'ok'))
         else:
            info('[cin][ko] ajout de %s dans rcs' % systemfile, status='ko', verbose=verbose)
            rcsbase['cin'].append((systemfile, 'ko'))
      # check out des fichiers controles
      else:
         if dryrun: exitstatus = 0
         elif dryrunko: exitstatus = 1
         else:
            # checkout = subprocess.call(co, stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT )
            checkout = pexpect.spawn('co -u %s' % systemfile)
 	    checkout.expect(pexpect.EOF)
	    checkout.close()
            exitstatus = checkout.exitstatus
         if exitstatus == 0:
            info('[out][ok] restauration de %s depuis rcs' % systemfile, status='ok', verbose=verbose)
            rcsbase['cout'].append((systemfile, 'ok'))
         else:
            info('[out][ko] restauration de %s depuis rcs' % systemfile, status='ko', verbose=verbose)
            rcsbase['cout'].append((systemfile, 'ko'))
   return rcsbase

def runback(lst=[]):
   ''' retablit les fichiers dans leur version initiale
       supprimme les liens dans le systeme de fichier
   '''
   data = run(lst=lst, dryrun=True, verbose=False)
   # restauration des fichier en version 1.1
   # et suppression des liens symboliques
   for k in data.keys():
      if k == 'fic':
         for fic in set(data[k]):
            if os.path.exists(os.path.join(os.path.dirname(fic),'RCS')):
               checkout = pexpect.spawn('co -u1.1 %s' % fic)
               checkout.expect(pexpect.EOF)
               checkout.close()
               if checkout.exitstatus == 0:
                  info('[out][ok] restauration en version 1.1 de %s depuis rcs' % fic, status='ok')
               else:
                  info('[out][ko] restauration en version 1.1 de %s depuis rcs' % fic, status='ko')
            else:
               info('[out] rien a faire pour %s' % fic)
      if k == 'lnk':
         for lnk in set(data[k]):
            if os.path.islink(lnk):
               os.unlink(lnk)
               info('[lnk] suppression de %s' % lnk)
            else:
               info('[lnk] rien a faire pour %s' % lnk)

def change(lst=[], fic=None, notification='modification', verbose=True):
   ''' modifie un fichier et enregistre dans rcs la revision
   '''
   if fic + '\n' in lst:
      # extraction du fichier (rajoute son droit en ecriture)
      # si le fichier est verouille on passe outre.
      checkout = pexpect.spawn('co -l %s' % fic)
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
         info('[edt][ok] accessible en ecriture %s' % fic, status='ok', verbose=verbose)
      else:
         info('[edt][ko] acessible en ecriture %s' % fic, status='ko', verbose=verbose)
         sys.exit(1)
      # edition du fichier
      # os.system('xterm -e %s %s' % (TEXTEDITOR, fichier))
      edit = pexpect.spawn('xterm -e %s %s' % (TEXTEDITOR, fic))
      edit.expect(pexpect.EOF)
      edit.close()
      # enregistrement du fichier et checkin
      checkin = pexpect.spawn('ci -u %s' % fic)
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
         info('[cin][ok] ajout de %s dans rcs' % fic, status='ok', verbose=verbose)
      else:
         info('[cin][ko] ajout de %s dans rcs' % fic, status='ok', verbose=verbose)
   else:
      info('[edt][ko] le fichier n\'est pas controle par rcs', status='ko',verbose=verbose)
      sys.exit(1)

def rlog(lst=[], fic=None):
   ''' affiche le log des modifications du fichier
   '''
   if fic + '\n' in lst:
      if os.path.exists(os.path.join(os.path.dirname(fic),'RCS')):
         os.system('rlog %s' % fic)
      else:
         info('[log] rien a faire pour %s' %fic)
   else:
      info('[log] le fichier %s n\'est pas controle par rcs' % fic, status='ko')
      printstat(lst=lst, items=['fic'])

if __name__ == '__main__':
   try:
      with open('/etc/rcsctl', 'r') as conf: conf = conf.readlines()
      for line in conf:
         if line.startswith('TOP'): TOP=line.split('=')[1].strip()
         if line.startswith('RCSLST'): RCSLST=line.split('=')[1].strip()
         if line.startswith('TEXTEDITOR'): TEXTEDITOR=line.split('=')[1].strip()
      RCSTOP=os.path.join(TOP, 'RCS')
   except IOError, e:
      print e
      sys.exit(e.errno)
   try:
      os.chdir(TOP)
   except OSError, e:
      print e
      sys.exit(e.errno)
   try:
      with open(RCSLST, 'r') as liste:
        rcsfiles = liste.readlines()
   except IOError, e:
      print e
      sys.exit(e.errno)

   if len(sys.argv) > 1:
      if sys.argv[1] == 'run':
         if '-d' in sys.argv or '--dryrun' in sys.argv:
            run(top=RCSTOP, lst=rcsfiles, dryrun=True, dryrunko=False)
         elif '-k' in sys.argv or '--dryrunko' in sys.argv:
            run(top=RCSTOP, lst=rcsfiles, dryrun=False, dryrunko=True)
         elif '-b' in sys.argv or '--back' in sys.argv:
            runback(top=RCSTOP, lst=rcsfiles)
         else:
            run(top=RCSTOP, lst=rcsfiles)       
      elif sys.argv[1] == 'change':
         if len(sys.argv) < 3:
            print usage
            sys.exit(1)
         fichier = sys.argv[2]
         notification= ' '.join(sys.argv[3:])
         change(lst=rcsfiles, fic=fichier, notification=notification)
      elif sys.argv[1] == 'print':
         arg = sys.argv[2:]
         printstat(lst=rcsfiles, items=arg)
      elif sys.argv[1] == 'rlog':
         try:
            fichier = sys.argv[2]
         except IndexError:
            sys.exit(1)
         rlog(lst=rcsfiles, fic=fichier)
      else:
         print usage
         sys.exit(1)
   else:
      print usage
      sys.exit(1)
   sys.exit(0)
