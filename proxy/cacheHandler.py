import hashlib
import os
import time

class CacheHandler():
    '''
    Klasse zum Verwalten des Caches
    '''
    def __init__(self, timeout, buffer_size):
        '''
        initialisiert den CacheHandler (Ordner Zwischenspeicher wird angelegt)
        '''
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.cache_dir = "zwischenspeicher"
        self.cache_copy = []
        # wenn das Verzeichnis "zwischenspeicher noch nicht vorhanden ist, wird es angelegt
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir) # oeffnet das Verzeichnis 
            except:
                print "Error: Das Verzeichnis Zwischenspeicher konnte nicht angelegt werden" 
        else:
            for ele in os.listdir(self.cache_dir+"/"):
                os.remove(self.cache_dir+"/"+ele)
    
    def pathInHash(self, path):
        '''
        wandelt eine URL in ein Hash-Objekt um
        '''
        m = hashlib.md5() 
        m.update(path) # erzeugt ein Hash-Objekt aus dem Pfad
        filename = m.hexdigest() # wandelt den Hash-Objekt in Hex-Zahlen um
        return filename
    
    def writeFile(self, path, data):
        '''
        schreibt eine Datei in den Cache
        '''
        # wenn die Buffer-Size vom Cache erreicht ist, wird die Datei geloescht, auf die am laengsten nicht mehr zugegriffen wurde
        if len(self.cache_copy) == self.buffer_size: 
            toDelete = self.cache_copy[self.indexOf(path)]
            self.cache_copy.remove(toDelete)
            os.remove(self.cache_dir + "/" + toDelete[0] + ".txt")
        cache_filename = self.pathInHash(path)
        self.cache_copy.append((cache_filename, time.localtime()))
        try:
            f = open(self.cache_dir + "/" + cache_filename + ".txt", 'wb')
            f.writelines(data)
            f.close() # erzeugt eine Datei und schreibt den Seiteninhalt(data) in die Datei
        except:
            print "Schreiben fehlgeschlagen. Cache-Datei nicht angelegt."
        
    def openFile(self, cache_filename):
        '''
        Holt den Inhalt aus einer Textdatei
        '''
        data = []
        if os.path.exists(self.cache_dir + "/" + cache_filename):
            f = open(self.cache_dir + "/" + cache_filename, "r")
            data = f.readlines()
            f.close()
        dataCopy = self.cache_copy[self.indexOf(cache_filename)]
        self.cache_copy.remove(dataCopy)
        self.cache_copy.append(dataCopy)
        return "".join(data)
            
    def checkFile(self, cache_filename):
        '''
        prueft ob eine Datei mit dem "cache_filename" existiert und gibt den Inhalt zurueck
        '''
        for f in self.cache_copy:
            if f[0] == cache_filename:
                if time.mktime(f[1]) > (time.mktime(time.localtime()) - self.timeout):
                    return self.openFile(f[0] + ".txt")
        return ""

    def indexOf(self, cache_filename):
        '''
        Gibt den Index des Cache-Files in der Liste zurueck
        '''
        index = -1
        for ele in self.cache_copy:
            index += 1
            if ele[0] == cache_filename:
                break
        return index
