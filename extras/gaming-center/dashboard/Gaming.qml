pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC
import Quickshell
import Quickshell.Io
import Caelestia.Config
import qs.components

Item {
    id: root
    implicitWidth: 735
    implicitHeight: 410

    property var gamingData: ({ games: [], steamRunning: false, gamescopeRunning: false, hyprlandAvailable: false, dualsense: { devices: [] } })
    property string lastError: ""
    property bool loading: false
    property string updatedAt: ""
    property string actionMessage: ""

    readonly property string helper: `${Quickshell.shellDir}/scripts/liox_gaming_status.py`
    readonly property var games: Array.isArray(gamingData.games) ? gamingData.games : []
    readonly property var pad: gamingData.dualsense?.devices?.length ? gamingData.dualsense.devices[0] : null
    readonly property real battery: root.pad ? Math.max(0, Math.min(100, Number(root.pad.battery) || 0)) : 0

    // Los acentos siguen el tema de Caelestia y por tanto los cambios de Waywallen.
    // La tinta y las superficies mantienen contraste alto aun con paletas muy claras.
    readonly property color accent: Colours.palette.m3primary
    readonly property color heading: "#F4F8FC"
    readonly property color bodyText: "#D7E3EC"
    readonly property color secondaryText: "#B5C8D7"
    readonly property color cardBg: Qt.rgba(0.115 + accent.r * 0.035, 0.145 + accent.g * 0.035, 0.175 + accent.b * 0.035, 0.98)
    readonly property color innerBg: Qt.rgba(0.15 + accent.r * 0.045, 0.18 + accent.g * 0.045, 0.22 + accent.b * 0.045, 0.98)
    readonly property color lineColor: Qt.rgba(0.60, 0.75, 0.87, 0.28)
    readonly property color accentLine: Qt.rgba(accent.r, accent.g, accent.b, 0.78)
    readonly property color accentSoft: Qt.rgba(accent.r, accent.g, accent.b, 0.22)
    readonly property color success: "#91F1BD"

    function focusGame(pid): void {
        const n = Number(pid);
        if (!Number.isSafeInteger(n) || n <= 0) return;
        focusProcess.exec(["hyprctl", "dispatch", "focuswindow", "pid:" + n]);
    }

    function openSteam(): void {
        Qt.openUrlExternally("steam://open/games");
    }

    function refresh(): void {
        if (scan.running) return;
        root.loading = true;
        scan.exec(["python3", root.helper, "status"]);
    }

    Process {
        id: scan
        onRunningChanged: {
            if (!running) root.loading = false;
        }
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const parsed = JSON.parse(text);
                    if (!Array.isArray(parsed.games)) throw new Error("Formato de juegos inválido");
                    root.gamingData = parsed;
                    root.lastError = "";
                    root.updatedAt = Qt.formatTime(new Date(), "hh:mm:ss");
                } catch (e) {
                    root.lastError = String(e);
                }
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim()) root.lastError = text.trim().slice(0, 160);
            }
        }
    }

    Process { id: focusProcess }

    Timer {
        interval: 3000
        repeat: true
        running: root.visible
        triggeredOnStart: true
        onTriggered: root.refresh()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 7
        spacing: Tokens.spacing.medium

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                StyledText {
                    text: "Gaming Center"
                    font.pixelSize: 22
                    font.bold: true
                    color: root.heading
                }
                StyledText {
                    text: root.games.length === 0 ? "Tu centro de juegos y periféricos" : root.games.length + (root.games.length === 1 ? " juego abierto" : " juegos abiertos")
                    font.pixelSize: 12
                    color: root.secondaryText
                }
            }

            Rectangle {
                radius: 12
                color: root.innerBg
                border.color: root.lineColor
                border.width: 1
                implicitWidth: hyprStatus.implicitWidth + 23
                implicitHeight: 31
                StyledText {
                    id: hyprStatus
                    anchors.centerIn: parent
                    text: root.gamingData.hyprlandAvailable ? "● Hyprland listo" : "● Sin Hyprland"
                    color: root.gamingData.hyprlandAvailable ? root.success : "#FFC0C0"
                    font.pixelSize: 12
                    font.bold: true
                }
            }

            Rectangle {
                radius: 12
                implicitHeight: 32
                implicitWidth: refreshLabel.implicitWidth + 25
                color: refreshMouse.containsMouse ? root.innerBg : root.cardBg
                border.color: root.accentLine
                border.width: 1
                StyledText {
                    id: refreshLabel
                    anchors.centerIn: parent
                    text: root.loading ? "↻ Consultando" : "↻ Actualizar"
                    color: root.heading
                    font.pixelSize: 12
                    font.bold: true
                }
                MouseArea {
                    id: refreshMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.refresh()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 0
                Layout.preferredWidth: 2
                Layout.horizontalStretchFactor: 2
                radius: 18
                color: root.cardBg
                border.color: root.lineColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 17
                    spacing: 12

                    RowLayout {
                        Layout.fillWidth: true
                        StyledText { text: "JUEGOS ACTIVOS"; color: root.bodyText; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
                        Rectangle {
                            radius: 9
                            color: root.accentSoft
                            implicitWidth: countText.implicitWidth + 16
                            implicitHeight: 24
                            StyledText { id: countText; anchors.centerIn: parent; text: String(root.games.length); color: root.heading; font.pixelSize: 12; font.bold: true }
                        }
                    }
                    Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.lineColor }

                    // Centrado geométrico del estado vacío: no depende de espaciadores.
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: root.games.length === 0

                        ColumnLayout {
                            id: emptyState
                            anchors.centerIn: parent
                            width: Math.min(parent.width, 390)
                            spacing: 10

                            StyledText {
                                text: "🎮"
                                font.pixelSize: 36
                                Layout.alignment: Qt.AlignHCenter
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: "Sin juegos en este momento"
                                font.pixelSize: 18
                                font.bold: true
                                color: root.heading
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: "Abre Steam o inicia un juego para verlo aquí"
                                font.pixelSize: 13
                                color: root.secondaryText
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                            }
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                implicitWidth: emptySteamLabel.implicitWidth + 36
                                implicitHeight: 34
                                radius: 10
                                color: root.innerBg
                                border.color: root.accentLine
                                StyledText {
                                    id: emptySteamLabel
                                    anchors.centerIn: parent
                                    text: "↗ Abrir biblioteca Steam"
                                    color: root.heading
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.openSteam()
                                }
                            }
                        }
                    }

                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: root.games.length > 0
                        id: gamesScroll
                        clip: true
                        interactive: contentHeight > height
                        boundsBehavior: Flickable.StopAtBounds
                        flickableDirection: Flickable.VerticalFlick
                        contentWidth: width
                        contentHeight: gameItems.implicitHeight

                        QQC.ScrollBar.vertical: QQC.ScrollBar {
                            policy: gamesScroll.contentHeight > gamesScroll.height ? QQC.ScrollBar.AsNeeded : QQC.ScrollBar.AlwaysOff
                            width: 5
                        }

                        ColumnLayout {
                            id: gameItems
                            width: parent.width
                            spacing: 8
                            Repeater {
                                model: root.games
                                delegate: Rectangle {
                                    id: gameTile
                                    required property var modelData
                                    readonly property string appClass: String(modelData.class ?? "")
                                    readonly property string steamId: appClass.startsWith("steam_app_") ? appClass.slice(10) : ""
                                    readonly property string platformLabel: {
                                        const p = String(modelData.platform || "").trim();
                                        if (p) return p;
                                        if (steamId) return "Steam";
                                        if (appClass === "eden") return "Eden";
                                        if (appClass === "dolphin-emu") return "Dolphin";
                                        return "Juego";
                                    }
                                    Layout.fillWidth: true
                                    implicitHeight: gameInfo.implicitHeight + 29
                                    radius: 14
                                    color: root.innerBg
                                    border.width: 1
                                    border.color: root.accentSoft
                                    Rectangle {
                                        anchors.left: parent.left
                                        anchors.top: parent.top
                                        anchors.bottom: parent.bottom
                                        width: 4
                                        radius: 2
                                        color: root.accent
                                    }
                                    ColumnLayout {
                                        id: gameInfo
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.leftMargin: 16
                                        anchors.rightMargin: 12
                                        spacing: 7
                                        StyledText {
                                            Layout.fillWidth: true
                                            text: String(gameTile.modelData.title || "Juego sin nombre").trim()
                                            font.pixelSize: 21
                                            font.bold: true
                                            color: root.heading
                                            elide: Text.ElideRight
                                        }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 6
                                            Rectangle {
                                                implicitWidth: platformText.implicitWidth + 18
                                                implicitHeight: 23
                                                radius: 8
                                                color: root.accentSoft
                                                border.color: root.accentLine
                                                StyledText {
                                                    id: platformText
                                                    anchors.centerIn: parent
                                                    text: gameTile.platformLabel
                                                    color: root.heading
                                                    font.pixelSize: 11
                                                    font.bold: true
                                                }
                                            }
                                            Item { Layout.fillWidth: true }
                                        }
                                        StyledText {
                                            Layout.fillWidth: true
                                            text: "Workspace " + (gameTile.modelData.workspace ?? "?") + (gameTile.modelData.focused ? "  ·  En primer plano" : "  ·  En segundo plano")
                                            font.pixelSize: 13
                                            color: root.bodyText
                                            elide: Text.ElideRight
                                        }
                                        StyledText {
                                            Layout.fillWidth: true
                                            text: (gameTile.steamId ? "STEAM APP ID  ·  " + gameTile.steamId : gameTile.appClass) + "  ·  PID " + gameTile.modelData.pid
                                            font.pixelSize: 12
                                            font.bold: true
                                            color: root.secondaryText
                                            elide: Text.ElideRight
                                        }
                                        Rectangle {
                                            Layout.alignment: Qt.AlignHCenter
                                            implicitWidth: focusLabel.implicitWidth + 32
                                            implicitHeight: 32
                                            radius: 10
                                            color: focusMouse.containsMouse ? root.accentSoft : root.cardBg
                                            border.color: root.accentLine
                                            StyledText { id: focusLabel; anchors.centerIn: parent; text: "↗ Ir a la ventana del juego"; color: root.heading; font.pixelSize: 12; font.bold: true }
                                            MouseArea { id: focusMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.focusGame(gameTile.modelData.pid) }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 8
                        Rectangle {
                            radius: 9
                            color: root.innerBg
                            border.color: root.lineColor
                            border.width: 1
                            implicitWidth: steamText.implicitWidth + 20
                            implicitHeight: 29
                            StyledText {
                                id: steamText
                                anchors.centerIn: parent
                                text: root.gamingData.steamRunning ? "● Steam activo" : "○ Steam inactivo"
                                font.pixelSize: 12
                                font.bold: true
                                color: root.gamingData.steamRunning ? root.success : root.secondaryText
                            }
                        }
                        Rectangle {
                            radius: 9
                            color: root.innerBg
                            border.color: root.lineColor
                            border.width: 1
                            implicitWidth: scopeText.implicitWidth + 20
                            implicitHeight: 29
                            StyledText {
                                id: scopeText
                                anchors.centerIn: parent
                                text: root.gamingData.gamescopeRunning ? "● Gamescope activo" : "○ Gamescope inactivo"
                                font.pixelSize: 12
                                color: root.gamingData.gamescopeRunning ? root.success : root.secondaryText
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.horizontalStretchFactor: 1
                Layout.minimumWidth: 0
                Layout.fillHeight: true
                radius: 18
                color: root.cardBg
                border.width: 1
                border.color: root.lineColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 8
                    StyledText {
                        Layout.fillWidth: true
                        text: "MANDO CONECTADO"
                        color: root.secondaryText
                        font.pixelSize: 12
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.lineColor }
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        ColumnLayout {
                            anchors.centerIn: parent
                            width: Math.min(parent.width, 220)
                            spacing: 9
                            StyledText {
                                Layout.fillWidth: true
                                text: root.pad ? String(root.pad.name) : "Sin DualSense"
                                font.pixelSize: 21
                                font.bold: true
                                color: root.heading
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: root.pad ? String(root.pad.transport) + " · " + String(root.pad.status) : "Conecta tu mando"
                                font.pixelSize: 12
                                color: root.secondaryText
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                            Item { Layout.preferredHeight: 10 }
                            StyledText {
                                Layout.fillWidth: true
                                text: root.pad ? root.battery + "%" : "—"
                                color: root.heading
                                font.pixelSize: 33
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: "BATERÍA"
                                color: root.secondaryText
                                font.pixelSize: 11
                                horizontalAlignment: Text.AlignHCenter
                            }
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                Layout.preferredWidth: Math.min(170, parent.width)
                                implicitHeight: 12
                                radius: 6
                                color: root.innerBg
                                Rectangle {
                                    x: 1
                                    y: 1
                                    width: Math.max(0, (parent.width - 2) * root.battery / 100)
                                    height: parent.height - 2
                                    radius: 5
                                    color: root.accent
                                }
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: "Solo lectura · RGB intacto"
                                color: root.secondaryText
                                font.pixelSize: 11
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            StyledText {
                text: root.updatedAt ? "Última lectura: " + root.updatedAt : "Esperando primera lectura"
                color: root.secondaryText
                font.pixelSize: 12
            }
            Item { Layout.fillWidth: true }
            StyledText {
                text: "Steam · Gamescope · DualSense | Sin cambios RGB"
                color: root.secondaryText
                font.pixelSize: 12
            }
        }

        StyledText {
            visible: root.lastError !== ""
            Layout.fillWidth: true
            text: "Detector: " + root.lastError
            color: "#FFC6C6"
            font.pixelSize: 12
            elide: Text.ElideRight
        }
    }
}
