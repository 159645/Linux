#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from tempfile import NamedTemporaryFile
import string
import rpm
import sys
import os

"""
Permet de recuperer la liste des rpms construits, pour trouver
dans quel depot date la derniere version du rpm

python v2.4
"""

RPMLISTE = []
TEMP     = NamedTemporaryFile()
TEMPFILE = TEMP.name

def ReadRpmHeader(rpmfile):
    fd = os.open(rpmfile, os.O_RDONLY) 
    try:
        h = ts.hdrFromFdno(fd)
    finally:
        os.close(fd)
    return h.sprintf('%{name}'), h.sprintf('%{version}'), h.sprintf('%{release}'), h['summary'] 

def makeRpmlist(path):
    if not hasattr(makeRpmlist,"cpt"):
        makeRpmlist.cpt = 0
    dirs = os.listdir(path)
    for elem in dirs:
        elem = os.path.join(path,elem)
        if os.path.islink(elem):
            continue
        if os.path.isdir(elem):
            makeRpmlist(elem)
        if os.path.isfile(elem):
            (chem, fich) = os.path.split(elem)
            (nom, ext)   = os.path.splitext(fich)
            if ext == '.rpm':
                RPMLISTE.append((chem, fich))
                makeRpmlist.cpt += 1
                print "\r%-4d RPM (s) TROUVE : %-70s" %(makeRpmlist.cpt, fich),
                sys.stdout.flush()
    return RPMLISTE

if __name__ == '__main__':
    try:
       recherche = sys.argv[1]
    except IndexError:
       recherche = None

    os.system('clear')
    rep = os.getcwd()
    
    listefichiersrpm = makeRpmlist(rep)
    listedetaillerpm = []
   
    ts = rpm.TransactionSet()

    for chem, rpmf in listefichiersrpm:
        (nom, version, release, resume) = ReadRpmHeader(os.path.join(chem, rpmf))
        listedetaillerpm.append((chem, nom, version, release, resume))

    for chem, nom, version, release, resume in listedetaillerpm:
        depot = chem.split('/')[10:][0]
        TEMP.write("%-40s %-20s %5s %10s %-s\n" % ( nom, version, release, depot, resume))

    print '\n'
    print "%-40s  %-20s  %-5s  %-10s  %-s" % ('NOM', 'VERSION', 'REL', 'DEPOT', 'RESUME')

    if not recherche:
        os.system('grep -v ^$ %s' % TEMPFILE)
        print '\n'
    else:
        os.system('grep -i %s %s' % (recherche, TEMPFILE))
        print '\n'

    sys.exit(0)
