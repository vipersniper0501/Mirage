import os
import pathlib
import time
import datetime
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
            threads[-1].start()
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
    Original_History = {}
    New_History = {}
    Possible_Discrepancies = {}
    scanPath = ""
    updateSignal = pyqtSignal(str)
    discrepancy_Signal = pyqtSignal()
    wait_time = 30
    collecting_garbage = True

    def __init__(self, parent=None):
        super(MirageMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setFixedSize(1078, 598)
        try:
            self.scanPath = sys.argv[1]
        except IndexError:
            self.scanPath = "./"
        self.Mirage_Function_Assigns()
        # NewThread(self.garbage_Collection, False, False, "Collecting Garbage")

    def garbage_Collection(self):

        """
        Iterates through the controlling threads list and removes and dead
        threads while in another thread.
        """

        while True:
            for t in threads:
                if t.getName() != "Scanning System":
                    t.join()
                    threads.remove(t)
            if len(threads) <= 2:
                self.collecting_garbage = False

    def Scan_Files(self, dictionary):

        """
        Recursively traverse through the OS from the specified path
        and append found files/directories to specified dictionary along
        with the hash of the file.

        :param dictionary: the dictionary that will be appended with hashes
        """

        def Check_File_Data(root, f):

            """
            Checks the file for its last accessed date and appends to a
            dictionary.
            """

            try:
                fname = pathlib.Path(os.path.join(root, f))
                dictionary[fname] = datetime.datetime.fromtimestamp(
                    fname.stat().st_mtime)
                self.updateSignal.emit(f"{fname}: {dictionary[fname]}")
            except FileNotFoundError:
                self.updateSignal.emit(
                    f"File '{f}' could not be accessed."
                )

        def Generate_Hash(root, f):

            """
            Generates a file hash for the inputted file
            :param root: directory file is located in
            :param f: file name to hash
            """

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

        for root, _, f_names in os.walk(self.scanPath):
            if self.running is False:
                return 1
            for f in f_names:
                # NewThread(Generate_Hash, False, True, str(f), root, f)
                NewThread(Check_File_Data, False, True, str(f), root, f)
        # while self.collecting_Garbage:
        #     # attempt at locking thread until garbage collection had finished.
        #     pass
            for t in threads:
                if t.getName() != "Scanning System":
                    # print(f"Collecting Garbage: {t.getName()}")
                    t.join()
                    threads.remove(t)
        for t in threads:
            if t.getName() != "Scanning System":
                t.join()
                threads.remove(t)

    def Compare_History(self):

        """
        Compares the File History to determine possible discrepancies
        Possible Discrepencies: File Added, File Removed, File Changed
        """

        # TODO NOTE: Infinite loop occurs after file delete, add, or change
        # while scanning system creating a fatal flaw that essentially makes
        # the program useless. Need to find a way to handle this error.

        # TODO NOTE: Need to make it so that program can tell when a deleted
        # file comes back or when a newly created file has been edited.

        Original_History_Values = list(self.Original_History.values())
        New_History_Values = list(self.New_History.values())
        New_History_Keys = list(self.New_History.keys())
        Original_History_Keys = list(self.Original_History.keys())
        for x, hashes in enumerate(New_History_Values):
            if self.running is False:
                return 1
            # File Has Been Added
            if len(New_History_Keys) > len(Original_History_Keys):
                if New_History_Keys[x] not in Original_History_Keys:
                    if New_History_Keys[x] not in self.Possible_Discrepancies:
                        self.Possible_Discrepancies[
                            New_History_Keys[x]
                        ] = 1
                        self.discrepancy_Signal.emit()
                print(f"New file was added {New_History_Keys[x]}")
            # File Has Been Deleted
            if len(New_History_Keys) < len(Original_History_Keys):
                if Original_History_Keys[x] not in New_History_Keys:
                    if Original_History_Keys[x] not in self.Possible_Discrepancies:
                        self.Possible_Discrepancies[
                            Original_History_Keys[x]
                        ] = 2
                        self.discrepancy_Signal.emit()
                    print(f"File was removed {Original_History_Keys[x]}")
            # File Has Been Modified
            if hashes not in Original_History_Values and \
                    New_History_Keys[x] in Original_History_Keys:
                print(
                    "[File Changed]:\033[91m"
                    f"File {New_History_Keys[x]}\033[0m"
                )
                if New_History_Keys[x] not in self.Possible_Discrepancies:
                    self.Possible_Discrepancies[New_History_Keys[x]] = 0
                    self.discrepancy_Signal.emit()
        return 0

    def Scan_Loop(self):

        """
        The loop that scans the os looking for possible discrepancies

        NOTE: This is run in a separate thread
        """

        while self.running is True:
            print(self.scanPath)
            self.Original_History.clear()
            self.New_History.clear()

            t0 = time.perf_counter()
            if self.Scan_Files(self.Original_History) == 1:
                break
            t1 = time.perf_counter()
            print("ScanFiles Time: " + str(t1-t0) + "s")

            for _ in range(self.wait_time):
                if self.running is False:
                    break
                print("Sleeping...ZZZZZZ")
                time.sleep(1)

            if self.Scan_Files(self.New_History) == 1:
                break

            if self.Compare_History() == 1:
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
            "[File Has Changed]: ",
            "[File Has Been Added]: ",
            "[File Has Been Removed]: "
        ]

        self.DiscrepancyOutput.setPlainText("")

        while True:
            try:
                for entry in self.Possible_Discrepancies.keys():
                    self.DiscrepancyOutput.appendPlainText(
                        f"{_type[self.Possible_Discrepancies[entry]]}{entry}\n"
                    )
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
            self.scanPath = dialog

        def Folder_Input_Text():
            self.scanPath = self.ScanLocationInput.toPlainText()

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
