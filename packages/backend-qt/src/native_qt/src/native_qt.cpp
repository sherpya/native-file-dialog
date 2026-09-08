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
#include <QTimer>
#include <QThread>
#include <exception>

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
static bool s_dialog_active = false;

class DialogGuard {
public:
  explicit DialogGuard(const py::object &pump) {
    if (s_dialog_active)
      throw std::runtime_error("A native file dialog is already active");
    if (!pump.is_none() && !PyCallable_Check(pump.ptr()))
      throw py::type_error("event_pump must be callable or None");
    auto threading = py::module_::import("threading");
    if (!threading.attr("current_thread")().is(threading.attr("main_thread")()))
      throw std::runtime_error("Linux file dialogs must run on the main thread");
    s_dialog_active = true;
  }
  ~DialogGuard() { s_dialog_active = false; }
  DialogGuard(const DialogGuard &) = delete;
  DialogGuard &operator=(const DialogGuard &) = delete;
};

static bool pumpEvents(const py::object &pump) {
  return pump.is_none() || pump().ptr() != Py_False;
}

static int executeDialog(QFileDialog &dlg, const py::object &pump) {
  QTimer timer;
  std::exception_ptr error;
  bool cancelled = false;
  if (!pump.is_none()) {
    QObject::connect(&timer, &QTimer::timeout, &dlg, [&]() {
      py::gil_scoped_acquire acquire;
      try {
        if (pumpEvents(pump)) return;
      } catch (...) {
        error = std::current_exception();
      }
      cancelled = true;
      timer.stop();
      dlg.reject();
    });
    timer.start(20);
  }
  int accepted;
  { py::gil_scoped_release release; accepted = dlg.exec(); }
  timer.stop();
  if (error) std::rethrow_exception(error);
  return cancelled ? QDialog::Rejected : accepted;
}

static QApplication *appInstance() {
  if (auto *existing = QCoreApplication::instance()) {
    auto *app = qobject_cast<QApplication *>(existing);
    if (!app)
      throw std::runtime_error("File dialogs require QApplication, not QCoreApplication/QGuiApplication");
    if (app->thread() != QThread::currentThread())
      throw std::runtime_error("QApplication belongs to another thread");
    return app;  // Never own or delete an application's existing instance.
  }
  if (!s_app) {
    static int fake_argc = 1;
    static const char *fake_prog = "native_file_dialog";
    static char *fake_argv[] = { const_cast<char *>(fake_prog), nullptr };
    s_app = new QApplication(fake_argc, fake_argv);
  }
  return s_app;
}

py::object open_file(const std::string &title, const std::string &initialdir, const std::string &filter, const py::object &pump) {
  DialogGuard guard(pump);
  if (!pumpEvents(pump)) return py::none();
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

  int accepted = executeDialog(dlg, pump);
  if (!accepted) return py::none();
  const QStringList result = dlg.selectedFiles();
  if (result.isEmpty()) return py::none();
  return py::cast(result.at(0).toStdString());
}

std::vector<std::string> open_multiple(const std::string &title, const std::string &initialdir, const std::string &filter, const py::object &pump) {
  DialogGuard guard(pump);
  if (!pumpEvents(pump)) return {};
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

  int accepted = executeDialog(dlg, pump);
  if (!accepted) return {};
  const QStringList result = dlg.selectedFiles();
  std::vector<std::string> out;
  out.reserve(result.size());
  for (const QString &s : result) out.push_back(s.toStdString());
  return out;
}

py::object save_file(const std::string &title, const std::string &initialdir, const std::string &filter, const std::string &default_name, const py::object &pump) {
  DialogGuard guard(pump);
  if (!pumpEvents(pump)) return py::none();
  (void)appInstance();

  const QUrl startUrl = QUrl::fromUserInput(QString::fromStdString(initialdir));
  const DialogStart start = dialogStartFromUrl(startUrl);

  QFileDialog dlg;
  dlg.setWindowTitle(title.empty() ? QStringLiteral("Save As") : QString::fromStdString(title));
  dlg.setAcceptMode(QFileDialog::AcceptSave);
  dlg.setFileMode(QFileDialog::AnyFile);
  dlg.setSupportedSchemes({QStringLiteral("file")});
  dlg.setDirectoryUrl(start.directory);
  if (!default_name.empty())
    dlg.selectFile(QString::fromStdString(default_name));
  else
    dlg.selectFile(start.preselectedFile);
  applyFilter(dlg, QString::fromStdString(filter));

  int accepted = executeDialog(dlg, pump);
  if (!accepted) return py::none();
  const QStringList result = dlg.selectedFiles();
  if (result.isEmpty()) return py::none();
  return py::cast(result.at(0).toStdString());
}

py::object open_directory(const std::string &title, const std::string &initialdir, const py::object &pump) {
  DialogGuard guard(pump);
  if (!pumpEvents(pump)) return py::none();
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

  int accepted = executeDialog(dlg, pump);
  if (!accepted) return py::none();
  const QStringList result = dlg.selectedFiles();
  if (result.isEmpty()) return py::none();
  return py::cast(result.at(0).toStdString());
}

PYBIND11_MODULE(_native_qt, m) {
  m.def("open_file", &open_file, py::arg("title"), py::arg("initialdir"), py::arg("filters"), py::arg("event_pump") = py::none());
  m.def("open_multiple", &open_multiple, py::arg("title"), py::arg("initialdir"), py::arg("filters"), py::arg("event_pump") = py::none());
  m.def("save_file", &save_file, py::arg("title"), py::arg("initialdir"), py::arg("filters"), py::arg("default_name") = "", py::arg("event_pump") = py::none());
  m.def("open_directory", &open_directory, py::arg("title"), py::arg("initialdir"), py::arg("event_pump") = py::none());

  auto atexit = py::module_::import("atexit");
  atexit.attr("register")(py::cpp_function([]() {
    delete s_app;
    s_app = nullptr;
  }));
}
