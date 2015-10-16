#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import errno


def execwithdialog(cmd='', stdinput=''):
   """
       Utilisation d'un fork pour executer une commande
       communication entre le processus parent et fils via des pipes

        pere              fils
        ------------------------------ 
        stdin_write ----> stdin_read  
        stdout_read <---- stdout_write
        stderr_read <---- stderr_write

       1) Creation des différents pipes, pour permettre la 
          communication entre les deux processus. Le processus
          fils heritant des descripteurs du pere.
       2) Creation du nouveau processus
       3) Le pere ecrit dans le pipe stdin_write, l'autre bout du pipe
          est dupliqué sur stdin du processus fils.
       4) Le processus fils va ecrire sur stdout_write et stderr_write,
          dupliques respectivement sur stdout et stderr. Le processus
          pere va lire stdout_read et stderr_read.  
       
   """
   if not cmd:
      return(None, None)

   cmd = cmd.split()
   exe = cmd[0]
   args = cmd

   # pipe pour stdin
   stdin_read, stdin_write = os.pipe()   
   # pipe pour stdout
   stdout_read, stdout_write = os.pipe()
   # pipe pour stderr
   stderr_read, stderr_write = os.pipe()

   child = os.fork()

   if child == 0:
      # le processus fils herite des descripteurs
      # du parent.
      
      # on utilise stdin pour lire du process parent
      os.close(stdin_write)
      # on utilise stdout et stderr pour ecrire vers le parent
      os.close(stdout_read)
      os.close(stderr_read)

      # on duplique stdin, stdout et stderr
      os.dup2(stdin_read, 0)
      os.dup2(stdout_write, 1)
      os.dup2(stderr_write, 2)
      
      # on execute la commande
      os.execvp(exe, cmd)

      # os.execvp va recouvrir le processus courant
      # tout ce qui se trouve a cet endroit ne sera jamais 
      # ...

   else: 
      # processus parent

      # on va ecrire dans le pipe stdin_write pour le procesus fils
      os.close(stdin_read)
      # on va lire depuis le pipe stdout_read et stderr_read du fils
      os.close(stdout_write)
      os.close(stderr_write)

      # ecriture dans le pipe a destination du fils
      if len(stdinput) > 0:
         write2stdin = ("%s\n.\n" % stdinput ).encode()
         os.write(stdin_write, write2stdin)

      # on attend que le fils retourne
      try:
         (child_pid, child_exitstatus) = os.waitpid(child, 0)
      except OSError, (errno, msg):
         print __name__, "waitpid:", msg

      # on ouvre le bout du pipe qui va recevoir les données
      # on peut directement utiliser os.read() pour recevoir 
      # les données. Mais en utilisant fdopen on utilise du
      # coup un file object qui est plus pratique a manipuler
      child_stdout = os.fdopen(stdout_read).readlines()
      child_stderr = os.fdopen(stderr_read).readlines()
 
   return(child_exitstatus, child_stdout, child_stderr)


if __name__ == '__main__':
   ret, stdout, stderr = execwithdialog('ci -u /tmp/test', 'modification des tests')
   print stdout
   print stderr
   print ret

