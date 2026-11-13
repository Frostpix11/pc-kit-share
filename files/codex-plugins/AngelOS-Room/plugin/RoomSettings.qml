import QtQuick
import qs.config
import qs.services
import qs.widgets

Column {
    id: root
    property var plugin
    readonly property string mode: plugin ? plugin.get("mode", "night") : "night"
    width: parent ? parent.width : 440
    spacing: Skin.spacing
    PxGroup {
        title: "Комната — день и ночь"
        icon: "image"
        width: parent.width
        PxText {
            width: parent.width
            text: "Летнее утро автора и ночная комната с серафимом за окном. В режиме «Авто» обои следуют дневному и ночному режиму angelOS."
            wrapMode: Text.Wrap
        }
        Flow {
            width: parent.width
            spacing: Skin.spacing
            Repeater {
                model: [{key: "day", label: "День"}, {key: "night", label: "Ночь"}, {key: "auto", label: "Авто"}]
                PxButton {
                    required property var modelData
                    text: modelData.label
                    checked: root.mode === modelData.key
                    onClicked: root.plugin.set("mode", modelData.key)
                }
            }
        }
        PxText {
            width: parent.width
            text: "Движение облаков, шторы и растений, параллакс и глубина виджетов используют настройки обоев angelOS. Отключение плагина возвращает предыдущие обои."
            wrapMode: Text.Wrap
        }
    }
}
