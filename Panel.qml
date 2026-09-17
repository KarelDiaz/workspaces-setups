import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// Workspace Setups: bar icon that lists named workspace setups and opens
// them. Launching sends every app of the setup to its configured workspace,
// silently, via:
//   hyprctl dispatch 'hl.dsp.exec_cmd("[workspace N silent] uwsm-app -- CMD")'
// Management (create/edit/delete) lives in a regular system window —
// ~/.config/omarchy/workspace-setups/workspace_setups.py — because popup
// panels don't handle text input focus well.
// Setups persist in ~/.config/omarchy/workspace-setups.json; the file is
// watched, so edits from the manager window apply without a shell restart.
Item {
  id: root

  property QtObject bar: null
  property string moduleName: "karel.workspace-setups"
  property var settings: ({})

  property string configPath: settings.configPath ||
    (Quickshell.env("HOME") || "") + "/.config/omarchy/workspace-setups.json"
  property string busyPath: "/tmp/workspace-setups.busy"
  property var setups: []
  property bool busy: false

  readonly property bool opened: popup.open
  readonly property color fg: bar ? bar.barForeground : Color.foreground
  readonly property string fontFam: bar ? bar.fontFamily : Style.font.family

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  function open() { popup.open = true }
  function close() { popup.open = false }
  function toggle() { opened ? close() : open() }

  function parseConfig(text) {
    try {
      var data = JSON.parse(text)
      var list = data && data.setups ? data.setups : []
      var clean = []
      for (var i = 0; i < list.length; i++) {
        var s = list[i]
        if (!s || !s.name) continue
        s.apps = s.apps || []
        clean.push(s)
      }
      setups = clean
    } catch (e) {
      setups = []
    }
  }

  function appSummary(setup) {
    var parts = []
    for (var i = 0; i < setup.apps.length; i++) {
      var app = setup.apps[i]
      if (!app || !app.command) continue
      var cmd = String(app.command).split(" ")[0]
      parts.push((app.workspace !== undefined && app.workspace !== null ? app.workspace : "?") + ": " + cmd)
    }
    return parts.length ? parts.join("  ·  ") : "Sin aplicaciones"
  }

  function launchSetup(index) {
    if (root.busy) return
    launchProc.idx = String(index)
    if (!launchProc.running) launchProc.running = true
    close()
  }

  function openManager() {
    if (!managerProc.running) managerProc.running = true
    close()
  }

  FileView {
    id: configFile
    path: root.configPath
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.parseConfig(text())
    onLoadFailed: root.setups = []
  }

  // Lanza el script secuencial; crea /tmp/workspace-setups.busy mientras corre.
  Process {
    id: launchProc
    property string idx: "0"
    command: ["bash", Quickshell.env("HOME") + "/.config/omarchy/plugins/kareldiaz.workspace-setups/launch.sh", idx]
  }

  Process {
    id: managerProc
    command: ["python3", Quickshell.env("HOME") + "/.config/omarchy/plugins/kareldiaz.workspace-setups/workspace_setups.py"]
  }

  // Sondea el archivo busy para mostrar el spinner mientras corre el setup.
  // (El gestor en Python usa el mismo launcher, asi que tambien lo cubre.)
  Process {
    id: busyProbe
    command: ["test", "-f", root.busyPath]
    onExited: function(code) { root.busy = (code === 0) }
  }

  Timer {
    interval: 500
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: if (!busyProbe.running) busyProbe.running = true
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.busy ? "󰑐" : "󰀻"
    tooltipText: root.busy ? "Abriendo espacio…" : "Espacios de trabajo"
    active: root.opened || root.busy
    onPressed: function(b) { root.toggle() }
  }

  // Gira el icono mientras se esta abriendo un espacio.
  SequentialAnimation {
    running: root.busy
    loops: Animation.Infinite
    NumberAnimation {
      target: button
      property: "textRotation"
      from: 0
      to: 360
      duration: 900
    }
    onRunningChanged: if (!running) button.textRotation = 0
  }

  PopupCard {
    id: popup
    anchorItem: button
    owner: root
    bar: root.bar
    triggerMode: "click"
    contentWidth: fittedContentWidth(Style.space(280))
    contentHeight: fittedContentHeight(panelColumn.implicitHeight, Style.space(420))

    Column {
      id: panelColumn
      width: parent ? parent.width : popup.contentWidth
      spacing: Style.space(10)

      PanelHero {
        title: "Espacios de trabajo"
        meta: root.setups.length === 1
          ? "1 espacio configurado"
          : root.setups.length + " espacios configurados"
        foreground: root.fg
        iconComponent: setupsHeroIcon
      }

      Repeater {
        model: root.setups

        delegate: Column {
          id: setupDelegate
          required property var modelData
          required property int index
          width: panelColumn.width
          spacing: Style.space(2)

          Button {
            width: parent.width
            text: setupDelegate.modelData.name
            iconText: setupDelegate.modelData.icon || "󰍹"
            enabled: !root.busy
            onClicked: root.launchSetup(setupDelegate.index)
          }

          /* Text {
            textFormat: Text.PlainText
            width: parent.width
            leftPadding: Style.space(12)
            text: root.appSummary(setupDelegate.modelData)
            color: Qt.darker(root.fg, 1.6)
            font.family: root.fontFam
            font.pixelSize: Style.font.caption
            wrapMode: Text.WordWrap
          } */
        }
      }

      Text {
        textFormat: Text.PlainText
        width: parent.width
        visible: root.setups.length === 0
        text: "Sin espacios configurados."
        color: Qt.darker(root.fg, 1.6)
        font.family: root.fontFam
        font.pixelSize: Style.font.caption
        wrapMode: Text.WordWrap
      }

      Button {
        width: parent.width
        text: "Gestionar espacios…"
        iconText: "󰒓"
        onClicked: root.openManager()
      }
    }
  }

  Component {
    id: setupsHeroIcon
    Text {
      textFormat: Text.PlainText
      text: "󰀻"
      color: root.fg
      font.family: root.fontFam
      font.pixelSize: Style.font.display
    }
  }
}
