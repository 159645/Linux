#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
import time
import sys
import os


# resultat de la recherche 
finds = []

# taille minimum du fichier
minsize=500

# liste des chemins de recherche
searchpaths = ( '/usr', '/etc', '/tmp' )

# ce qu'on recherche
search = ('.avi', '.mkv')


class pathsearch:
   '''
       Recherche recursivement dans path
       les fichiers avec les extensions listee dans
       search. Un peut a la maniere de os.walk()
   '''
   def __init__(self, path='/', search=(), nice=True):
      self.path = path
      self.search = search
      # nom du thread courant ou 'MainThread'
      self.tname = threading.current_thread().name
      self.f = 0
      self.g = 0
      self.nice = nice
 
      # path : doit exister
      if not os.path.exists(self.path):
         raise Exception('self.path')

      # search : pour endswith il faut str ou tuple
      if not isinstance(self.search, tuple):
         raise Exception('self.search')

   def start_search(self):
      print ("[{:^20}] : Start").format(self.tname)
      self.walk(self.path)
      print ("\n[{:^20}] : Finish find {} item(s)").format(self.tname, self.f)

   def echo(self, msg):
      stdoutlock.acquire()
      sys.stdout.write(msg),
      sys.stdout.flush()

      if self.nice:
         # on laisse souffler le cpu
         time.sleep(0.0001)
      stdoutlock.release()

   def walk(self, path):
      try:
         l = (os.path.join(path, x) for x in os.listdir(path))
         for x in l:
            if os.path.isdir(x):
               self.walk(x)
            elif os.path.isfile(x):
               if x.endswith(self.search):
                  # on ajoute le fichier 
                  if (os.stat(x).st_size /1024/1024 > minsize):
                     finds.append(x)
                     self.f +=1
            self.g +=1
            info = "\r[{:^20}] : Searching, {}/{}".format(self.tname, self.f, self.g)
            self.echo(info)
  
      except OSError: pass # Permission denied
      except KeyboardInterrupt, e:
         print >> sys.stderr, "\nExit on demand."
         sys.exit(1)



if __name__ == '__main__':

   stdoutlock = threading.Lock()

   for i in range(0, len(searchpaths)):  

      # tname nom du thread
      # spath emplacement ou se fait la recherche pour ce thread
      tname = spath = searchpaths[i]     

      # instance de la classe pathsearch
      # path : le chemin ou on doit chercher
      # search : tuple des extensions de fichier a chercher
      o = pathsearch(path=spath, search=search)
      
      # creation de l'objet thread
      t = threading.Thread(target=o.start_search)
      # Au momment ou on cree l'objet le thread est 'MainThread'        
      o.tname = t.name = tname    
      t.start()
  
      if not t.is_alive():
         print ("\n[{:^20}] : Fail starting").format(tname)


   # On attend que tous les Threads terminent
   for thread in threading.enumerate()[1:]:
      thread.join()

   print "\nSearch is Done!"

   for find in finds:
      print find
