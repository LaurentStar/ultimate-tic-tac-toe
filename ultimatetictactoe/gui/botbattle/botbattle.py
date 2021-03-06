from ... import game
from ..qboards import QMacroBoard
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QObject
import datetime
import time


DEFAULT_TIME = 1


class MoveCalculation(QObject):
    calculated = pyqtSignal(int, int)
    terminated = pyqtSignal()

    def __init__(self, bot, board, minimumTime=DEFAULT_TIME):
        super(MoveCalculation, self).__init__()
        self.bot = bot
        self.board = board
        self.minimumTime = minimumTime

    def run(self):
        start = datetime.datetime.now()
        move = self.bot.choose_move(self.board)
        delta = datetime.datetime.now() - start
        timeLeft = self.minimumTime - delta.total_seconds()
        if timeLeft > 0:
            time.sleep(timeLeft)
        self.terminated.emit()
        self.calculated.emit(*move)


class BotBattle(QWidget):

    def __init__(self, bot1, bot2):
        super(BotBattle, self).__init__()
        self.bot1 = bot1
        self.bot2 = bot2
        self.score1 = 0
        self.score2 = 0
        self.draw = 0
        self.starting = self.bot1
        self.on_turn = self.bot1
        self.board = game.boards.Macroboard()
        self.qBoard = QMacroBoard(self.buttonClick)
        self.qBoard.setClickEnabled(False)
        self.qBoard.updateBoard(self.board)

        self.interrupted = False
        self.moveThread = None

        buttonLayout = self.createButton()
        self.title = self.createTitle()
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.qBoard)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

    def __del__(self):
        if self.moveThread:
            self.moveThread.wait()

    def botMove(self):
        self.moveThread = QThread()
        self.moveCalculation = MoveCalculation(self.on_turn, self.board)
        self.moveCalculation.calculated.connect(self.makeBotMove)
        self.moveCalculation.moveToThread(self.moveThread)
        self.moveThread.started.connect(self.moveCalculation.run)
        self.moveCalculation.terminated.connect(self.moveThread.quit)
        self.moveThread.start()

    def makeBotMove(self, px, py):
        self.board.make_move(px, py)
        self.qBoard.updateBoard(self.board)
        if self.board.state != game.boards.State.IN_PROGRESS:
            # update score
            if self.board.has_a_winner:
                if self.on_turn == self.bot1:
                    self.score1 += 1
                else:
                    self.score2 += 1
            else:
                self.draw += 1
            # change order
            self.starting = self.bot1 if self.starting == self.bot2\
                else self.bot2
            self.on_turn = self.starting
            self.updateTitle()
            self.startButton.show()
            return
        self.on_turn = self.bot1 if self.on_turn == self.bot2 else self.bot2
        if not self.interrupted:
            self.botMove()

    def createTitle(self):
        title = QLabel(self.bot1.name + ' vs ' + self.bot2.name)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        title.setFont(font)
        return title

    def updateTitle(self):
        title = (self.bot1.name + ': ' + str(self.score1) + ' vs ' +
                 self.bot2.name + ': ' + str(self.score2))
        if self.draw > 0:
            title += (' Draw: ' + str(self.draw))
        self.title.setText(title)

    def createButton(self):
        self.startButton = QPushButton('Start')
        self.startButton.clicked.connect(self.start)
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(self.startButton)
        layout.addStretch(1)
        return layout

    def start(self):
        self.startButton.hide()
        self.board = game.boards.Macroboard(self.bot1 == self.starting)
        self.qBoard.updateBoard(self.board)
        self.botMove()

    def interrupt(self):
        self.interrupted = True

    def buttonClick(self):
        return
