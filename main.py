import os
import time
import sys
import hashlib
from threading import Thread

from PyQt5.QtWidgets import QMainWindow, QApplication,\
                            QFileDialog
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal

from UI.MirageMainWindow import Ui_MainWindow

threads = []


def NewThread(com, Returning: bool, managed: bool, thread_ID: str, *arguments):

    """
    Will create a new thread for a function/command.
    This Function requires a global list called threads for easy managemnet of
    Threads
    :param com: Command to be Executed
    :param Returning: True/False Will the command return anything?
    :param managed: Will the thread object be added to a global list called
                    'threads' for later use.
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

    if managed:
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
    elif not managed:
        ntw = NewThreadWorker(target=com,
                              name=thread_ID,
                              args=(*arguments,))
        if not Returning:
            ntw.start()
        else:
            ntw.start()
            return ntw.joinThread()


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
    discrepancy_Signal = pyqtSignal()
    wait_time = 30

    def __init__(self, parent=None):
        super(MirageMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setFixedSize(1078, 598)
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

        # Could possibly be updated to instead of using hashes for detecting
        # updated files, you could just use the os.stat module to get the last
        # modified date and compare them. Would most likely have a much larger
        # performance boost.

        def Generate_Hash(root, f):
            sha1 = hashlib.sha1()
            self.updateSignal.emit(str(f))
            try:
                with open(os.path.join(root, f), 'rb') as file:
                    while True:
                        data = file.read(self.BUF_SIZE)
                        if not data:
                            break
                        sha1.update(data)
            except FileNotFoundError:
                self.updateSignal.emit(
                    f"File '{f}' could not be accessed."
                )
            dictionary[os.path.join(root, f)] = sha1.hexdigest()

        for root, d_names, f_names in os.walk(self.Path):
            print("Current Directory: " + str(root))
            if self.running is False:
                return 1
            self.updateSignal.emit("\n"
                                   + str(root)
                                   + str(d_names)
                                   + str(f_names))
            for f in f_names:
                NewThread(Generate_Hash, False, True, str(f), root, f)
            for t in threads:
                if t.getName() != "Scanning System":
                    t.join()
                    threads.remove(t)
            print(f"Directory {str(root)} is completed")
        print(threads)
        self.updateSignal.emit("\n"+str(dictionary))
        for t in threads:
            if t.getName() != "Scanning System":
                t.join()
                threads.remove(t)

    def Hash_Compare(self):

        """
        Compares the Hashes generated to determine possible discrepancies
        """

        Original_Hashes_Values = list(self.Original_Hashes.values())
        New_Hashes_Values = list(self.New_Hashes.values())
        New_Hashes_Keys = list(self.New_Hashes.keys())
        Original_Hashes_Keys = list(self.Original_Hashes.keys())
        for x, hashes in enumerate(New_Hashes_Values):
            if self.running is False:
                return 1
            if len(New_Hashes_Keys) > len(Original_Hashes_Keys):
                if New_Hashes_Keys[x] not in Original_Hashes_Keys:
                    if New_Hashes_Keys[x] not in self.Possible_Discrepancies:
                        self.Possible_Discrepancies[
                            New_Hashes_Keys[x]
                        ] = 1
                        self.discrepancy_Signal.emit()
                print("New file was added")
            if len(New_Hashes_Keys) < len(Original_Hashes_Keys):
                if Original_Hashes_Keys[x] not in New_Hashes_Keys:
                    if Original_Hashes_Keys[x] not in self.Possible_Discrepancies:
                        self.Possible_Discrepancies[
                            Original_Hashes_Keys[x]
                        ] = 2
                        self.discrepancy_Signal.emit()
                    print("File was removed")
            if hashes not in Original_Hashes_Values and \
                    New_Hashes_Keys[x] in Original_Hashes_Keys:
                print(
                    "[File Changed]:\033[91m"
                    f"File {New_Hashes_Keys[x]}\033[0m"
                )
                if New_Hashes_Keys[x] not in self.Possible_Discrepancies:
                    self.Possible_Discrepancies[New_Hashes_Keys[x]] = 0
                    self.discrepancy_Signal.emit()
        return 0

    def Scan_Loop(self):

        """
        The loop that scans the os looking for possible discrepancies

        NOTE: This is run in a seperate thread
        """

        while self.running is True:
            print(self.Path)
            self.Original_Hashes.clear()
            self.New_Hashes.clear()

            t0 = time.perf_counter()
            if self.Scan_Files(self.Original_Hashes) == 1:
                break
            t1 = time.perf_counter()
            print("ScanFiles Time: " + str(t1-t0) + "s")

            for _ in range(self.wait_time):
                if self.running is False:
                    break
                print("Sleeping...ZZZZZZ")
                time.sleep(1)

            if self.Scan_Files(self.New_Hashes) == 1:
                break

            if self.Hash_Compare() == 1:
                break

    @pyqtSlot(str)
    def Log_Update(self, data):

        """
        Updates UI log output
        """

        self.LogOutput.appendPlainText(data)
        # Ensures that the user always sees that latest log (at the bottom)
        self.LogOutput.verticalScrollBar().setValue(
            self.LogOutput.verticalScrollBar().maximum()
        )

    @pyqtSlot()
    def discrepancy_update(self):

        """
        Updates the discrepancy logs
        """

        _type = [
            "[File Hash Changed]: ",
            "[File Has Been Added]: ",
            "[File Has Been Removed]: "
        ]

        self.DiscrepancyOutput.setPlainText("")

        while True:
            try:
                for entry in self.Possible_Discrepancies.keys():
                    self.DiscrepancyOutput.appendPlainText(f"{_type[self.Possible_Discrepancies[entry]]}{entry}\n")
                    #  break
                break
            except RuntimeError:
                print("Exception caught!\n\n\n\n")

    def Mirage_Function_Assigns(self):

        """
        Assign functions and actions to the different buttons and inputs
        """

        def Scan_Button_Action():
            if self.running is False:
                self.progressBar.setRange(0, 0)  # Creates pulsing progress bar
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
                    NewThread(self.Scan_Loop, False, True, "Scanning System")
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
                self.progressBar.setRange(0, 1)

        def Folder_Selection():
            dialog = str(QFileDialog.getExistingDirectory(self,
                                                          "Select Directory"))
            self.ScanLocationInput.setPlainText(dialog)
            self.Path = dialog

        def Folder_Input_Text():
            self.Path = self.ScanLocationInput.toPlainText()

        def Set_Timer():
            self.wait_time = self.sleep_Time.value()

        self.sleep_Time.valueChanged.connect(Set_Timer)
        self.discrepancy_Signal.connect(self.discrepancy_update)
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
