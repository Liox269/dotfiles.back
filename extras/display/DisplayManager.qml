pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell.Io
import Caelestia.Components
import Caelestia.Config
import qs.components
import qs.components.controls
import qs.services
import qs.modules.nexus.common

ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: Tokens.spacing.small
    property var displays: []
    property string message: "Leyendo monitores de Hyprland..."

    Process {
        id: monitorReader
        command: ["python3", "__BACKEND__", "status"]
        running: true
        stdout: StdioCollector {}
        onExited: (code, status) => {
            try {
                const data = JSON.parse(stdout.text);
                if (!data.ok) {
                    root.message = data.error || "No se pudieron leer los monitores";
                    return;
                }
                root.displays = data.displays;
                root.message = data.count + " monitor(es) detectado(s). Solo lectura: no se aplican cambios.";
            } catch (err) {
                root.message = "Error de lectura: " + err;
            }
        }
    }

    StyledText {
        Layout.topMargin: Tokens.spacing.large
        text: "Display Manager"
        font: Tokens.font.body.large
        color: Colours.light ? "#162333" : "#EDF4F9"
    }
    StyledText {
        Layout.fillWidth: true
        text: "Resolución, frecuencia, posición y escala detectadas por Hyprland Lua."
        wrapMode: Text.WordWrap
        font: Tokens.font.body.small
        color: Colours.light ? "#42566B" : "#C5D1DB"
    }

    Repeater {
        model: root.displays
        delegate: ColumnLayout {
            id: displayCard
            required property var modelData
            Layout.fillWidth: true
            spacing: Tokens.spacing.extraSmall

            StyledText {
                text: displayCard.modelData.name + (displayCard.modelData.focused ? " · activo" : "")
                font: Tokens.font.body.large
                color: Colours.light ? "#162333" : "#EDF4F9"
            }
            StyledText {
                Layout.fillWidth: true
                text: displayCard.modelData.description
                wrapMode: Text.WordWrap
                font: Tokens.font.body.small
                color: Colours.light ? "#42566B" : "#C5D1DB"
            }
            StyledText {
                Layout.fillWidth: true
                text: displayCard.modelData.width + " × " + displayCard.modelData.height + " @ " + Number(displayCard.modelData.refreshRate).toFixed(2) + " Hz"
                font: Tokens.font.body.small
                color: Colours.light ? "#162333" : "#EDF4F9"
            }
            StyledText {
                Layout.fillWidth: true
                text: "Escala " + displayCard.modelData.scale + " · Posición " + displayCard.modelData.x + ", " + displayCard.modelData.y + " · Rotación " + displayCard.modelData.transform
                font: Tokens.font.body.small
                color: Colours.light ? "#42566B" : "#C5D1DB"
            }
            StyledText {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Modos: " + (displayCard.modelData.availableModes.length ? displayCard.modelData.availableModes.join(" · ") : "No informados")
                font: Tokens.font.label.small
                color: Colours.light ? "#42566B" : "#C5D1DB"
            }
        }
    }

    IconTextButton {
        icon: "refresh"
        text: "Actualizar monitores"
        type: IconTextButton.Tonal
        disabled: monitorReader.running
        onClicked: monitorReader.exec(["python3", "__BACKEND__", "status"])
    }
    StyledText {
        Layout.fillWidth: true
        text: root.message
        wrapMode: Text.WordWrap
        font: Tokens.font.label.small
        color: Colours.light ? "#42566B" : "#C5D1DB"
    }
}
