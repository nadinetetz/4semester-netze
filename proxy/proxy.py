import erlebnis
import socket
import sys
import re
import select
import requestHandler
from cacheHandler import CacheHandler
import time

BACKLOG = 200
MAX_DATA_RECV = 4096
PORT_UDP = 10000
PORT_RECV = 20000

def startProxy(port, timeout):
    '''
    Startet und verwaltet die Sockets fuer den Webbrowser, den Broadcast, den Netzwerkverkehr
    '''
    host = '' # leerer String fuer localhost 
    try:
        sock_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # erzeugt einen Socket 
        sock_b.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # wenn sich der Server beendet kann er wieder genutzt werden
        sock_b.bind((host, port)) # verbinden des Sockets mit dem Host und Port
        sock_b.listen(BACKLOG)
        
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_udp.bind(("<broadcast>", PORT_UDP))

        sock_r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # erzeugt einen Socket 
        sock_r.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # wenn sich der Server beendet kann er wieder genutzt werden
        sock_r.bind((host, PORT_RECV)) # verbinden des Sockets mit dem Host und Port

    except socket.error, (value, message):
        if sock_b:
            sock_b.close()
        print "Socket kann nicht geoeffnet werden:", message
        sys.exit(1)

    timeLis = []
    keyList = []
    req = {}
    data = []
    
    while 1:
        to = checkTimeout(timeLis)
        
        if to == None:
            while keyList != []:
                if req[keyList[0]][1] != "":
                    proxy_thread(req[keyList[0]][0], req[keyList[0]][1])
                req.pop(keyList[0])
                keyList.remove(keyList[0])
            req = {}
                
        listIn, listOut, listTmp = select.select([sock_b, sock_udp, sock_r], [], [], to)

        for sock in listIn:
            
            #sock hoert auf browser
            if sock == sock_b:
                so = sock.accept()
                conn = so[0]
                request = conn.recv(MAX_DATA_RECV)
                if request != "":
                    cache_filename = cacheHandler.pathInHash(requestHandler.getURL(request))
                    d = cacheHandler.checkFile(cache_filename)
                    #wenn wir die Anfrage selbst haben
                    if d != "":
                        conn.send(d)
                        conn.close()
                    #sonst: Broadcast
                    else:
                        keyList.append(cache_filename)
                        req[cache_filename] = (conn, request)
                        broadcast(cache_filename, PORT_UDP)
                #timeout fuer Anfrage setzen
                timeLis.append(time.mktime(time.localtime()) + 0.2)
                
            #sock erhaelt Anfrage von Broadcast
            if sock == sock_udp:
                cache_filename, addr = sock.recvfrom(1000)
                rFile = cacheHandler.checkFile(cache_filename)
                a = (addr[0], PORT_RECV)
                rFile = makeErlebnis(rFile)
                if rFile != "":
                    l = rFile.split("\n")
                    for line in l:
                        sock.sendto(line, a)
                    sock.sendto(cacheHandler.pathInHash("complete"), a)

            #sock erhaelt Antwort von Broadcast
            if sock == sock_r:
                d = sock.recv(1000)
                if d != cacheHandler.pathInHash("complete"):
                    data.append(d)
                else:
                    content = "\n".join(data)
                    if content != "":
                        path = requestHandler.getURL(content)
                        cache_filename = cacheHandler.pathInHash(path)
                        for k in keyList:
                            if k == cache_filename:
                                content = makeErlebnis(content)
                                conn = req[k][0]
                                conn.send(content)
                                conn.close()
                        if cache_filename in keyList:
                            keyList.remove(cache_filename)
    sock_b.close()
    sock_udp.close()
    sock_r.close()
    
def checkTimeout(timeLis):
    '''
    aktualisiert den Cache
    '''
    if timeLis != []:
        if timeLis[0] > time.mktime(time.localtime()):
            return timeLis[0] - time.mktime(time.localtime())
        else:
            t = timeLis[0]
            timeLis.remove(t)
    return None
    
def proxy_thread(conn, request):
    '''
    Arbeitet eine Anfrage vom Webserver ab, die nicht im Cache ist
    '''
    url = requestHandler.getURL(request)
    temp = requestHandler.delete_http(url)
    webserver, port = requestHandler.find_webserver(temp)

    try:
        # erzeugt einen Socket fuer die Verbindung zum Webserver
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        s.connect((webserver, port))
        if "connection: keep-alive" in request.lower():
            p = request.replace("Connection: keep-alive", "Connection: close") # setzt die Connection der Anfrage auf "close"
        else:
            p = request
        # Abfangen wenn kein Accept-Eintrag im Header ist
        if "Accept-Encoding" in p:
            p = re.sub("Accept-Encoding:.*\r\n", "", p) # loescht den Eintrag "Accept-Encoding" aus dem Anfrage-String
        s.send(p)
        data = ""
        while 1:
            d = s.recv(MAX_DATA_RECV) # Daten vom Webserver   
            data += d
            if (len(d) <= 0): # solange die Antwort nicht leer ist
                break
        cacheHandler.writeFile(url, data)
        page = makeErlebnis(data)
        conn.send(page) # sendet die Antwort an den Browser
        s.close()
        conn.close()
    except socket.error, exc:
        import traceback
        traceback.print_exc()
        if s:
            s.close()
        if conn:
            conn.close()
        print "Runtime Error:", exc
        sys.exit(1)

def makeErlebnis(data):
    if requestHandler.checkHeader(data) == 1:
        page = erlebnis.erlebnis(data)
    else:
        page = data
    return page

def broadcast(cache_filename, port):
    '''
    schickt einen broadcast ins Netzwerk
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.sendto(cache_filename, ("<broadcast>", port))
    sock.close()
    
if __name__ == '__main__':
    # ueberpruefen der Anzahl der Kommandozeilenparameter
    if (len(sys.argv) == 4):
        port = int(sys.argv[1])
        timeout = sys.argv[2] # oder 0.0005 # timeout fuer den Cache
    cacheHandler = CacheHandler(int(sys.argv[2]), sys.argv[3])
    #cacheHandler.initCache(int(sys.argv[2]), sys.argv[3])
    startProxy(port, timeout)  
