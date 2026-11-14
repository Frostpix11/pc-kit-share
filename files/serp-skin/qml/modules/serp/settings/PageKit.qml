import QtQuick
import qs.services
import qs.modules.serp

// serp-skin settings: pc-kit — everything we put over angelOS and how it stands right now
// (services/SerpKit = `kit doctor --json`): the summary and the way into the pc-kit panel
// (panels/SerpKitPanel), where every piece is shown and switched.
SPage {
    id: page
    title: "pc-kit"
    subtitle: "Наши патчи поверх angelOS и система вокруг них"
    Component.onCompleted: SerpKit.touch()

    // the summary card: the state large, the counts, check again
    Rectangle {
        id: card
        property string rowKey: "summary"
        width: parent.width
        height: sum.height + Serp.px(36)
        radius: Serp.radius
        color: Qt.alpha(Serp.surface0, 0.4)
        readonly property color tone: SerpKit.tone(SerpKit.state)
        Row {
            id: sum
            x: Serp.px(18)
            y: Serp.px(18)
            width: parent.width - Serp.px(36)
            spacing: Serp.px(14)
            Rectangle {
                width: Serp.px(48)
                height: width
                radius: Serp.radiusSmall
                color: Qt.alpha(card.tone, 0.16)
                SIcon {
                    anchors.centerIn: parent
                    name: SerpKit.state === "bad" ? "circle-x" : SerpKit.state === "ok" ? "check" : "shield"
                    size: Serp.px(26)
                    color: card.tone
                }
            }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                width: sum.width - Serp.px(48) - again.width - Serp.px(28)
                spacing: Serp.px(3)
                SText {
                    text: SerpKit.error ? SerpKit.error : !SerpKit.known ? "Проверяю…" : SerpKit.bad > 0 ? "Надо поправить: " + SerpKit.bad : SerpKit.warn > 0 ? "Всё работает, замечаний: " + SerpKit.warn : "Всё в порядке"
                    size: Serp.px(16)
                    black: true
                }
                SText {
                    width: parent.width
                    text: "патчи " + SerpKit.patchesOn + "/" + SerpKit.patches.length + (SerpKit.patchesTaken ? " · снято тобой " + SerpKit.patchesTaken : "") + " · система " + SerpKit.systemOk + "/" + SerpKit.system.length + " · проверено " + SerpKit.ago()
                    size: Serp.px(11)
                    color: Serp.subtext0
                }
            }
            SButton {
                id: again
                anchors.verticalCenter: parent.verticalCenter
                enabled: !SerpKit.busy
                Row {
                    spacing: Serp.px(5)
                    SIcon {
                        anchors.verticalCenter: parent.verticalCenter
                        name: "refresh-cw"
                        size: Serp.px(12)
                    }
                    SText {
                        anchors.verticalCenter: parent.verticalCenter
                        text: SerpKit.busy ? "Проверяю…" : "Проверить"
                        size: Serp.px(11.5)
                    }
                }
                onClicked: SerpKit.refresh()
            }
        }
    }

    SetRow {
        rowKey: "open"
        icon: "shield"
        title: "Открыть панель pc-kit"
        desc: "Все патчи, плагины и система: что делает каждый, его правки строка за строкой, история, включить и снять"
        SButton {
            flat: false
            padH: Serp.px(12)
            Row {
                spacing: Serp.px(6)
                SText {
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Открыть"
                    size: Serp.px(11.5)
                    bold: true
                }
                SIcon {
                    anchors.verticalCenter: parent.verticalCenter
                    name: "chevron-right"
                    size: Serp.px(13)
                }
            }
            onClicked: {
                Serp.settingsOpen = false;
                Serp.togglePanel("kit");
            }
        }
    }
    SText {
        width: parent.width
        wrapMode: Text.WordWrap
        elide: Text.ElideNone
        text: "Источник: ~/pc-kit (kit doctor, kit inventory). На баре это щит справа, его правый клик проверяет заново."
        size: Serp.px(11)
        color: Serp.subtext
    }
}
