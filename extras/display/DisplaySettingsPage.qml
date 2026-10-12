pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Caelestia.Config
import qs.modules.nexus.common
import qs.modules.nexus.pages

PageBase {
    id: root
    title: "Displays"

    // PageBase ya incluye VerticalFadeFlickable y usa implicitHeight del contenido.
    ColumnLayout {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        width: root.cappedWidth
        spacing: Tokens.spacing.medium

        DisplayManager {
            Layout.fillWidth: true
        }
    }
}
