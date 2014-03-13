def getURL(request):
    '''
    gibt die URL aus der Anfrage zurueck
    '''
    # Splittet die Anfrage nach der ersten Zeile
    first_line = request.split('\n')[0]
    # holt die url
    url = first_line.split(' ')[1]
    return url
        
def delete_http(url):
    '''
    loescht "http://" aus der URL
    '''
    http_pos = url.find("://")
    if (http_pos==-1):
        temp = url
    else: # wenn "://" in der url vorkommt
        temp = url[(http_pos+3):] # hole den Rest der Url nach "://"
    return temp

def find_webserver(url):
    '''
    Gibt den Webserver aus der URL zurueck
    '''
    port_pos = url.find(":") # Position des Ports
    webserver_pos = url.find("/") # Positions des Endes des Webservers
    if webserver_pos == -1:
        webserver_pos = len(url)
    if (port_pos==-1 or webserver_pos < port_pos): # wenn kein Port gegeben ist
        port = 80 # Default-Port
        webserver = url[:webserver_pos]
    else: 
        port = int((url[(port_pos+1):])[:webserver_pos-port_pos-1]) # Port aus der Anfrage
        webserver = url[:port_pos] # Webserver aus der Anfrage
    return (webserver, port)

def checkHeader(data):
    '''
    Prueft ob der Content-Type in der Anfrage "text/html" ist
    '''
    content = "Content-Type: "
    if content in data:
        if "text/html" in data.split(content)[1].split(";")[0]:
            return 1
    return 0