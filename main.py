import os
import time
import sys
import hashlib
from threading import Thread
from platform import uname

from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QDialog,\
                            QFileDialog
from PyQt5.QtCore import Qt

from UI.MirageMainWindow import Ui_MainWindow


def NewThread(com, Returning: bool, thread_ID, *arguments):
    """
    Will create a new thread for a function/command.
    :param com: Command to be Executed
    :param Returning: True/False Will the command return anything?
    :param thread_ID: Name of thread
    :param arguments: Arguments to be sent to Command
    """

    class NewThreadWorker(Thread):
        """
        New Thread Class
        """

        def __init__(self, group=None, target=None, name=None, args=(),
                     kwargs=None, *, daemon=None):
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

    ntw = NewThreadWorker(target=com, name=thread_ID, args=(*arguments,))
    if not Returning:
        ntw.start()
    else:
        ntw.start()
        return ntw.joinThread()


def test_Change_File():
    """
    Small test for Hash Compare
    """
    with open("./test", "+w") as f:
        f.write("Hello World!")
        f.close()


#  def test_loop():
    #  """
    #  Small Test loop for all main functions
    #  """
    #  while True:
        #  Scan_Files(Original_Hashes)
        #  test_Change_File()
        #  time.sleep(60)
        #  Scan_Files(New_Hashes)
        #  result = Hash_Compare()
        #  if result == 0:
            #  for i in range(len(Possible_Discrepancies)):
                #  print("\n\n\nList of Possible Discrepencies:")
                #  print(
                    #  f"\n\nFile: {list(Possible_Discrepancies.keys())[i]}\n"
                    #  f"Original Hash: "
                    #  f"{list(Possible_Discrepancies.values())[i][0]}\n"
                    #  f"New Hash: {list(Possible_Discrepancies.values())[i][1]}"
                #  )
            #  break


class MirageMainWindow(QMainWindow, Ui_MainWindow):
    """
    Manages Mirage's GUI
    """

    running = False
    BUF_SIZE = 65536
    # TODO: move this to a .csv file maybe...
    Original_Hashes = {}
    New_Hashes = {}
    Possible_Discrepancies = {}
    Path = ""

    def __init__(self, parent=None):
        super(MirageMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setFixedSize(800, 598)
        try:
            self.Path = sys.argv[1]
        except Exception:
            self.Path = "./"
        self.Mirage_Function_Assigns()

    def Scan_Files(self, dictionary):
        """
        Recursively traverse through the OS from the specified path
        and append found files/directories to specified dictionary along
        with the hash of the file.

        :param dictionary: the dictionary that will be appended with hashes
        """
        for root, d_names, f_names in os.walk(self.Path):
            print("OS Walk Result:")
            print(root, d_names, f_names)
            for f in f_names:
                sha256 = hashlib.sha256()
                print(f)
                try:
                    with open(os.path.join(root, f), 'rb') as file:
                        while True:
                            data = file.read(self.BUF_SIZE)
                            if not data:
                                break
                            sha256.update(data)
                except Exception as e:
                    print(
                        f"File '{f}' was found but could not be accessed "
                        f"because of the following exception: {e}"
                    )
                dictionary[os.path.join(root, f)] = sha256.hexdigest()
        print(dictionary)

    def Hash_Compare(self):
        """
        Compares the Hashes generated to determine possible discrepancies
        """
        Original_Hashes_Values = list(self.Original_Hashes.values())
        New_Hashes_Values = list(self.New_Hashes.values())
        New_Hashes_Keys = list(self.New_Hashes.keys())
        Original_Hashes_Keys = list(self.Original_Hashes.keys())
        if New_Hashes_Keys != Original_Hashes_Keys:
            # Need to be able to handle newly created files
            # here. could create some kinda of offset as to
            # where to compare from

            return 1
        for i in range(len(Original_Hashes_Values)):
            if Original_Hashes_Values[i] != New_Hashes_Values[i]:
                print(
                    "[File Changed] POSSIBLE DISCREPANCY FOUND:"
                    f"File {New_Hashes_Keys[i]}"
                )
                if New_Hashes_Keys[i] not in self.Possible_Discrepancies:
                    temp = [Original_Hashes_Values[i], New_Hashes_Values[i]]
                    self.Possible_Discrepancies[New_Hashes_Keys[i]] = temp
        return 0

    def Mirage_Function_Assigns(self):
        """
        Assign functions and actions to the different buttons and inputs
        """
        def Scan_Button_Action():
            if self.running is False:
                self.running = True
                self.ScanButton.setText("Stop Scan")
                self.ScanButton.setStyleSheet("Background: pink;"
                                              "Border: 1px solid black;"
                                              "Margin-left: 10px;"
                                              "Margin-right: 10px;")
            elif self.running is True:
                self.running = False
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

        self.ScanButton.clicked.connect(Scan_Button_Action)
        self.ScanLocationBrowse.clicked.connect(Folder_Selection)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    main = MirageMainWindow()
    main.show()
    sys.exit(app.exec_())
