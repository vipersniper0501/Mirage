import os
import time
import sys
import hashlib
from threading import Thread
from platform import uname

from PyQt5.QtWidgets import QMainWindow, QApplication,\
                            QFileDialog
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal

from UI.MirageMainWindow import Ui_MainWindow

threads = []


def NewThread(com, Returning: bool, thread_ID: str, *arguments):

    """
    Will create a new thread for a function/command.
    This Function requires a global list called threads for easy managemnet of
    Threads
    :param com: Command to be Executed
    :param Returning: True/False Will the command return anything?
    :param thread_ID: Name of thread
    :param arguments: Arguments to be sent to Command
    """

    class NewThreadWorker(Thread):

        """
        New Thread Class
        """

        def __init__(self, group=None, target=None, name=None,
                     args=(), kwargs=None, *, daemon=None):
            Thread.__init__(self, group, target, name, args, kwargs,
                            daemon=daemon)
            self.daemon = True
            self._return = None

        def run(self):
            if self._target is not None:
                self._return = self._target(*self._args, **self._kwargs)

        def joinThread(self):
            """
            Joins the threads, allowing a return value
            """
            Thread.join(self)
            return self._return

    threads.append(NewThreadWorker(target=com,
                                   name=thread_ID,
                                   args=(*arguments,)))
    if not Returning:
        print(threads)
        threads[-1].start()
        print(threads)
    else:
        threads[-1].start()
        return threads[-1].joinThread()


def test_Change_File():

    """
    Small test for Hash Compare
    """
    with open("./test", "w+") as f:
        f.write("Hello World!")
        f.close()


class MirageMainWindow(QMainWindow, Ui_MainWindow):

    """
    Manages Mirage's GUI
    """

    running = False
    BUF_SIZE = 65536
    Original_Hashes = {}
    New_Hashes = {}
    Possible_Discrepancies = {}
    Path = ""
    updateSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(MirageMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setFixedSize(800, 598)
        try:
            self.Path = sys.argv[1]
        except IndexError:
            self.Path = "./"
        self.Mirage_Function_Assigns()

    def Scan_Files(self, dictionary):

        """
        Recursively traverse through the OS from the specified path
        and append found files/directories to specified dictionary along
        with the hash of the file.

        :param dictionary: the dictionary that will be appended with hashes
        """

        # TODO: replace os.walk with os.scandir for faster performance.
        for root, d_names, f_names in os.walk(self.Path):
            if self.running is False:
                return 1
            self.updateSignal.emit("\nOS Walk Result:")
            self.updateSignal.emit("\n"
                                   + str(root)
                                   + str(d_names)
                                   + str(f_names))
            for f in f_names:
                sha1 = hashlib.sha1()
                self.updateSignal.emit(str(f))
                try:
                    with open(os.path.join(root, f), 'rb') as file:
                        while True:
                            data = file.read(self.BUF_SIZE)
                            if not data:
                                break
                            sha1.update(data)
                except Exception as e:
                    self.updateSignal.emit(
                        f"File '{f}' could not be accessed "
                        f"because of the following exception: {e}"
                    )
                dictionary[os.path.join(root, f)] = sha1.hexdigest()
        self.updateSignal.emit(str(dictionary))

    def Hash_Compare(self):

        """
        Compares the Hashes generated to determine possible discrepancies
        """

        # TODO: replace most of this with os.filecmp()
        Original_Hashes_Values = list(self.Original_Hashes.values())
        New_Hashes_Values = list(self.New_Hashes.values())
        New_Hashes_Keys = list(self.New_Hashes.keys())
        Original_Hashes_Keys = list(self.Original_Hashes.keys())
        if len(New_Hashes_Keys) != len(Original_Hashes_Keys):
            # Need to be able to handle newly created files
            # here. could create some kinda of offset as to
            # where to compare from
            print("New file was added")
        for x, i in enumerate(Original_Hashes_Values):
            if self.running is False:
                return 1
            if i != New_Hashes_Values[x]:
                print(
                    "[File Changed] POSSIBLE DISCREPANCY FOUND:"
                    f"File {New_Hashes_Keys[x]}"
                )
                if New_Hashes_Keys[x] not in self.Possible_Discrepancies:
                    temp = [i, New_Hashes_Values[x]]
                    self.Possible_Discrepancies[New_Hashes_Keys[x]] = temp
        return 0

    def Scan_Loop(self):

        """
        The loop that scans the os looking for possible discrepancies
        """

        while self.running is True:
            print(self.Path)
            if self.Scan_Files(self.Original_Hashes) == 1:
                break
            time.sleep(10)
            if self.Scan_Files(self.New_Hashes) == 1:
                break
            result = self.Hash_Compare()
            if result == 0:
                print(self.Possible_Discrepancies)
            elif result == 1:
                break

    @pyqtSlot(str)
    def Log_Update(self, data):

        """
        Updates UI log output
        """

        print("updating log")
        print(data)
        self.LogOutput.setText(self.LogOutput.toPlainText() + data)
        self.LogOutput.verticalScrollBar().setValue(
            self.LogOutput.verticalScrollBar().maximum())

    def Mirage_Function_Assigns(self):

        """
        Assign functions and actions to the different buttons and inputs
        """

        def Scan_Button_Action():
            global threads
            if self.running is False:
                thread_names = []
                for t in threads:
                    if t.is_alive():
                        thread_names.append(t.getName())
                        print(thread_names)
                    else:
                        print("Thread is still alive!")
                if "Scanning System" not in thread_names:
                    self.running = True
                    print(threads)
                    print("\n\n\n")
                    self.ScanButton.setText("Stop Scan")
                    self.ScanButton.setStyleSheet("Background: pink;"
                                                  "Border: 1px solid black;"
                                                  "Margin-left: 10px;"
                                                  "Margin-right: 10px;")
                    NewThread(self.Scan_Loop, False, "Scanning System")
            elif self.running is True:
                self.running = False
                thread_names = []
                for t in threads:
                    if t.is_alive():
                        thread_names.append(t.getName())
                        print(thread_names)
                    else:
                        print("Thread is still alive!")
                if "Scanning System" in thread_names:
                    self.ScanButton.setText("Begin Scan")
                    self.ScanButton.setStyleSheet("Background: lightgreen;"
                                                  "Border: 1px solid black;"
                                                  "Margin-left: 10px;"
                                                  "Margin-right: 10px;")

        def Folder_Selection():
            dialog = str(QFileDialog.getExistingDirectory(self,
                                                          "Select Directory"))
            self.ScanLocationInput.setPlainText(dialog)
            self.Path = dialog

        def Folder_Input_Text():
            self.Path = self.ScanLocationInput.toPlainText()

        self.updateSignal.connect(self.Log_Update)
        self.ScanButton.clicked.connect(Scan_Button_Action)
        self.ScanLocationBrowse.clicked.connect(Folder_Selection)
        self.ScanLocationInput.textChanged.connect(Folder_Input_Text)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    main = MirageMainWindow()
    main.show()
    sys.exit(app.exec_())
