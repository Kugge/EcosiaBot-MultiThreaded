import requests
import random
import os
import time
import sys
import proxyscrape
from threading import Thread
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QInputDialog, QHeaderView
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer



def printf(txt):
    sys.stdout.write(txt + "\n")
    sys.stdout.flush()


def gen_icon():
    if not os.path.isfile("data/icon.png"):
        printf("Downloading icon...")
        if not os.path.isdir('data'):
            os.makedirs("data")
        url = "https://raw.githubusercontent.com/Kugge/EcosiaBot-Utilities/master/tree.png"
        file = requests.get(url, timeout=10)
        open("data/icon.png", 'wb').write(file.content)
        printf("Done!")


def print_banner():
    url = "https://raw.githubusercontent.com/Kugge/EcosiaBot-Utilities/master/banner.txt"
    file = requests.get(url, timeout=10)
    print(file.text)


def get_wordlist():
    printf("Downloading wordlist...")
    if not os.path.isdir('data'):
        os.makedirs("data")
    url = "https://raw.githubusercontent.com/Kugge/EcosiaBot-Utilities/master/dictionnary.txt"
    file = requests.get(url, timeout=10)
    open("data/dictionnary.txt", 'wb').write(file.content)
    txt = open("data/dictionnary.txt").read()
    return txt.split("\n")


def get_agents():
    printf("Downloading user agents...")
    if not os.path.isdir('data'):
        os.makedirs("data")
    url = "https://raw.githubusercontent.com/Kugge/EcosiaBot-Utilities/master/useragents.txt"
    file = requests.get(url, timeout=10)
    open("data/agents.txt", 'wb').write(file.content)
    txt = open("data/agents.txt").read()
    return txt.split("\n")


def get_sentences():
    printf("Downloading sentences...")
    if not os.path.isdir('data'):
        os.makedirs("data")
    url = "https://raw.githubusercontent.com/Kugge/EcosiaBot-Utilities/master/questions.txt"
    file = requests.get(url, timeout=10)
    open("data/sentences.txt", 'wb').write(file.content)
    txt = open("data/sentences.txt").read()
    return txt.split("\n")


def get_proxy(collector, headers):
    p = collector.get_proxy()
    p_format = p.host + ":" + p.port
    try:
        requests.get("https://www.ecosia.org", proxies={"https": p_format}, timeout=10, headers=headers)
    except:
        return get_proxy(collector, headers)
    else:
        return p_format


def get_count(raw_txt):
    txt = raw_txt.split("\n")
    final = None
    for line in txt:
        if '<p class="tree-counter-text-mobile">' in line:
            final = line.replace('<p class="tree-counter-text-mobile">', '')
    if final == None:
        final = "0"
    return int(final)

    
class Bot(Thread):
    def __init__(self, uuid, agents, wordlist, sentences):
        Thread.__init__(self)
        
        self.query = "Loading..."
        self.proxy = "Loading..."
        
        self.agents = agents
        self.wordlist = wordlist
        self.sentences = sentences
        self.uuid = str(uuid)

        self.treec = 0
        self.searchc = 0
        
    def log(self, txt):
        uuid_format = "[Bot " + self.uuid + "] "
        printf(uuid_format + txt)

    def change_proxy(self):
        p = get_proxy(self.collector, self.gen_agent())
        self.proxy = p
        self.s.proxies = {"https": p}

    def gen_query(self):
        word = random.choice(self.wordlist)
        sentence = random.choice(self.sentences)
        return sentence.replace("$WORD", word)

    def gen_agent(self):
        return {"User-Agent": random.choice(self.agents)}

    def join(self):
        self.die = True
        super().join()

    def run(self):
        self.collector = proxyscrape.create_collector(self.uuid, 'https')
        self.s = requests.session()
        self.change_proxy()
        while True:
            query = self.gen_query()
            self.query = query
            try:
                r = self.s.get("https://www.ecosia.org/" + "search?q=" + query, headers=self.gen_agent(), timeout=10)
            except:
                self.change_proxy
            else:
                if "captcha" in r.text:
                    self.change_proxy()
                else:
                    self.searchc = get_count(r.text)
                    self.treec = self.searchc//45
                    rd = random.randint(25, 35)
                    
                    self.log("Search: " + str(self.searchc) + ", Trees: " + str(self.treec))
                    for _ in range(rd):
                       time.sleep(1)


class Manager(object):
    def __init__(self, threads, headers, wordlist, sentences):
        self.threads = threads
        self.headers = headers
        self.wordlist = wordlist
        self.sentences = sentences
        self.bots = []

    def gen_bots(self):
        printf("Generating bots...")
        for i in range(self.threads): 
            self.bots.append(Bot(i+1, self.headers, self.wordlist, self.sentences))

    def start_bots(self):
        printf("Starting bots...")
        for bot in self.bots:
            bot.start()


################################################## PYQT5
class GUI(QWidget):

    def __init__(self, agents, wordlist, sentences):
        super().__init__()
        self.agents = agents
        self.wordlist = wordlist
        self.sentences = sentences

        self.title = "EcosiaBot - By Kugge"
        self.left = 10
        self.top = 10
        self.width = 600
        self.height = 400

        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon('data/icon.png'))
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.getInteger()
        
        # Bots setup
        self.manager = Manager(self.lines, self.agents, self.wordlist, self.sentences)
        self.manager.gen_bots()
        self.manager.start_bots()
        
        # Done
        self.setTable()

        # Add box layout, add table to box layout and add box layout to widget
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table) 
        self.setLayout(self.layout) 
    
        # make QTimer
        self.qTimer = QTimer()
        self.qTimer.setInterval(1000) # ms
        self.qTimer.timeout.connect(self.updateTable)
        # start timer
        self.qTimer.start()

        # Show widget
        self.show()

        
    def setTable(self):
        self.table = QTableWidget()
        self.table.setRowCount(self.lines + 1)
        self.table.setColumnCount(5)
        header = self.table.horizontalHeader()       
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        totalsc = 0
        self.table.setHorizontalHeaderLabels(["Name", "Score", "Trees", "IP (Proxies)", "Query (Sentence)"])
        for i in range(self.lines):
            totalsc += self.manager.bots[i].searchc
            self.table.setItem(i+1,0, QTableWidgetItem("Bot " + str(i+1)))
            self.table.setItem(i+1,1, QTableWidgetItem(str(self.manager.bots[i].searchc)))
            self.table.setItem(i+1,2, QTableWidgetItem(str(self.manager.bots[i].treec)))
            self.table.setItem(i+1,3, QTableWidgetItem(str(self.manager.bots[i].proxy)))
            self.table.setItem(i+1,4, QTableWidgetItem(str(self.manager.bots[i].query)))
        self.table.setItem(0,0, QTableWidgetItem("Total"))
        self.table.setItem(0,1, QTableWidgetItem("Score: " + str(totalsc)))
        self.table.setItem(0,2, QTableWidgetItem("Trees: " + str(totalsc//45)))


    def updateTable(self):
        totalsc = 0
        for i in range(self.lines):
            totalsc += self.manager.bots[i].searchc
            self.table.item(i+1, 0).setText("Bot " + str(i+1))
            self.table.item(i+1, 1).setText(str(self.manager.bots[i].searchc))
            self.table.item(i+1, 2).setText(str(self.manager.bots[i].treec))
            self.table.item(i+1, 3).setText(str(self.manager.bots[i].proxy))
            self.table.item(i+1, 4).setText(str(self.manager.bots[i].query))
        self.table.item(0, 1).setText("Score: " + str(totalsc))
        self.table.item(0, 2).setText("Trees: " + str(totalsc//45))
        
    def getInteger(self):
        i, okPressed = QInputDialog.getInt(self, "EcosiaBot", "How many bots ?", 100, 1, 50000, 1)
        if okPressed:
            self.lines = i

############################################################################################################################

if __name__ == "__main__":
    print_banner()
    agents = get_agents()
    path = gen_icon()
    wordlist = get_wordlist()
    sentences = get_sentences()

    app = QApplication(sys.argv)
    ex = GUI(agents, wordlist, sentences)
    sys.exit(app.exec_())
