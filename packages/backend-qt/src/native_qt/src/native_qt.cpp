/*
 * Minimal Qt6 file dialog for native_file_dialog (open/save, single and multiple).
 * Uses Qt6 Core, Gui, Widgets only (no KF6).
 * SPDX-License-Identifier: MIT
 */

/* Include pybind11/Python.h before Qt so Qt's "slots" macro does not break PyType_Slot. */
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <QApplication>
#include <QCoreApplication>
#include <QFileDialog>
#include <QFileInfo>
#include <QString>
#include <QUrl>

namespace py = pybind11;

struct DialogStart {
  QUrl directory;
  QString preselectedFile;
};

static DialogStart dialogStartFromUrl(const QUrl &url) {
  DialogStart out;
  out.directory = url.adjusted(QUrl::RemoveFilename);
  out.preselectedFile = QString();
  if (url.isEmpty()) return out;
  if (url.isLocalFile()) {
    const QFileInfo fi(url.toLocalFile());
    if (fi.isDir()) {
      out.directory = url;
    } else {
      out.preselectedFile = fi.fileName();
    }
  } else {
    out.preselectedFile = url.fileName();
  }
  return out;
}

static void applyFilter(QFileDialog &dlg, const QString &filter) {
  if (!filter.isEmpty()) dlg.setNameFilter(filter);
}

static QApplication *s_app = nullptr;

static QApplication *appInstance() {
  if (!s_app) {
    static int fake_argc = 1;
    static const char *fake_prog = "native_file_dialog";
    static char *fake_argv[] = { const_cast<char *>(fake_prog), nullptr };
    s_app = new QApplication(fake_argc, fake_argv);
  }
  return s_app;
}

py::object open_file(const std::string &title, const std::string &initialdir, const std::string &filter) {
  (void)appInstance();

  const QUrl startUrl = QUrl::fromUserInput(QString::fromStdString(initialdir));
  const DialogStart start = dialogStartFromUrl(startUrl);

  QFileDialog dlg;
  dlg.setWindowTitle(title.empty() ? QStringLiteral("Open") : QString::fromStdString(title));
  dlg.setAcceptMode(QFileDialog::AcceptOpen);
  dlg.setFileMode(QFileDialog::ExistingFile);
  dlg.setSupportedSchemes({QStringLiteral("file")});
  dlg.setDirectoryUrl(start.directory);
  dlg.selectFile(start.preselectedFile);
  applyFilter(dlg, QString::fromStdString(filter));

  int accepted;
  { py::gil_scoped_release release; accepted = dlg.exec(); }
  if (!accepted) return py::none();
  const QStringList result = dlg.selectedFiles();
  if (result.isEmpty()) return py::none();
  return py::cast(result.at(0).toStdString());
}

std::vector<std::string> open_multiple(const std::string &title, const std::string &initialdir, const std::string &filter) {
  (void)appInstance();

  const QUrl startUrl = QUrl::fromUserInput(QString::fromStdString(initialdir));
  const DialogStart start = dialogStartFromUrl(startUrl);

  QFileDialog dlg;
  dlg.setWindowTitle(title.empty() ? QStringLiteral("Open") : QString::fromStdString(title));
  dlg.setAcceptMode(QFileDialog::AcceptOpen);
  dlg.setFileMode(QFileDialog::ExistingFiles);
  dlg.setSupportedSchemes({QStringLiteral("file")});
  dlg.setDirectoryUrl(start.directory);
  dlg.selectFile(start.preselectedFile);
  applyFilter(dlg, QString::fromStdString(filter));

  int accepted;
  { py::gil_scoped_release release; accepted = dlg.exec(); }
  if (!accepted) return {};
  const QStringList result = dlg.selectedFiles();
  std::vector<std::string> out;
  out.reserve(result.size());
  for (const QString &s : result) out.push_back(s.toStdString());
  return out;
}

py::object save_file(const std::string &title, const std::string &initialdir, const std::string &filter) {
  (void)appInstance();

  const QUrl startUrl = QUrl::fromUserInput(QString::fromStdString(initialdir));
  const DialogStart start = dialogStartFromUrl(startUrl);

  QFileDialog dlg;
  dlg.setWindowTitle(title.empty() ? QStringLiteral("Save As") : QString::fromStdString(title));
  dlg.setAcceptMode(QFileDialog::AcceptSave);
  dlg.setFileMode(QFileDialog::AnyFile);
  dlg.setSupportedSchemes({QStringLiteral("file")});
  dlg.setDirectoryUrl(start.directory);
  dlg.selectFile(start.preselectedFile);
  applyFilter(dlg, QString::fromStdString(filter));

  int accepted;
  { py::gil_scoped_release release; accepted = dlg.exec(); }
  if (!accepted) return py::none();
  const QStringList result = dlg.selectedFiles();
  if (result.isEmpty()) return py::none();
  return py::cast(result.at(0).toStdString());
}

py::object open_directory(const std::string &title, const std::string &initialdir) {
  (void)appInstance();

  const QUrl startUrl = QUrl::fromUserInput(QString::fromStdString(initialdir));
  const DialogStart start = dialogStartFromUrl(startUrl);

  QFileDialog dlg;
  dlg.setWindowTitle(title.empty() ? QStringLiteral("Select Directory") : QString::fromStdString(title));
  dlg.setAcceptMode(QFileDialog::AcceptOpen);
  dlg.setFileMode(QFileDialog::Directory);
  dlg.setOption(QFileDialog::ShowDirsOnly, true);
  dlg.setSupportedSchemes({QStringLiteral("file")});
  dlg.setDirectoryUrl(start.directory);

  int accepted;
  { py::gil_scoped_release release; accepted = dlg.exec(); }
  if (!accepted) return py::none();
  const QStringList result = dlg.selectedFiles();
  if (result.isEmpty()) return py::none();
  return py::cast(result.at(0).toStdString());
}

PYBIND11_MODULE(_native_qt, m) {
  m.def("open_file", &open_file, py::arg("title"), py::arg("initialdir"), py::arg("filters"));
  m.def("open_multiple", &open_multiple, py::arg("title"), py::arg("initialdir"), py::arg("filters"));
  m.def("save_file", &save_file, py::arg("title"), py::arg("initialdir"), py::arg("filters"));
  m.def("open_directory", &open_directory, py::arg("title"), py::arg("initialdir"));

  auto atexit = py::module_::import("atexit");
  atexit.attr("register")(py::cpp_function([]() {
    delete s_app;
    s_app = nullptr;
  }));
}
