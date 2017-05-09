import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import os
import h5py
from XrdAnalysis import Reader


class MainIcon(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(MainIcon, self).__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            for url in event.mimeData().urls():
                new_text = str(url.toLocalFile())
                self.read_raw(new_text)
        else:
            event.ignore()

    @staticmethod
    def ch_work_dir():
        my_path = r'C:\Users\hang\Dropbox\Experimental_Data'
        os.chdir(my_path)

    def sym_beam_intensity(self):
        self.ch_work_dir()
        with open('xrd_lib.h5', 'a'):
            file_handle = h5py.File('xrd_lib.h5')
        for i in file_handle.keys():
            try:
                sample = file_handle[i]
                import numpy
                int1 = numpy.asanyarray(sample['beam1mm/int_data'])
                int2 = numpy.asanyarray(sample['beam8mm/int_data'])

                int_mean = (int1.max() + int2.max()) / 2
                sample['pf'].attrs.__setitem__('beam_intensity', int_mean * 8940)
            except (KeyError, AttributeError) as e:
                print(e)
                pass
        file_handle.close()

    def read_raw(self, dropped_file):
        # Require data.
        self.ch_work_dir()
        file_handle = h5py.File('xrd_lib.h5', 'a')

        logging.debug("Reading file {0}...".format(dropped_file))
        instance = Reader.reader(dropped_file)
        if instance is None:
            logging.info('Can not recognize file type.')
            return
        instance = instance.read_data()

        sub_file_name = (
            instance.get_scan_attribute('sample') +
            '/' + os.path.basename(dropped_file).split('.')[0])

        logging.debug("Saving file to {0}...".format(sub_file_name))

        group_handle = file_handle.require_group(sub_file_name)

        # Record data.
        data_dict = instance.get_data_dict()
        for key in data_dict.keys():
            try:
                del group_handle[key]
            except (TypeError, KeyError):
                pass
            try:
                group_handle.create_dataset(
                    key,
                    data=data_dict[key]
                )
            except TypeError as e:
                logging.error(e)
                pass

        # Record Setup
        scan_dict = instance.get_scan_dict()
        for key in scan_dict.keys():
            try:
                group_handle.attrs.modify(key, scan_dict[key])
            except TypeError:
                pass
        file_handle.close()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = MainIcon(self)
        self.ui.setObjectName("background_label")

        self.setStyleSheet(
            "QWidget#background_label "
            "{border-image: url(Apps-File-Save-icon.png)}")
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(True)
        self.setFixedSize(60, 60)
        self.offset = None

        self.setCentralWidget(self.ui)

        _pop_menu_exit_button = QtWidgets.QAction('Exit', self)
        _pop_menu_exit_button.triggered.connect(self.close)

        self.popMenu = QtWidgets.QMenu(self)
        self.popMenu.addAction(QtWidgets.QAction('test0', self))
        self.popMenu.addAction(QtWidgets.QAction('test1', self))
        self.popMenu.addSeparator()
        self.popMenu.addAction(_pop_menu_exit_button)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.offset = event.pos()
        elif event.button() == QtCore.Qt.RightButton:
            self.popMenu.exec_(self.mapToGlobal(event.pos()))

    def mouseMoveEvent(self, event):
        x = event.globalX()
        y = event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x - x_w, y - y_w)


def main():
    app = QtWidgets.QApplication(sys.argv)

    ex_window = MainWindow()
    ex_window.show()
    exit_code_sys = app.exec_()
    app.deleteLater()
    sys.exit(exit_code_sys)


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    main()
