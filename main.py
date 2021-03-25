import os
import time
import sys
import hashlib
from platform import uname

from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QDialog
from PyQt5.QtCore import Qt

from UI.MirageMainWindow import Ui_MainWindow

try:
    Path = sys.argv[1]
except Exception:
    Path = "./"

BUF_SIZE = 65536

# TODO: move this to a .csv file maybe...
Original_Hashes = {}
New_Hashes = {}

Possible_Discrepancies = {}


def Scan_Files(dictionary):
    """
    Recursively traverse through the OS from the specified path
    and append found files/directories to specified dictionary along
    with the hash of the file.
    """
    for root, d_names, f_names in os.walk(Path):
        print("OS Walk Result:")
        print(root, d_names, f_names)
        for f in f_names:
            sha256 = hashlib.sha256()
            print(f)
            try:
                with open(os.path.join(root, f), 'rb') as file:
                    while True:
                        data = file.read(BUF_SIZE)
                        if not data:
                            break
                        sha256.update(data)
                        file.close
            except Exception as e:
                print(
                    f"File '{f}' was found but could not be accessed because"
                    f"of the following exception: {e}"
                )
            dictionary[os.path.join(root, f)] = sha256.hexdigest()
    print(dictionary)


def Hash_Compare():
    global Original_Hashes
    global New_Hashes
    global Possible_Discrepancies
    Original_Hashes_Values = list(Original_Hashes.values())
    New_Hashes_Values = list(New_Hashes.values())
    New_Hashes_Keys = list(New_Hashes.keys())
    Original_Hashes_Keys = list(Original_Hashes.keys())
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
            if New_Hashes_Keys[i] not in Possible_Discrepancies:
                temp = [Original_Hashes_Values[i], New_Hashes_Values[i]]
                Possible_Discrepancies[New_Hashes_Keys[i]] = temp
    return 0


def test_Change_File():
    with open("./test", "+w") as f:
        f.write("Hello World!")
        f.close


def test_loop():
    while True:
        Scan_Files(Original_Hashes)
        test_Change_File()
        time.sleep(60)
        Scan_Files(New_Hashes)
        result = Hash_Compare()
        if result == 0:
            for i in range(len(Possible_Discrepancies)):
                print("\n\n\nList of Possible Discrepencies:")
                print(
                    f"\n\nFile: {list(Possible_Discrepancies.keys())[i]}\n"
                    f"Original Hash: "
                    f"{list(Possible_Discrepancies.values())[i][0]}\n"
                    f"New Hash: {list(Possible_Discrepancies.values())[i][1]}"
                )
            break


class MirageMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MirageMainWindow, self).__init__(parent)
        self.setupUi(self)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    main = MirageMainWindow()
    main.show()
    sys.exit(app.exec_())
