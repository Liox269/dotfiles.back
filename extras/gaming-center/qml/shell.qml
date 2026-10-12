pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

ShellRoot {
    id: app
    property var state: ({games: [], steamRunning: false, gamescopeRunning: false, dualsense: {devices: []}, hyprlandAvailable: false})
    property string error: ""
    property bool busy: false
    property string backend: Quickshell.shellDir + "/../status.py"

    function refresh(): void {
        if (!reader.running) reader.exec(["python3", backend, "status"])
    }

    Process {
        id: reader
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (!data || !Array.isArray(data.games)) throw new Error("Respuesta incorrecta");
                    app.state = data;
                    app.error = "";
                } catch (e) {
                    app.error = "No se pudo analizar el estado: " + String(e);
                }
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim().length > 0) app.error = text.trim().slice(0, 280);
            }
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0 && !app.error) app.error = "El detector terminó con error (" + exitCode + ")";
        }
    }
    Timer {
        interval: 5000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: app.refresh()
    }

    FloatingWindow {
        id: window
        title: "Liox Gaming Center"
        visible: true
        color: "#171720"
        implicitWidth: 380
        implicitHeight: 440

        Rectangle {
            anchors.fill: parent
            color: "#171720"
            radius: 16
            border.width: 1
            border.color: "#444053"
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                Text { text: "◈  Gaming Center"; color: "#E6DDF7"; font.pixelSize: 20; font.weight: Font.DemiBold; Layout.fillWidth: true }
                Rectangle {
                    implicitWidth: 64; implicitHeight: 30; radius: 10
                    color: reloadArea.pressed ? "#56506c" : "#302B3F"
                    Text { anchors.centerIn: parent; color: "#DCC7FF"; text: "↻ Actualizar"; font.pixelSize: 10 }
                    MouseArea { id: reloadArea; anchors.fill: parent; onClicked: app.refresh() }
                }
            }
            Text {
                Layout.fillWidth: true
                text: app.state.hyprlandAvailable ? "Hyprland conectado" : "Hyprland no disponible"
                color: app.state.hyprlandAvailable ? "#A6D9C8" : "#FFB7B7"
                font.pixelSize: 12
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: gameColumn.implicitHeight + 28
                radius: 12
                color: "#242230"
                ColumnLayout {
                    id: gameColumn
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14 }
                    spacing: 8
                    Text { text: "JUEGOS DETECTADOS"; color: "#B9A8D0"; font.pixelSize: 11; font.weight: Font.DemiBold }
                    Text {
                        visible: app.state.games.length === 0
                        text: "No se detectan juegos abiertos"
                        color: "#D2C9E1"
                        font.pixelSize: 13
                    }
                    Repeater {
                        model: app.state.games
                        delegate: ColumnLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            Text { text: modelData.title.trim(); color: "#F2EBFF"; font.pixelSize: 16; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
                            Text { text: (modelData.focused ? "En foco · " : "") + "Workspace " + (modelData.workspace || "?") + " · " + modelData.class; color: "#B9A8D0"; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                        }
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 64
                radius: 12
                color: "#242230"
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    Text { text: "Steam"; color: "#F2EBFF"; font.pixelSize: 14; Layout.fillWidth: true }
                    Text { text: app.state.steamRunning ? "Activo" : "Inactivo"; color: app.state.steamRunning ? "#A6D9C8" : "#B9A8D0"; font.pixelSize: 12 }
                    Text { text: "   Gamescope"; color: "#F2EBFF"; font.pixelSize: 14 }
                    Text { text: app.state.gamescopeRunning ? "Sí" : "No"; color: "#B9A8D0"; font.pixelSize: 12 }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 87
                radius: 12
                color: "#242230"
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 7
                    Text { text: "DUALSENSE · SOLO LECTURA"; color: "#B9A8D0"; font.pixelSize: 11; font.weight: Font.DemiBold }
                    Text {
                        readonly property var ds: app.state.dualsense && app.state.dualsense.devices && app.state.dualsense.devices.length > 0 ? app.state.dualsense.devices[0] : null
                        text: ds ? (ds.name + " · " + ds.transport + " · " + (ds.battery === null ? "Batería desconocida" : ds.battery + "%")) : "Mando desconectado"
                        color: "#F2EBFF"; font.pixelSize: 13
                    }
                }
            }
            Text {
                visible: app.error.length > 0
                text: app.error
                color: "#FFB7B7"
                font.pixelSize: 11
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Item { Layout.fillHeight: true }
            Text {
                text: "Datos cada 5 s · No modifica Steam ni luces RGB"
                color: "#8F889D"; font.pixelSize: 11
            }
        }
    }
}
