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

Flickable {
    id: root

    property int opacityPercent: 45
    property int cornerRadius: 6
    property int innerGaps: 17
    property int outerGaps: 10
    property bool animationsEnabled: true
    property bool blurEnabled: false
    property string resultText: "Cargando valores de Hyprland..."

    Layout.fillWidth: true
    // Limitar la altura dentro de WallpaperAndStyle para que los botones nunca queden fuera.
    implicitHeight: Math.min(470, form.implicitHeight + 12)
    clip: true
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds
    contentWidth: width
    contentHeight: form.implicitHeight + 12

    function updateFromOutput(raw) {
        try {
            const response = JSON.parse(raw);
            if (!response.ok) {
                resultText = response.error || "Error al leer la configuración";
                return;
            }
            if (response.values) {
                opacityPercent = response.values.opacity;
                cornerRadius = response.values.rounding;
                innerGaps = response.values.gaps;
                outerGaps = response.values.gapsOut;
                animationsEnabled = response.values.animations;
                blurEnabled = response.values.blur;
            }
            resultText = "Valores leídos de Hyprland. Los cambios solo se aplican al pulsar Aplicar.";
        } catch (err) {
            resultText = "No se pudo interpretar la respuesta: " + err;
        }
    }

    Process {
        id: readProcess
        command: ["python3", "__CONTROLLER__", "status"]
        running: true
        stdout: StdioCollector {}
        onExited: (code, status) => root.updateFromOutput(stdout.text)
    }

    Process {
        id: editProcess
        stdout: StdioCollector {}
        onExited: (code, status) => {
            root.updateFromOutput(stdout.text);
            if (code === 0)
                readProcess.exec(["python3", "__CONTROLLER__", "status"]);
        }
    }

    ColumnLayout {
        id: form
        width: root.width
        spacing: Tokens.spacing.small

    StyledText {
        Layout.topMargin: Tokens.spacing.large
        color: "#E7EEF5"
        text: "Advanced appearance"
        font: Tokens.font.body.large
    }

    StyledText {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: "Ventanas de Hyprland. No modifica el wallpaper de Caelestia ni los colores de Waywallen."
        font: Tokens.font.body.small
        color: "#C5D1DB"
    }

    SliderRow {
        icon: "opacity"
        label: "Opacidad de ventanas"
        valueLabel: root.opacityPercent + "%"
        value: root.opacityPercent / 100
        onMoved: v => root.opacityPercent = Math.max(25, Math.min(100, Math.round(v * 100)))
    }

    ToggleRow {
        text: "Desenfoque de ventanas"
        subtext: "Blur de Hyprland (desactivarlo no afecta al wallpaper)"
        checked: root.blurEnabled
        onToggled: checked => root.blurEnabled = checked
    }

    SliderRow {
        icon: "rounded_corner"
        label: "Esquinas redondeadas"
        valueLabel: root.cornerRadius + " px"
        value: root.cornerRadius / 40
        onMoved: v => root.cornerRadius = Math.round(v * 40)
    }

    SliderRow {
        icon: "space_dashboard"
        label: "Espacio entre ventanas"
        valueLabel: root.innerGaps + " px"
        value: root.innerGaps / 40
        onMoved: v => root.innerGaps = Math.round(v * 40)
    }

    SliderRow {
        icon: "view_week"
        label: "Espacio exterior"
        valueLabel: root.outerGaps + " px"
        value: root.outerGaps / 40
        onMoved: v => root.outerGaps = Math.round(v * 40)
    }

    ToggleRow {
        text: "Animaciones de Hyprland"
        subtext: "Conserva las curvas y velocidades personalizadas"
        checked: root.animationsEnabled
        onToggled: checked => root.animationsEnabled = checked
    }

    StyledText {
        Layout.fillWidth: true
        text: "Cambios reversibles con respaldo de variables.lua y animations.lua."
        wrapMode: Text.WordWrap
        color: "#C5D1DB"
        font: Tokens.font.body.small
    }

    ButtonRow {
        Layout.fillWidth: true
        spacing: Tokens.spacing.small

        IconTextButton {
            icon: "tune"
            text: "Valores elegidos"
            type: IconTextButton.Tonal
            onClicked: {
                root.opacityPercent = 45;
                root.blurEnabled = false;
                root.cornerRadius = 6;
                root.innerGaps = 17;
                root.outerGaps = 10;
                root.animationsEnabled = true;
                root.resultText = "Valores preparados; pulsa Aplicar para guardarlos.";
            }
        }
        IconTextButton {
            icon: "check"
            text: "Aplicar"
            type: IconTextButton.Tonal
            disabled: editProcess.running || readProcess.running
            onClicked: {
                root.resultText = "Aplicando...";
                editProcess.exec(["python3", "__CONTROLLER__", "apply",
                    "--opacity", String(root.opacityPercent),
                    "--blur", root.blurEnabled ? "on" : "off",
                    "--rounding", String(root.cornerRadius),
                    "--gaps", String(root.innerGaps),
                    "--gaps-out", String(root.outerGaps),
                    "--animations", root.animationsEnabled ? "on" : "off"]);
            }
        }
        IconTextButton {
            icon: "history"
            text: "Restaurar"
            type: IconTextButton.Tonal
            disabled: editProcess.running || readProcess.running
            onClicked: {
                root.resultText = "Restaurando...";
                editProcess.exec(["python3", "__CONTROLLER__", "restore"]);
            }
        }
    }

    StyledText {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: root.resultText
        font: Tokens.font.label.small
        color: "#C5D1DB"
    }
    }
}
