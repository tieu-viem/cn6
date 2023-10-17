from subprocess import *;
from threading import *;
from time import *;
import os;
import random;
if os.name == 'nt':
    from subprocess import STARTUPINFO;
import json

class Move:
    NONE = 0;
    BLACK = 1;
    WHITE = 2;
    EDGE = 19;
    def __init__(self, color = NONE, x1 = -1, y1 = -1, x2 = -1, y2 = -1):
        self.color = color;
        self.x1 = x1;
        self.y1 = y1;
        self.x2 = x2;
        self.y2 = y2;

    def __str__(self):
        return 'color: {0}, x1: {1}, y1: {2}, x2: {3}, y2: {4}'.format(self.color, self.x1, self.y1, self.x2, self.y2);

    def fromCmd(cmd, color = None):
        # print(cmd);
        # print(self);
        cmd = cmd.strip();
        if cmd.startswith('move '):
            cmd = cmd[5:].upper();
            if len(cmd) == 2:
                cmd = cmd*2;
            m = Move(color);
            m.x1 = ord(cmd[0]) - ord('A');
            m.y1 = ord(cmd[1]) - ord('A');
            m.x2 = ord(cmd[2]) - ord('A');
            m.y2 = ord(cmd[3]) - ord('A');
            return m;
        
        return None;

    def toCmd(self):  
        cmd = 'move ' + self.cmd() + '\n';
        print('Cmd:', cmd);
        return cmd;

    def toPlaceCmd(self):
        if self.color == Move.BLACK:
            cmd = 'black ';
        elif self.color == Move.WHITE:
            cmd = 'white ';
        else:
            return 'None Place Cmd\n';
        cmd += self.cmd() + '\n';
        # print('Cmd:', cmd);
        return cmd;

    def cmd(self):
        base = ord('A');
        return chr(base + self.x1) + chr(base + self.y1) + chr(base + self.x2) + chr(base + self.y2);

    def invalidate(self):
        self.color= None;
        self.x1 = -1;
        self.y1 = -1;
        self.x2 = -1;
        self.y2 = -1;

    def isValidated(self):
        if self.color != Move.BLACK and self.color != Move.WHITE:
            return False;
        if Move.isValidPosition(self.x1, self.y1) and Move.isValidPosition(self.x2, self.y2):
            return True;

        return False;

    def isValidPosition(x, y):
        if x >= 0 and x < Move.EDGE and y >= 0 and y < Move.EDGE:
            return True;
        return False;

class GameEngine:
    def __init__(self):
        self.fileName = GameEngine.getDefaultEngineFile();
        self.proc = None;
        self.move = Move();
        self.color = Move.NONE;
        self.setName('Unknown');

    def getDefaultEngineFile():
        # Check the os, supported Linux/Mac/Windows.
        defaultEngineFile = '';
        if os.name == 'nt':
            defaultEngineFile = 'engines/cloudict.exe';
        else:
            osName = os.uname()[0];
            if osName == 'Darwin':
                defaultEngineFile = 'engines/cloudict.app';
            elif osName == 'Linux':
                defaultEngineFile = 'engines/cloudict.linux';
            else:
                print('Not supported OS');
                exit(-1);
        return defaultEngineFile;

    def init(self, fileName = None, depth = None, vcf = None):
        self.release();

        if fileName != None and fileName.strip() != '':
            self.fileName = fileName;
        else:
            fileName = self.fileName;
        #print('init:', self.fileName);
        if os.name == 'nt':
            # Windows NT hide
            startupinfo =  STARTUPINFO();
            startupinfo.dwFlags |= STARTF_USESHOWWINDOW;
            self.proc = Popen(fileName, stdin=PIPE, stdout=PIPE, bufsize=0, startupinfo=startupinfo);
        else:
            self.proc = Popen(fileName, stdin=PIPE, stdout=PIPE, bufsize=0);

        # game engine name
        self.setName(fileName);
        self.sendCmd('name\n');
        while True:
            msg = self.waitForNextMsg();
            if msg.startswith('name '):
                self.setName(msg.split(' ')[1]);
                break;

        if depth != None:
            cmd = 'depth ' + str(depth) + '\n';
            # print(cmd);
            self.sendCmd(cmd);
        if vcf != None:
            if vcf:
                cmd = 'vcf\n';
            else:
                cmd = 'unvcf\n';
            # print(cmd);
            self.sendCmd(cmd);
            
        self.move.invalidate();

        return True;

    def setName(self, name):
        self.name = self.shortName = name;
        if len(self.shortName) > 10 and self.shortName.find('.') > -1:
            ls = self.shortName.split('.');
            for i in ls:
                if i != '':
                    self.shortName = i;
                    break;
        if len(self.shortName) > 10:
            self.shortName = self.shortName[:8] + '...';

    def release(self):
        while self.proc != None:
            if self.proc.poll() == None:
                self.proc.terminate();
                # self.sendCmd('quit\n');
                # print('Release');
                sleep(0.2);
            else:
                self.proc = None;
                break;
        self.move.invalidate();

    def next(self, moveList = []):
        if self.proc != None:
            cmd = 'new xxx\n';
            self.sendCmd(cmd);
            for m in moveList:
                cmd = m.toPlaceCmd();
                self.sendCmd(cmd);

            cmd = 'next\n';
            self.sendCmd(cmd);

    def sendCmd(self, cmd):
        if self.proc != None:
            try:
                # print('sendCmd to stdin:', cmd);
                if len(cmd) < 1 or cmd[-1] != '\n':
                    # Add ret in the end;
                    cmd += '\n';
                self.proc.stdin.write(cmd.encode());
            except Exception as e:
                print('Error for sendCmd:', cmd, str(e));

    def waitForNextMsg(self):
        if self.proc != None:
            try:
                # print('Waiting');
                self.msg = self.proc.stdout.readline().decode();
                # print('out:', self.msg);
            except Exception as e:
                print('Error for waitForNextMsg:', str(e));
        return self.msg;

class GameState:

    Exit = -1;

    Idle = 0;
    AI2AI = 1;
    AI2Human = 2
    Human2Human = 3;

    WaitForEngine = 1;
    WaitForHumanFirst = 2;
    WaitForHumanSecond = 3;

    Win = 4;

class App(Frame):
    
        
    def __init__(self, master=None):
        Frame.__init__(self, master, width=640, height=700)
        self.pack();

        # Game state: -1 -> quit, 0 -> first, 1 -> second, 2 -> gameEngine 3;
        self.gameMode = GameState.Idle;
        self.gameState = GameState.Idle;

        self.current_player = Move.BLACK;
        self.next_player = Move.WHITE;

        self.currentPlayerColor = Move.BLACK  # Bắt đầu với màu đen.


        self.initResource();

        self.createBoard();
        
        self.initBoard();

    def destroy(self):
        self.gameState = GameState.Exit;
        self.gameEngine.release();
        self.searchThread.join();
        Frame.destroy(self);
    
    

    def initResource(self):

        # Images sets.
        self.images = {};
        im = self.images;
        im['go_u'] = PhotoImage(file='imgs/go_u.gif');
        im['go_ul'] = PhotoImage(file='imgs/go_ul.gif');
        im['go_ur'] = PhotoImage(file='imgs/go_ur.gif');
        im['go'] = PhotoImage(file='imgs/go.gif');
        im['go_l'] = PhotoImage(file='imgs/go_l.gif');
        im['go_r'] = PhotoImage(file='imgs/go_r.gif');
        im['go_d'] = PhotoImage(file='imgs/go_d.gif');
        im['go_dl'] = PhotoImage(file='imgs/go_dl.gif');
        im['go_dr'] = PhotoImage(file='imgs/go_dr.gif');
        im['go_-'] = PhotoImage(file='imgs/go_-.gif');
        im['go_b'] = PhotoImage(file='imgs/go_b.gif');
        im['go_w'] = PhotoImage(file='imgs/go_w.gif');
        im['go_bt'] = PhotoImage(file='imgs/go_bt.gif');
        im['go_wt'] = PhotoImage(file='imgs/go_wt.gif');

        im['angel'] = PhotoImage(file='imgs/logo.png');
        im['laugh'] = PhotoImage(file='imgs/logo.png');
        im['plain'] = PhotoImage(file='imgs/logo.png');
        im['raspberry'] = PhotoImage(file='imgs/logo.png');
        im['sad'] = PhotoImage(file='imgs/logo.png');
        im['smile'] = PhotoImage(file='imgs/logo.png');
        im['smile-big'] = PhotoImage(file='imgs/logo.png');
        im['surprise'] = PhotoImage(file='imgs/logo.png');
        im['uncertain'] = PhotoImage(file='imgs/logo.png');
        im['wink'] = PhotoImage(file='imgs/logo.png');

        self.faces = {};
        waiting = [im['angel'], im['raspberry'], im['smile'], im['wink']];
        self.faces[GameState.Idle] = waiting;
        self.faces[GameState.WaitForHumanFirst] = waiting;
        self.faces[GameState.WaitForHumanSecond] = waiting;
        waitingSad = [im['plain'], im['sad'], im['surprise'], im['uncertain'] ];
        self.faces['LowScore'] = waitingSad;
        searching = [im['plain'], im['surprise'], im['uncertain'] ];
        self.faces[GameState.WaitForEngine] = searching;
        won = [im['angel'], im['laugh'], im['raspberry'], im['smile'], im['smile-big'], im['wink'] ];
        self.faces['win'] = won;
        lost = [im['plain'], im['sad'], im['surprise'], im['uncertain'], ];
        self.faces['lose'] = lost;

        # Các Game Engines
        self.gameEngine = GameEngine()
        self.searchThread = Thread(target=self.searching)
        self.searchThread.start()
        # Game engines
        self.gameEngine = GameEngine();
        self.searchThread = Thread(target = self.searching);
        self.searchThread.start();

        # Widgets
        self.canvas = Canvas(self, width=640, height=640)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=1)

        # Các nút điều khiển
        self.controlFrame = LabelFrame(self)
        self.controlFrame.pack(fill=BOTH, expand=1)

        # Chế độ AI
        self.controlFrame.aiLevel = labelframe = LabelFrame(self.controlFrame, text='Cấp độ AI')
        labelframe.pack(fill=X, expand=1)
        self.aiLevel = IntVar()
        labelframe.lowRBtn = Radiobutton(labelframe, text="Thấp", variable=self.aiLevel, value=4)
        labelframe.lowRBtn.select()
        labelframe.lowRBtn.pack(anchor=W)
        labelframe.mediumRBtn = Radiobutton(labelframe, text="Trung bình", variable=self.aiLevel, value=5)
        labelframe.mediumRBtn.pack(anchor=W)
        labelframe.highRBtn = Radiobutton(labelframe, text="Cao", variable=self.aiLevel, value=6)
        labelframe.highRBtn.pack(anchor=W)
        self.vcf = IntVar()
        chbox = Checkbutton(labelframe, text="Với VCF", variable=self.vcf)
        chbox.select()
        chbox.pack(anchor=W)

        # Ngôn ngữ
        self.controlFrame.language = labelframe = LabelFrame(self.controlFrame, text='Ngôn ngữ')
        labelframe.pack(fill=X, expand=1)
        self.language = IntVar()
        labelframe.lowRBtn = Radiobutton(labelframe, text="Tiếng Việt", variable=self.language, value=4)
        labelframe.lowRBtn.select()
        labelframe.lowRBtn.pack(anchor=W)
        labelframe.mediumRBtn = Radiobutton(labelframe, text="Tiếng Anh", variable=self.language, value=5)
        labelframe.mediumRBtn.pack(anchor=W)
        labelframe.highRBtn = Radiobutton(labelframe, text="Tiếng Trung", variable=self.language, value=6)
        labelframe.highRBtn.pack(anchor=W)

        self.language.trace("w", lambda *args: self.update_language())

        # Lựa chọn Người chơi Đen
        self.controlFrame.selectBlack = labelframe = LabelFrame(self.controlFrame, text='Người chơi 1')
        labelframe.pack(fill=X, expand=1)
        labelframe.blackImg = Label(labelframe, image=self.images['go_b'])
        labelframe.blackImg.pack(side=LEFT, anchor=W)
        self.blackSelected = StringVar()
        labelframe.humanRBtn = Radiobutton(labelframe, text="Người", variable=self.blackSelected, value=' ')
        labelframe.humanRBtn.select()
        labelframe.humanRBtn.pack(anchor=W)
        labelframe.engineRBtn = Radiobutton(labelframe, text="AI", variable=self.blackSelected, value='engine')
        labelframe.engineRBtn.pack(anchor=W)

        # Lựa chọn Người chơi Trắng
        self.controlFrame.selectWhite = labelframe = LabelFrame(self.controlFrame, text='Người chơi 2')
        labelframe.pack(fill=X, expand=1)
        labelframe.whiteImg = Label(labelframe, image=self.images['go_w'])
        labelframe.whiteImg.pack(side=LEFT, anchor=W)
        self.whiteSelected = StringVar()
        labelframe.humanRBtn = Radiobutton(labelframe, text="Người", variable=self.whiteSelected, value=' ')
        labelframe.humanRBtn.select()
        labelframe.humanRBtn.pack(anchor=W)
        labelframe.engineRBtn = Radiobutton(labelframe, text="AI", variable=self.whiteSelected, value='engine')
        labelframe.engineRBtn.pack(anchor=W)

        # Điều khiển trò chơi
        self.controlFrame.gameContral = labelframe = LabelFrame(self.controlFrame, text='Điều khiển Trò chơi')
        labelframe.pack(fill=X, expand=1)
        labelframe.newBtn = Button(labelframe, text='Bắt đầu Trò chơi', command=self.newGame)
        labelframe.newBtn.pack(side=TOP, fill=X)
        labelframe.pauseBtn = Button(labelframe, text='Tạm dừng', command=self.pauseGame)
        labelframe.pauseBtn.pack(fill=X) 
        labelframe.backBtn = Button(labelframe, text='Quay Lại', command=self.backMove)
        labelframe.backBtn.pack(fill=X)
        labelframe.loadBtn = Button(labelframe, text='Tải Game Engine', command=self.loadGameEngine)
        labelframe.loadBtn.pack(fill=BOTH)
        labelframe.quitBtn = Button(labelframe, text='Thoát Trò chơi', command=self.master.destroy)
        labelframe.quitBtn.pack(fill=X)

        # Trạng thái AI
        self.controlFrame.aiStatus = labelframe = LabelFrame(self.controlFrame, text='Trạng thái AI')
        labelframe.pack(side=BOTTOM, fill=BOTH, expand="yes")
        labelframe.name = Label(labelframe, text='Tên AI')
        labelframe.name.pack(side=TOP, anchor=W)
        labelframe.image = Label(labelframe, image=self.images['smile'])
        labelframe.image.pack(side=TOP, anchor=W)
        labelframe.info = Label(labelframe, text='')
        labelframe.info.pack(side=BOTTOM, anchor=W)

        #self.initGameEngine();

        self.updateStatus();
    
    def pauseGame(self):
        messagebox.showinfo("Tạm dừng", "Trò chơi đã được tạm dừng.")

    
    def update_language(self):
        selected_language = self.language.get()  # Lấy giá trị của ngôn ngữ được chọn

        # Dictionary chứa các dữ liệu ngôn ngữ tương ứng
        language_data = {
            5: {
                'ai_level_text': 'AI Level',
                'low_text': 'Low',
                'medium_text': 'Medium',
                'high_text': 'High',
                'vcf_text': 'With VCF',
                'player1_text': 'Player 1',
                'player2_text': 'Player 2',
                'start_game_text': 'Start Game',
                'back_text': 'Back',
                'load_text': 'Load Game Engine',
                'exit_text': 'Exit Game',
                'ai_status_text': 'AI Status',
                'ai_name_text': 'AI Name',
                'language': 'Language',
                'gameContral': 'Game controls',
                'pauseBtn': 'Pause',
                'humanRBtn': 'Human',
                'engineRBtn': 'AI'
            },
            4: {
                'ai_level_text': 'Cấp độ AI',
                'low_text': 'Thấp',
                'medium_text': 'Trung bình',
                'high_text': 'Cao',
                'vcf_text': 'Với VCF',
                'player1_text': 'Người chơi 1',
                'player2_text': 'Người chơi 2',
                'start_game_text': 'Bắt đầu Trò chơi',
                'back_text': 'Quay Lại',
                'load_text': 'Tải Game Engine',
                'exit_text': 'Thoát Trò chơi',
                'ai_status_text': 'Trạng thái AI',
                'ai_name_text': 'Tên AI',
                'language': 'Ngôn ngữ',
                'gameContral': 'Điều khiển trò chơi',
                'pauseBtn': 'Tạm dừng',
                'humanRBtn': 'Người',
                'engineRBtn': 'AI'
            },
            6: {
                'ai_level_text': 'AI级别',
                'low_text': '低',
                'medium_text': '中等',
                'high_text': '高',
                'vcf_text': '使用VCF',
                'player1_text': '玩家1',
                'player2_text': '玩家2',
                'start_game_text': '开始游戏',
                'back_text': '返回',
                'load_text': '加载游戏引擎',
                'exit_text': '退出游戏',
                'ai_status_text': 'AI状态',
                'ai_name_text': 'AI名称',
                'language': '语言',
                'gameContral': '游戏控制',
                'pauseBtn': '暂停',
                'humanRBtn': '人类',
                'engineRBtn': '人工智能'

            },
        }

        # Cập nhật văn bản cho các widget
        self.controlFrame.aiLevel['text'] = language_data[selected_language]['ai_level_text']
        self.controlFrame.aiLevel.lowRBtn['text'] = language_data[selected_language]['low_text']
        self.controlFrame.aiLevel.mediumRBtn['text'] = language_data[selected_language]['medium_text']
        self.controlFrame.aiLevel.highRBtn['text'] = language_data[selected_language]['high_text']
        self.controlFrame.language['text'] = language_data[selected_language]['language']
        # self.controlFrame.aiLevel.vcf['text'] = language_data[selected_language]['vcf_text']
        self.controlFrame.selectBlack['text'] = language_data[selected_language]['player1_text']
        self.controlFrame.selectBlack.humanRBtn['text'] = language_data[selected_language]['humanRBtn']
        self.controlFrame.selectBlack.engineRBtn['text'] = language_data[selected_language]['engineRBtn']
        self.controlFrame.selectWhite['text'] = language_data[selected_language]['player2_text']
        self.controlFrame.selectWhite.humanRBtn['text'] = language_data[selected_language]['humanRBtn']
        self.controlFrame.selectWhite.engineRBtn['text'] = language_data[selected_language]['engineRBtn']
        self.controlFrame.gameContral['text'] = language_data[selected_language]['gameContral']
        self.controlFrame.gameContral.newBtn['text'] = language_data[selected_language]['start_game_text']
        self.controlFrame.gameContral.backBtn['text'] = language_data[selected_language]['back_text']
        self.controlFrame.gameContral.loadBtn['text'] = language_data[selected_language]['load_text']
        self.controlFrame.gameContral.quitBtn['text'] = language_data[selected_language]['exit_text']
        self.controlFrame.aiStatus['text'] = language_data[selected_language]['ai_status_text']
        self.controlFrame.aiStatus.name['text'] = language_data[selected_language]['ai_name_text']
        self.controlFrame.gameContral.pauseBtn['text'] = language_data[selected_language]['pauseBtn']

    def isVcf(self):
        vcf = True;
        if self.vcf.get() < 1:
            vcf = False;
        # print('VCF', vcf);
        return vcf;

    def loadGameEngine(self):
        fileName = filedialog.askopenfilename(title='Load executable file for new game engine ', initialdir='engines');
        print('Load game engine:', fileName);
        if len(fileName) > 0:
            try:
                self.initGameEngine(fileName);
            except Exception as e:
                messagebox.showinfo("Error","Error to load the engine: " + fileName + ",\n errors: " + str(e));

    def initGameEngine(self, fileName=''):
        self.gameEngine.init(fileName, self.aiLevel.get(), self.isVcf());
        # Change the engine name
        shortName = self.gameEngine.shortName.capitalize();
        self.controlFrame.aiLevel['text'] = shortName + ' AI Level';
        self.controlFrame.selectBlack.engineRBtn['text'] = shortName;
        self.controlFrame.selectWhite.engineRBtn['text'] = shortName;
        name = self.gameEngine.name.capitalize();
        self.controlFrame.aiStatus.name['text'] = name;
        #root.title('Cloudict.Connect6 - ' + name);

    def createBoardUnit(self, x, y, imageKey):
        lb = Label(self.canvas, height=32, width=32);
        lb.x = x;
        lb.y = y;
        lb['image'] = self.images[imageKey];
        lb.initImage = self.images[imageKey];
        lb.bind('<Button-1>', self.onClickBoard);
        self.gameBoard[x][y] = lb;

        return lb;

    def createBoard(self):
        self.gameBoard = [ [ 0 for i in range(Move.EDGE) ] for i in range(Move.EDGE)];
        self.moveList = [];
        images = self.images;
        gameBoard = self.gameBoard;
        canvas = self.canvas;
        # Upper
        self.createBoardUnit(0, 0, 'go_ul');
        for j in range(1, 18):
            self.createBoardUnit(0, j, 'go_u');
        self.createBoardUnit(0, 18, 'go_ur');

        # Middle
        for i in range(1,18):
            gameBoard[i][0] = self.createBoardUnit(i, 0, 'go_l');
            for j in range(1,18):
                gameBoard[i][j] = self.createBoardUnit(i, j, 'go');

            gameBoard[i][18] = self.createBoardUnit(i, 18, 'go_r');

        # Block point in the board
        self.createBoardUnit(3, 3, 'go_-');
        self.createBoardUnit(3, 9, 'go_-');
        self.createBoardUnit(3, 15, 'go_-');
        self.createBoardUnit(9, 3, 'go_-');
        self.createBoardUnit(9, 9, 'go_-');
        self.createBoardUnit(9, 15, 'go_-');
        self.createBoardUnit(15, 3, 'go_-');
        self.createBoardUnit(15, 9, 'go_-');
        self.createBoardUnit(15, 15, 'go_-');

        # Down
        self.createBoardUnit(18, 0, 'go_dl');
        for j in range(1,18):
            self.createBoardUnit(18, j, 'go_d');
        self.createBoardUnit(18, 18, 'go_dr');

    def backMove(self):
        if self.gameMode == GameState.AI2Human or self.gameMode == GameState.Human2Human:
            if self.gameState == GameState.WaitForHumanFirst:
                if self.gameMode == GameState.AI2Human and len(self.moveList) > 1:
                    # Back to 2 Move
                    self.unmakeTopMove();
                    self.unmakeTopMove();
                elif self.gameMode == GameState.Human2Human and len(self.moveList) > 0:
                    # Back to 1 Move
                    self.unmakeTopMove();
            elif self.gameState == GameState.WaitForHumanSecond:
                self.unplaceColor(self.move.x1, self.move.y1);
                self.toGameState(GameState.WaitForHumanFirst);

    def initBoard(self):
        self.moveList = [];
        for i in range(Move.EDGE):
            for j in range(Move.EDGE):
                self.unplaceColor(i, j);

    def unplaceColor(self, i, j):
        gameBoard = self.gameBoard;
        gameBoard[i][j]['image'] = gameBoard[i][j].initImage;
        gameBoard[i][j].color = 0;
        gameBoard[i][j].grid(row=i, column=j);

    def connectedByDirection(self, x, y, dx, dy):
        gameBoard = self.gameBoard;
        cnt = 1;
        xx = dx; yy = dy;
        while Move.isValidPosition(x+xx, y+yy) and gameBoard[x][y].color == gameBoard[x+xx][y+yy].color:
            xx += dx; yy += dy;
            cnt += 1;
        xx = -dx; yy = -dy;
        while Move.isValidPosition(x+xx, y+yy) and gameBoard[x][y].color == gameBoard[x+xx][y+yy].color:
            xx -= dx; yy -= dy;
            cnt += 1;
        if cnt >= 6:
            return True;
        return False;
        
    def connectedBy(self, x, y):
        # Four direction
        if self.connectedByDirection(x, y, 1, 1):
            return True;
        if self.connectedByDirection(x, y, 1, -1):
            return True;
        if self.connectedByDirection(x, y, 1, 0):
            return True;
        if self.connectedByDirection(x, y, 0, 1):
            return True;
        return False;

    def isWin(self, move):
        if move.isValidated():
            return self.connectedBy(move.x1, move.y1) or self.connectedBy(move.x2, move.y2);
        return False;

    def updateCurrentPlayerColor(self):
        if self.currentPlayerColor == Move.BLACK:
            self.currentPlayerColor = Move.WHITE
        else:
            self.currentPlayerColor = Move.BLACK

    def nextColor(self):
        return self.currentPlayerColor


    def waitForMove(self):
        color = self.nextColor();
        while True:
            # print('waitForMove');
            msg = self.gameEngine.waitForNextMsg();
            # print('Msg:', msg);
            move = Move.fromCmd(msg, color);
            # print('Wait move:', move);
            self.updateStatus();
            if move != None:
                break;
            
        return move

    def searching(self):
        while True:
            try:
                if self.gameState == GameState.Exit:
                    break;
                if self.gameMode == GameState.AI2AI or self.gameMode == GameState.AI2Human:
                    if self.gameState == GameState.WaitForEngine:
                        self.gameEngine.next(self.moveList);
                        move = self.waitForMove();
                        self.gameEngine.color = move.color;
                        self.makeMove(move);
                        if self.gameState == GameState.WaitForEngine and self.gameMode == GameState.AI2Human:
                            self.toGameState(GameState.WaitForHumanFirst);
                    else:
                        sleep(0.1);
                else:
                    sleep(0.2);
            except Exception as e:
                print('Exception when searching: ' + str(e));
                sleep(0.5);

    def updateStatus(self):
        image = random.sample(self.faces.get(GameState.Idle), 1)[0];
        ls = self.faces.get(self.gameState);
        # According to gameState.
        if ls != None and len(ls) > 0:
            image = random.sample(ls, 1)[0];
            
        self.controlFrame.aiStatus.image['image'] = image;
        self.controlFrame.aiStatus.info['text'] = '';

        msg = 'Nhấn bắt đầu để chơi.';
        if self.gameState == GameState.Win:
            if self.winner == self.gameEngine.color:
                msg = 'Tôi thắng!';
            else:
                msg = 'Tôi thua!';
        elif self.gameState == GameState.WaitForHumanFirst:
            msg = 'Di chuyển lần đầu tiên...';
        elif self.gameState == GameState.WaitForHumanSecond:
            msg = 'Di chuyển lần thứ hai...';
        elif self.gameState == GameState.WaitForEngine:
            msg = 'Đang suy nghĩ.';
            # Check format: Searching 31/37

            if self.gameEngine.msg.startswith('Searching '):
                s = self.gameEngine.msg.split(' ')[1];
                ls = s.split('/');
                cnt = float(ls[0])/float(ls[1]) * 15;
                msg += '.' * int(cnt);
        self.controlFrame.aiStatus.info['text'] = msg;

            
    def otherColor(self, color):
        if color == Move.BLACK:
            return Move.WHITE;
        elif color == Move.WHITE:
            return Move.BLACK;
        return Move.NONE;

    def newGame(self):
        self.gameEngine.release();
        self.initBoard();
        black = self.blackSelected.get().strip();
        white = self.whiteSelected.get().strip();
        if black == '' and white == '':
            self.toGameMode(GameState.Human2Human);
            self.toGameState(GameState.WaitForHumanFirst);
        elif black != '' and white != '':
            self.toGameMode(GameState.AI2AI);
            self.initGameEngine();
            self.toGameState(GameState.WaitForEngine);
        else:
            self.initGameEngine();
            self.toGameMode(GameState.AI2Human);
            if black != '':
                self.toGameState(GameState.WaitForEngine);
            else:
                self.toGameState(GameState.WaitForHumanFirst);

    def addToMoveList(self, move):
        # Rerender pre move
        n = len(self.moveList);
        if n > 0:
            m = self.moveList[n-1];
            self.placeColor(m.color, m.x1, m.y1);
            self.placeColor(m.color, m.x2, m.y2);
            
        self.moveList.append(move);

    def unmakeTopMove(self):
        if len(self.moveList) > 0:
            m = self.moveList[-1];
            self.moveList = self.moveList[:-1];
            self.unplaceColor(m.x1, m.y1);
            self.unplaceColor(m.x2, m.y2);
            if len(self.moveList) > 0:
                m = self.moveList[-1];
                self.placeColor(m.color, m.x1, m.y1, 't');
                self.placeColor(m.color, m.x2, m.y2, 't');

    def makeMove(self, move):
        if move.isValidated():
            self.placeStone(move.color, move.x1, move.y1);
            self.placeStone(move.color, move.x2, move.y2);
            self.addToMoveList(move);
            # print('Made move:', move);
        return move;

    def placeStone(self, color, x, y):
        self.placeColor(color, x, y, 't');
        if self.connectedBy(x, y):
            self.winner = color;
            self.toGameState(GameState.Win);
            if color == Move.BLACK:
                messagebox.showinfo("Black Win", "Black Win;) Impressive!")
            else:
                messagebox.showinfo("White Win", "White Win;) Impressive!")

    def placeColor(self, color, x, y, extra = ''):
        if color == Move.BLACK:
            imageKey = 'go_b';
        elif color == Move.WHITE:
            imageKey = 'go_w';
        else:
            return ;
        imageKey += extra;
        self.gameBoard[x][y].color = color;
        self.gameBoard[x][y]['image'] = self.images[imageKey];
        self.gameBoard[x][y].grid(row=x, column=y);

    def isNoneStone(self, x, y):
        return self.gameBoard[x][y].color == Move.NONE;

    def toGameMode(self, mode):
        self.gameMode = mode;

    def toGameState(self, state):
        self.gameState = state;
        self.updateStatus();

    def onClickBoard(self, event):
        x = event.widget.x
        y = event.widget.y

        if not self.isNoneStone(x, y):
            return

        color = self.nextColor()

        if len(self.moveList) == 0:
            # First Move for Black
            self.updateCurrentPlayerColor()
            self.move = Move(color, x, y, x, y)

            self.addToMoveList(self.move)
            self.placeStone(self.move.color, x, y)
            self.toGameState(GameState.WaitForHumanFirst)
        elif self.gameState == GameState.WaitForHumanFirst:
            self.updateCurrentPlayerColor()
            self.move = Move(color, x, y)

            self.placeStone(self.move.color, x, y)
            self.toGameState(GameState.WaitForHumanSecond)
        elif self.gameState == GameState.WaitForHumanSecond:
            self.updateCurrentPlayerColor()
            self.move = Move(color, x, y)
            self.placeStone(self.move.color, x, y)
            self.addToMoveList(self.move)
            self.toGameState(GameState.WaitForHumanFirst)

        if self.gameMode == GameState.AI2Human:
            if len(self.moveList) == 0 and self.gameState == GameState.WaitForHumanFirst:
                # First Move for Black
                self.move = Move(color, x, y, x, y)
                self.addToMoveList(self.move)
                self.placeStone(self.move.color, x, y)
                self.toGameState(GameState.WaitForEngine)
            elif self.gameState == GameState.WaitForHumanFirst:
                self.move = Move(color, x, y)
                self.placeStone(self.move.color, x, y)
                self.toGameState(GameState.WaitForHumanSecond)
            elif self.gameState == GameState.WaitForHumanSecond:
                self.move.x2 = x
                self.move.y2 = y
                self.placeStone(self.move.color, x, y)
                self.addToMoveList(self.move)
                self.toGameState(GameState.WaitForEngine)

def main():

    root = Tk();

    # create the application
    app = App(root)

    #
    # here are method calls to the window manager class
    #
    app.master.title('Connect6')
    # app.master.maxsize(840, 840)

    # start the program
    app.mainloop()

    # root.destroy();

if __name__ == '__main__':
    main();