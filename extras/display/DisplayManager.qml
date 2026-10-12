pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import Quickshell.Io
import Caelestia.Components
import Caelestia.Config
import qs.components
import qs.components.controls
import qs.services

ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: Tokens.spacing.medium
    property var displays: []
    property string message: "Leyendo monitores..."
    property bool pendingChange: false
    property int remaining: 0
    property string shellNotice: ""

    function handle(raw) {
        try {
            const data = JSON.parse(raw);
            if (!data.ok) { root.message = data.error || "Operación fallida"; return; }
            if (data.displays !== undefined) root.displays = data.displays;
            if (data.pending !== undefined) root.pendingChange = data.pending;
            if (data.secondsLeft !== undefined) root.remaining = data.secondsLeft;
            root.message = data.message || (data.count + " pantallas detectadas");
        } catch(e) { root.message = "No se pudo leer la respuesta: " + e; }
    }
    function reload() { reader.exec(["python3", "__BACKEND__", "status"]); }
    Process {
        id: reader
        command: ["python3", "__BACKEND__", "status"]
        running: true
        stdout: StdioCollector {}
        onExited: (code, status) => root.handle(stdout.text)
    }
    Process {
        id: writer
        stdout: StdioCollector {}
        onExited: (code, status) => {
            root.handle(stdout.text);
            root.reload();
        }
    }
    Timer {
        interval: 1000
        repeat: true
        running: root.pendingChange
        onTriggered: root.reload()
    }
    StyledText {
        Layout.topMargin: Tokens.spacing.small
        text: "Administrar pantallas"
        font: Tokens.font.body.large
        color: Colours.palette.m3onSurface
    }
    StyledText {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: "Elige resolución y frecuencia entre los modos detectados. La escala es independiente. La posición se conserva."
        font: Tokens.font.body.small
        color: Colours.palette.m3onSurfaceVariant
    }
    StyledText {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: "Para CS2: lo ideal es mantener el escritorio en 1920×1080 y elegir 4:3 dentro del juego. Cambiar el escritorio también afecta a Caelestia y a la disposición de ventanas."
        font: Tokens.font.body.small
        color: Colours.palette.m3onSurfaceVariant
    }
    Repeater {
        model: root.displays
        delegate: ColumnLayout {
            id: card
            required property var modelData
            Layout.fillWidth: true
            spacing: Tokens.spacing.small
            property var modes: modelData.availableModes || []
            property string selectedMode: ""
            property real selectedScale: Number(modelData.scale || 1)
            Component.onCompleted: {
                const m = modelData.width + "x" + modelData.height + "@" + Number(modelData.refreshRate || 60).toFixed(2);
                let idx = modes.findIndex(v => v.startsWith(modelData.width + "x" + modelData.height + "@") && Math.abs(Number(v.split("@")[1].replace("Hz","")) - Number(modelData.refreshRate)) < 0.2);
                selectedMode = idx >= 0 ? modes[idx] : (modes.length ? modes[0] : "");
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: content.implicitHeight + Tokens.padding.large * 2
                radius: Tokens.rounding.large
                color: Colours.tPalette.m3surfaceContainer
                ColumnLayout {
                    id: content
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: Tokens.padding.large
                    spacing: Tokens.spacing.small
                    StyledText {
                        text: card.modelData.name + (card.modelData.focused ? " · activo" : "")
                        font: Tokens.font.body.large
                        color: Colours.palette.m3onSurface
                    }
                    StyledText {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: card.modelData.description || "Monitor sin descripción"
                        font: Tokens.font.body.small
                        color: Colours.palette.m3onSurfaceVariant
                    }
                    StyledText {
                        text: card.modelData.width + " × " + card.modelData.height + " · " + Number(card.modelData.refreshRate).toFixed(2) + " Hz · escala " + card.modelData.scale
                        color: Colours.palette.m3onSurface
                        font: Tokens.font.body.small
                    }
                    StyledText {
                        text: "Posición " + card.modelData.x + ", " + card.modelData.y + " · Rotación " + card.modelData.transform
                        color: Colours.palette.m3onSurfaceVariant
                        font: Tokens.font.label.small
                    }
                    StyledText { text: "Perfiles rápidos"; color: Colours.palette.m3onSurface; font: Tokens.font.body.small }
                    Flow {
                        Layout.fillWidth: true
                        width: parent.width
                        spacing: Tokens.spacing.small
                        visible: card.modelData.name === "DP-2"
                        Repeater {
                            model: [
                                { label: "Nativo · 120 Hz", prefix: "1920x1080@119." },
                                { label: "CS2 · 4:3 · 120 Hz", prefix: "1024x768@119." },
                                { label: "CS2 · FPS · 120 Hz", prefix: "800x600@119." }
                            ]
                            delegate: IconTextButton {
                                required property var modelData
                                text: modelData.label
                                icon: "sports_esports"
                                type: IconTextButton.Tonal
                                disabled: root.pendingChange || writer.running || card.modes.findIndex(v => v.startsWith(modelData.prefix)) < 0
                                onClicked: {
                                    const chosen = card.modes.find(v => v.startsWith(modelData.prefix));
                                    if (chosen) card.selectedMode = chosen;
                                }
                            }
                        }
                    }
                    StyledText {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: "CS2 4:3: 1024×768 es compatible con tu monitor. 1280×960 no aparece entre los modos anunciados y no se ofrecerá. La proporción estirada se configura en el juego o en el escalado de la GPU."
                        visible: card.modelData.name === "DP-2"
                        color: Colours.palette.m3onSurfaceVariant
                        font: Tokens.font.label.small
                    }
                    StyledText { text: "Resolución y frecuencia"; color: Colours.palette.m3onSurface; font: Tokens.font.body.small }
                    Controls.ComboBox {
                        Layout.fillWidth: true
                        model: card.modes
                        currentIndex: Math.max(0, card.modes.indexOf(card.selectedMode))
                        enabled: !root.pendingChange && !writer.running
                        onActivated: index => card.selectedMode = card.modes[index]
                    }
                    StyledText {
                        text: "Escala: " + Math.round(card.selectedScale * 100) + "%"
                        color: Colours.palette.m3onSurface
                        font: Tokens.font.body.small
                    }
                    Controls.Slider {
                        Layout.fillWidth: true
                        from: 0.75
                        to: 2.5
                        stepSize: 0.05
                        value: card.selectedScale
                        enabled: !root.pendingChange && !writer.running
                        onMoved: card.selectedScale = Math.round(value * 20) / 20
                    }
                    IconTextButton {
                        text: "Probar 15 segundos"
                        icon: "timer"
                        type: IconTextButton.Tonal
                        disabled: root.pendingChange || writer.running || !card.selectedMode
                        onClicked: {
                            root.message = "Aplicando prueba temporal...";
                            writer.exec(["python3", "__BACKEND__", "test", "--name", card.modelData.name,
                                         "--mode", card.selectedMode, "--scale", String(card.selectedScale)]);
                        }
                    }
                }
            }
        }
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: confirmations.implicitHeight + Tokens.padding.large * 2
        visible: root.pendingChange
        radius: Tokens.rounding.large
        color: Colours.palette.m3secondaryContainer
        ColumnLayout {
            id: confirmations
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: Tokens.padding.large
            spacing: Tokens.spacing.small
            StyledText {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "¿Mantener cambios? " + root.remaining + " s para restaurar automáticamente."
                color: Colours.palette.m3onSecondaryContainer
                font: Tokens.font.body.small
            }
            RowLayout {
                IconTextButton {
                    text: "Mantener cambios"
                    icon: "check"
                    disabled: writer.running
                    onClicked: writer.exec(["python3", "__BACKEND__", "confirm"])
                }
                IconTextButton {
                    text: "Revertir"
                    icon: "undo"
                    disabled: writer.running
                    onClicked: writer.exec(["python3", "__BACKEND__", "cancel"])
                }
            }
        }
    }
    IconTextButton {
        icon: "refresh"
        text: "Actualizar monitores"
        type: IconTextButton.Tonal
        disabled: reader.running || writer.running
        onClicked: root.reload()
    }
    StyledText {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: "Al confirmar un cambio de resolución, Caelestia se reiniciará automáticamente (solo después de guardar). Durante la prueba de 15 segundos no se reinicia, para mantener disponible la reversión. Si cambia la escala, también se reiniciará después de confirmar."
        font: Tokens.font.body.small
        color: Colours.palette.m3onSurfaceVariant
    }
    StyledText {
        Layout.fillWidth: true
        text: root.message
        wrapMode: Text.WordWrap
        color: Colours.palette.m3onSurfaceVariant
        font: Tokens.font.label.small
    }
}
