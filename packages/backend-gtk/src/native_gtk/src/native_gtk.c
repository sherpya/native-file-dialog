/*
 * Native file dialog for native_file_dialog.
 * GTK4/libadwaita (NFD_USE_GTK4) or GTK3.
 * SPDX-License-Identifier: MIT
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#ifdef NFD_USE_GTK4
#include <adwaita.h>
#endif
#include <gtk/gtk.h>
#include <glib.h>
#include <string.h>

/* G_APPLICATION_DEFAULT_FLAGS was added in GLib 2.74 but its expansion
   may reference the deprecated G_APPLICATION_FLAGS_NONE enum, triggering
   a warning on older toolchains. Fall back to the raw value if missing. */
#ifndef G_APPLICATION_DEFAULT_FLAGS
#define G_APPLICATION_DEFAULT_FLAGS ((GApplicationFlags) 0)
#endif

/* ---- Shared state ---- */

static GPtrArray *nfd_result_paths = NULL;
static int nfd_canceled = 1;

static char *nfd_title = NULL;
static char *nfd_initialdir = NULL;
static char **nfd_filter_list = NULL;
static int nfd_multi = 0;
static int nfd_save = 0;
static int nfd_choose_dir = 0;

static void nfd_clear_result(void) {
  if (nfd_result_paths) {
    g_ptr_array_free(nfd_result_paths, TRUE);
    nfd_result_paths = NULL;
  }
  nfd_canceled = 1;
}

static void nfd_store_path(const char *path) {
  if (!nfd_result_paths)
    nfd_result_paths = g_ptr_array_new_with_free_func(g_free);
  g_ptr_array_add(nfd_result_paths, g_strdup(path));
  nfd_canceled = 0;
}

static void nfd_free_params(void) {
  g_free(nfd_title);
  nfd_title = NULL;
  g_free(nfd_initialdir);
  nfd_initialdir = NULL;
  if (nfd_filter_list) {
    for (char **p = nfd_filter_list; *p; p++) g_free(*p);
    g_free(nfd_filter_list);
    nfd_filter_list = NULL;
  }
}

/* ---- GTK version-specific implementation ---- */

#ifdef NFD_USE_GTK4

/* Build GListModel of GtkFileFilter from "Description | pat1 pat2" list. */
static GListModel *nfd_build_filters(char **filter_list) {
  if (!filter_list) return NULL;
  GListStore *store = g_list_store_new(GTK_TYPE_FILE_FILTER);
  for (int i = 0; filter_list[i]; i++) {
    char *filter_str = filter_list[i];
    GtkFileFilter *filter = gtk_file_filter_new();
    int j = 0;
    g_autofree char *name = NULL;
    g_auto(GStrv) patterns = NULL;

    while (filter_str[j] != '\0' && filter_str[j] != '|') j++;

    if (filter_str[j] == '|') {
      name = g_strndup(filter_str, j);
      g_strstrip(name);
      j++;
      while (filter_str[j] == ' ') j++;
      patterns = g_strsplit_set(filter_str + j, " ", -1);
    } else {
      patterns = g_strsplit_set(filter_str, " ", -1);
    }
    if (name)
      gtk_file_filter_set_name(filter, name);
    else
      gtk_file_filter_set_name(filter, filter_str);
    for (char **p = patterns; p && *p; p++)
      if ((*p)[0])
        gtk_file_filter_add_pattern(filter, *p);
    g_list_store_append(store, filter);
    g_object_unref(filter);
  }
  return G_LIST_MODEL(store);
}

static void dialog_ready_cb(GObject *source_object, GAsyncResult *result, gpointer user_data) {
  GtkFileDialog *dialog = GTK_FILE_DIALOG(source_object);
  GApplication *app = G_APPLICATION(user_data);
  g_autoptr(GError) error = NULL;

  if (nfd_choose_dir) {
    GFile *file = gtk_file_dialog_select_folder_finish(dialog, result, &error);
    if (!error && file) {
      g_autofree char *path = g_file_get_path(file);
      if (path) nfd_store_path(path);
      g_object_unref(file);
    }
  } else if (nfd_save) {
    GFile *file = gtk_file_dialog_save_finish(dialog, result, &error);
    if (!error && file) {
      g_autofree char *path = g_file_get_path(file);
      if (path) nfd_store_path(path);
      g_object_unref(file);
    }
  } else if (nfd_multi) {
    g_autoptr(GListModel) files = gtk_file_dialog_open_multiple_finish(dialog, result, &error);
    if (!error && files) {
      guint n = g_list_model_get_n_items(files);
      for (guint i = 0; i < n; i++) {
        GFile *file = g_list_model_get_item(files, i);
        g_autofree char *path = g_file_get_path(file);
        if (path) nfd_store_path(path);
        g_object_unref(file);
      }
    }
  } else {
    GFile *file = gtk_file_dialog_open_finish(dialog, result, &error);
    if (!error && file) {
      g_autofree char *path = g_file_get_path(file);
      if (path) nfd_store_path(path);
      g_object_unref(file);
    }
  }
  g_object_unref(source_object);
  g_application_quit(app);
}

static void on_activate(GApplication *app, gpointer user_data) {
  (void)user_data;
  adw_init();
  g_application_hold(app);

  GtkFileDialog *dialog = gtk_file_dialog_new();
  const char *default_title = nfd_choose_dir ? "Select Folder" : (nfd_save ? "Save As" : "Open");
  gtk_file_dialog_set_title(dialog, nfd_title ? nfd_title : default_title);

  if (nfd_initialdir && nfd_initialdir[0]) {
    g_autoptr(GFile) dir = g_file_new_for_path(nfd_initialdir);
    gtk_file_dialog_set_initial_folder(dialog, dir);
  }

  g_autoptr(GListModel) filters_model = nfd_build_filters(nfd_filter_list);
  if (filters_model)
    gtk_file_dialog_set_filters(dialog, filters_model);

  g_object_ref(dialog);
  if (nfd_choose_dir)
    gtk_file_dialog_select_folder(dialog, NULL, NULL, dialog_ready_cb, app);
  else if (nfd_save)
    gtk_file_dialog_save(dialog, NULL, NULL, dialog_ready_cb, app);
  else if (nfd_multi)
    gtk_file_dialog_open_multiple(dialog, NULL, NULL, dialog_ready_cb, app);
  else
    gtk_file_dialog_open(dialog, NULL, NULL, dialog_ready_cb, app);
}

#else /* GTK3 */

static void nfd_add_filters(GtkFileChooser *chooser, char **filter_list) {
  if (!filter_list) return;
  for (int i = 0; filter_list[i]; i++) {
    char *filter_str = filter_list[i];
    GtkFileFilter *filter = gtk_file_filter_new();
    int j = 0;
    g_autofree char *name = NULL;
    g_auto(GStrv) patterns = NULL;

    while (filter_str[j] != '\0' && filter_str[j] != '|') j++;

    if (filter_str[j] == '|') {
      name = g_strndup(filter_str, j);
      g_strstrip(name);
      j++;
      while (filter_str[j] == ' ') j++;
      patterns = g_strsplit_set(filter_str + j, " ", -1);
    } else {
      patterns = g_strsplit_set(filter_str, " ", -1);
    }
    if (name)
      gtk_file_filter_set_name(filter, name);
    else
      gtk_file_filter_set_name(filter, filter_str);
    for (char **p = patterns; p && *p; p++)
      if ((*p)[0])
        gtk_file_filter_add_pattern(filter, *p);
    gtk_file_chooser_add_filter(chooser, filter);
  }
}

static void dialog_response_cb(GtkNativeDialog *native, int response, gpointer user_data) {
  GtkFileChooser *chooser = GTK_FILE_CHOOSER(native);
  GApplication *app = G_APPLICATION(user_data);

  if (response == GTK_RESPONSE_ACCEPT) {
    if (nfd_multi) {
      GSList *filenames = gtk_file_chooser_get_filenames(chooser);
      for (GSList *l = filenames; l; l = l->next) {
        nfd_store_path((const char *)l->data);
        g_free(l->data);
      }
      g_slist_free(filenames);
    } else {
      gchar *filename = gtk_file_chooser_get_filename(chooser);
      if (filename) {
        nfd_store_path(filename);
        g_free(filename);
      }
    }
  }
  g_object_unref(native);
  g_application_quit(app);
}

static void on_activate(GApplication *app, gpointer user_data) {
  (void)user_data;
  g_application_hold(app);

  GtkFileChooserAction action;
  if (nfd_choose_dir)
    action = GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER;
  else if (nfd_save)
    action = GTK_FILE_CHOOSER_ACTION_SAVE;
  else
    action = GTK_FILE_CHOOSER_ACTION_OPEN;

  const char *default_title = nfd_choose_dir ? "Select Folder" : (nfd_save ? "Save As" : "Open");
  GtkFileChooserNative *dialog = gtk_file_chooser_native_new(
      nfd_title ? nfd_title : default_title,
      NULL, action, "_OK", "_Cancel");

  g_signal_connect(dialog, "response", G_CALLBACK(dialog_response_cb), app);

  if (nfd_initialdir && nfd_initialdir[0])
    gtk_file_chooser_set_current_folder(GTK_FILE_CHOOSER(dialog), nfd_initialdir);

  if (nfd_multi)
    gtk_file_chooser_set_select_multiple(GTK_FILE_CHOOSER(dialog), TRUE);

  nfd_add_filters(GTK_FILE_CHOOSER(dialog), nfd_filter_list);
  gtk_native_dialog_show(GTK_NATIVE_DIALOG(dialog));
}

#endif /* NFD_USE_GTK4 */

/* ---- Shared: run dialog and convert result to Python ---- */

static PyObject *run_dialog(void) {
  nfd_clear_result();

  /* Suppress deprecation warning for G_APPLICATION_DEFAULT_FLAGS on glib 2.74
     where the macro internally expands to the deprecated G_APPLICATION_FLAGS_NONE. */
  G_GNUC_BEGIN_IGNORE_DEPRECATIONS
#ifdef NFD_USE_GTK4
  g_autoptr(AdwApplication) app = adw_application_new("org.nativefiledialog.gtk", G_APPLICATION_DEFAULT_FLAGS);
#else
  g_autoptr(GtkApplication) app = gtk_application_new("org.nativefiledialog.gtk", G_APPLICATION_DEFAULT_FLAGS);
#endif
  G_GNUC_END_IGNORE_DEPRECATIONS
  g_signal_connect(app, "activate", G_CALLBACK(on_activate), NULL);
  Py_BEGIN_ALLOW_THREADS
  g_application_run(G_APPLICATION(app), 0, NULL);
  Py_END_ALLOW_THREADS

  if (nfd_canceled || !nfd_result_paths || nfd_result_paths->len == 0) {
    nfd_clear_result();
    Py_RETURN_NONE;
  }

  if (nfd_multi) {
    PyObject *list = PyList_New((Py_ssize_t)nfd_result_paths->len);
    if (!list) { nfd_clear_result(); return NULL; }
    for (guint i = 0; i < nfd_result_paths->len; i++) {
      char *path = g_ptr_array_index(nfd_result_paths, i);
      PyObject *p = PyUnicode_FromString(path);
      if (!p) { Py_DECREF(list); nfd_clear_result(); return NULL; }
      PyList_SET_ITEM(list, (Py_ssize_t)i, p);
    }
    nfd_clear_result();
    return list;
  } else {
    char *path = g_ptr_array_index(nfd_result_paths, 0);
    PyObject *p = PyUnicode_FromString(path);
    nfd_clear_result();
    return p;
  }
}

/* ---- Shared Python API ---- */

static int nfd_parse_filter_arg(PyObject *filter_list_obj) {
  if (filter_list_obj && filter_list_obj != Py_None && PyList_Check(filter_list_obj)) {
    Py_ssize_t n = PyList_GET_SIZE(filter_list_obj);
    nfd_filter_list = g_new0(char *, (size_t)n + 1);
    for (Py_ssize_t i = 0; i < n; i++) {
      PyObject *item = PyList_GET_ITEM(filter_list_obj, i);
      if (PyUnicode_Check(item)) {
        Py_ssize_t size;
        const char *s = PyUnicode_AsUTF8AndSize(item, &size);
        if (s) nfd_filter_list[i] = g_strndup(s, (size_t)size);
      }
    }
  }
  return 0;
}

static PyObject *py_open_file(PyObject *self, PyObject *args) {
  const char *title = NULL, *initialdir = NULL;
  PyObject *filter_list_obj = NULL;
  (void)self;
  if (!PyArg_ParseTuple(args, "ss|O", &title, &initialdir, &filter_list_obj))
    return NULL;

  nfd_free_params();
  nfd_title = g_strdup(title);
  nfd_initialdir = g_strdup(initialdir);
  nfd_parse_filter_arg(filter_list_obj);
  nfd_multi = 0;
  nfd_save = 0;
  nfd_choose_dir = 0;
  return run_dialog();
}

static PyObject *py_open_multiple(PyObject *self, PyObject *args) {
  const char *title = NULL, *initialdir = NULL;
  PyObject *filter_list_obj = NULL;
  (void)self;
  if (!PyArg_ParseTuple(args, "ss|O", &title, &initialdir, &filter_list_obj))
    return NULL;

  nfd_free_params();
  nfd_title = g_strdup(title);
  nfd_initialdir = g_strdup(initialdir);
  nfd_parse_filter_arg(filter_list_obj);
  nfd_multi = 1;
  nfd_save = 0;
  nfd_choose_dir = 0;

  PyObject *result = run_dialog();
  if (result == Py_None) {
    Py_DECREF(result);
    return PyList_New(0);
  }
  return result;
}

static PyObject *py_save_file(PyObject *self, PyObject *args) {
  const char *title = NULL, *initialdir = NULL;
  PyObject *filter_list_obj = NULL;
  (void)self;
  if (!PyArg_ParseTuple(args, "ss|O", &title, &initialdir, &filter_list_obj))
    return NULL;

  nfd_free_params();
  nfd_title = g_strdup(title);
  nfd_initialdir = g_strdup(initialdir);
  nfd_parse_filter_arg(filter_list_obj);
  nfd_multi = 0;
  nfd_save = 1;
  nfd_choose_dir = 0;
  return run_dialog();
}

static PyObject *py_open_directory(PyObject *self, PyObject *args) {
  const char *title = NULL, *initialdir = NULL;
  (void)self;
  if (!PyArg_ParseTuple(args, "ss", &title, &initialdir))
    return NULL;

  nfd_free_params();
  nfd_title = g_strdup(title);
  nfd_initialdir = g_strdup(initialdir);
  nfd_multi = 0;
  nfd_save = 0;
  nfd_choose_dir = 1;
  return run_dialog();
}

static PyMethodDef nfd_methods[] = {
  {"open_file", py_open_file, METH_VARARGS, "Open file dialog (single)."},
  {"open_multiple", py_open_multiple, METH_VARARGS, "Open file dialog (multiple)."},
  {"save_file", py_save_file, METH_VARARGS, "Save file dialog (with optional filters)."},
  {"open_directory", py_open_directory, METH_VARARGS, "Choose directory dialog."},
  {NULL, NULL, 0, NULL}
};

/* ---- Module definition ---- */

#ifdef NFD_USE_GTK4
#define NFD_MODULE_NAME "_native_gtk"
#else
#define NFD_MODULE_NAME "_native_gtk3"
#endif

static struct PyModuleDef nfd_module = {
  PyModuleDef_HEAD_INIT,
  NFD_MODULE_NAME,
  NULL,
  -1,
  nfd_methods
};

#ifdef NFD_USE_GTK4
PyMODINIT_FUNC PyInit__native_gtk(void) {
  return PyModule_Create(&nfd_module);
}
#else
PyMODINIT_FUNC PyInit__native_gtk3(void) {
  return PyModule_Create(&nfd_module);
}
#endif
