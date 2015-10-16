#!/usr/bin/env python
# -*- coding: utf-8 -*-
import getopt, sys
import config
import prep
import jobs
import check
from dire import msg


def main(args):
   """
       verifie les parametres de lancement, et tente d'effectuer,
       les taches demandée.

   """
   args = sys.argv[1:]
   configfile = '/etc/rcsctl.conf'
   silent = False
   echo = msg()

   try:
      gopts,cmds = getopt.getopt(args, 'hc:s')
   except getopt.error, e:
      print "Options Error: %s" % e
      sys.exit(1)

   # traitement des options
   for o,a in gopts:
      if o == '-c':
         # fichier de configuration alternatif
         configfile=a
      if o == '-s':
         silent = True
      if o == '-h':
         usage()

   if len(cmds) == 0 \
      or cmds[0] not in ('info', 'run', 'dryrun', 'undo', 'dryundo', 'change'):
      usage()

   if 'info' in cmds: silent = True
   
   # recuperation de la configuration
   conf = config.getconfig(configfile, silent=silent)
   # recuperation des taches
   todo = prep.todolist(conf, silent=silent) 

   if cmds[0] == 'run':
      jobs.dothejob(todo, action='do', silent=silent) 


   if cmds[0] == 'dryrun':
      jobs.dothejob(todo, action='do', dryrun=True,  silent=silent)


   if cmds[0] == 'undo':
      jobs.dothejob(todo, action='undo', silent=silent)


   if cmds[0] == 'dryundo':
      jobs.dothejob(todo, action='undo', dryrun=True, silent=silent)


   if cmds[0] == 'change':
      if conf.poste != 'admin':
         echo.errorb("[fic] impossible de modifier les fichiers sur ce poste.")
         sys.exit(1)

      cmds.remove(cmds[0])
      if len(cmds) < 2:
         echo.errorb("[fic] vous devez fournir un nom de fichier, et un commentaire.")
         usage()
      else:
         fichier = cmds[0]
         comment = ' '.join(cmds[1:])
         if fichier in conf.filelist and \
            fichier not in todo.skips:
            check.rcsoperation(fichier).change(comment)            
         else:
            echo.errorb("[fic] non pris en charge %s" % fichier)
            

   if cmds[0] == 'info':
      cmds.remove(cmds[0])

      if len(cmds) == 0:
         def show(f):
            print ('%-80s|%-10s|%-5s|%-5s|' % 
                  (f, todo.files[f]['rcscontrolled'],
                      todo.files[f]['rcsfirstrev'],
                      todo.files[f]['rcslastrev'],
                  ))
         print 105*'-'
         print '%-80s|%-10s|%-5s|%-5s|' % ('filename', 'control', 'frev', 'lrev')
         print 105*'-'
         for f in todo.files.keys(): show(f)
         print 105*'-' 

      else:
        fichiers = cmds[:]
        for fichier in fichiers:
           if fichier in conf.filelist and fichier not in todo.skips: 
              print "%s:" % fichier
              for k,v in todo.files[fichier].items():
                 print("%-15s: %s" % (k,v))
           print "\n"  



def usage():
   print """
   Usage: rcsctl [options] <run |dryrun |undo |dryundo |info [fichiers, ..]| change> 

   Options:
   -h : help 
   -c <fichier de configuration>: propose un nouveau fichier de configuration.
   -s : execution silencieuse
   """
   sys.exit(1)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt, e:
        print >> sys.stderr, "\n\nExiting on user cancel."
        sys.exit(1)
