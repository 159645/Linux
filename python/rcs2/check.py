#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import errno
import platform
from string import Template


class rcsoperation:
   """ wrap rcs commande """

   def __init__(self, fichier):
      self.fichier = fichier
      self.editor = 'vim'

      # dictionnaire des valeures a remplacer dans le fichier
      # apres le check-out si besoin.
      self.templated = { 'HOSTNAME' : platform.node(),
                         'ARCH'     : platform.machine(),
                         'SERVEUR1' : 'serveur1.domaine.fr',
                         'SERVEUR2' : 'serveur2.domaine.fr'
                       }


   def _template(self):
      """ si le fichier a besoin de remplacer des valeurs on applique
         après le checkout
      """
     
      fread = Template(open(self.fichier).read())
      fread = fread.safe_substitute(self.templated)
     
      with open(self.fichier, 'w') as new:
         new.write(fread)


   def _checkin(self, checkin_info=''):
      """ checkin du fichier """
      cin = self.check('ci -u %s' % self.fichier, checkin_info)[0]

      return cin


   def _checkout(self, checkin_info='', rev=''):
      """ check out du fichier """
      if rev != '':
         if rev not in self.revs():
            rev=''

      cout = self.check('co -u{} {}'.format(rev, self.fichier))[0]

      return cout


   def _unlock(self, checkin_info=''):
      """ checkout et supprimme le lock """
      unlock = self.check('co -l %s' % self.fichier)[0]  

      return unlock


   def _edit(self, checkin_info=''):
      edit = self.check('xterm -fa "size=14" -e {} {}'.format (self.editor, self.fichier))[0]

      return edit


   def _rlog(self):
      """ retourne le log du fichier """
      log = self.check('rlog %s' % self.fichier)[1]

      return log


   def revs(self):
      """ retourne une liste des revisions du fichier """
      rl = []
      log = self._rlog()      

      try:
         for line in log:
            if line.startswith('revision'):
               rl.append(line.split()[1])

      finally:

         return rl


   def change(self, checkin_info=''):
      """
          modifie un fichier, supprimmer le lock du fichier
          editer le fichier avec vim, checkin du fichier
      """
      exit = 0
      for action in self._unlock, self._edit, self._checkin:
         result = action(checkin_info)

         if result:
            exit = result
            break

      return exit


   def check(self, cmd='', stdinput=''):
      if not cmd:
         return(None, None, None)

      cmd = cmd.split()
      exe = cmd[0]
      args = cmd

      stdin_read, stdin_write = os.pipe()   
      stdout_read, stdout_write = os.pipe()
      stderr_read, stderr_write = os.pipe()

      child = os.fork()
      if child == 0:
         # processus fils
         os.close(stdin_write)
         os.close(stdout_read)
         os.close(stderr_read)

         os.dup2(stdin_read, 0)
         os.dup2(stdout_write, 1)
         os.dup2(stderr_write, 2)
      
         # on execute la commande
         os.execvp(exe, cmd)
         # ...    
      else: 
         # processus parent
         os.close(stdin_read)
         os.close(stdout_write)
         os.close(stderr_write)

         if len(stdinput) > 0:
            if exe == 'ci':
               # dans le cas d'un checkin ou ajoute \n.\n
               stdinput = stdinput + '\n.\n'        
            # os.write travaillle avec des bytes string
            os.write(stdin_write, stdinput.encode())

         # wait 
         try:
            (child_pid, child_exitstatus) = os.waitpid(child, 0)
         except OSError, (errno, msg):
            print __name__, "waitpid:", msg

         child_stdout = os.fdopen(stdout_read).readlines()
         child_stderr = os.fdopen(stderr_read).readlines()
 
      return(child_exitstatus, child_stdout, child_stderr)

