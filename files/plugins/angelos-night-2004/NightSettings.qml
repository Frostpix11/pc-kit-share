import QtQuick
import Quickshell
import qs.config
import qs.services
import qs.widgets

Column {
    id: root
    property var plugin
    width: parent ? parent.width : 440
    spacing: Skin.spacing

    // what the wallpaper shows now: by the clock, or by hand from here (services/SceneDebug, not saved)
    readonly property bool byHand: SceneDebug.hour >= 0 || SceneDebug.eventOn
    function show() {
        Quickshell.execDetached(["qs", "-c", "angelos", "ipc", "call", "angelos-night-2004", "select"]);
    }
    function hour(h) {
        show();
        SceneDebug.eventOn = false;
        SceneDebug.hour = h;
    }
    function meteor(age, speed) {
        show();
        SceneDebug.speed = speed;
        SceneDebug.playing = true;
        SceneDebug.jump(age);
        SceneDebug.hour = 4;
    }

    PxGroup {
        title: "Точка сохранения — ночь"
        icon: "image"
        width: parent.width
        PxText {
            width: parent.width
            text: "Временная ночь для обоев автора «Точка сохранения» на его же движке: сумерки 20–22, ночь, рассвет 6–8, звёзды, метеор в 04:00: подлёт, падение за дом, вспышка, тряска, взрыв, осколки и звуки. Своё время суток для обоев: Настройки → Обои → Время суток."
            wrapMode: Text.Wrap
        }
        PxButton {
            text: "Показать эти обои"
            onClicked: root.show()
        }
    }
    PxGroup {
        title: "Посмотреть сейчас"
        icon: "eye"
        width: parent.width
        PxText {
            width: parent.width
            text: root.byHand ? "Сейчас время выставлено вручную — верните часы, когда насмотритесь (после перезапуска angelOS часы вернутся сами)." : "Сейчас обои идут по часам."
            wrapMode: Text.Wrap
        }
        Flow {
            width: parent.width
            spacing: Skin.spacing
            PxButton { text: "День"; onClicked: root.hour(13) }
            PxButton { text: "Сумерки"; onClicked: root.hour(20.6) }
            PxButton { text: "Ночь"; onClicked: root.hour(2) }
            PxButton { text: "Рассвет"; onClicked: root.hour(6.6) }
        }
        Flow {
            width: parent.width
            spacing: Skin.spacing
            PxButton { text: "Метеор целиком (2 мин)"; onClicked: root.meteor(-2400, 20) }
            PxButton { text: "Падение сейчас"; onClicked: root.meteor(-12, 1) }
            PxButton { text: "После удара"; onClicked: root.meteor(150, 1) }
        }
        PxButton {
            text: "Вернуть часы"
            enabled: root.byHand
            onClicked: SceneDebug.reset()
        }
    }
    // the author's own "Time of day" and "Wallpaper sounds" (catalog/Wallpaper.qml scene-time and
    // scene-sounds) are not in the settings tree yet; the same keys, for this wallpaper
    readonly property string here: Config.home + "/Pictures/AngelOS-Night/reference/neutral-656x376.png"
    readonly property bool soundsOn: Wallpapers.own(here, "sceneSounds") !== false
    PxGroup {
        title: "Время суток"
        icon: "image"
        width: parent.width
        PxText {
            width: parent.width
            text: "«По часам»: с 20:00 сумерки, с 22:00 ночь, к 8 утра снова день."
            wrapMode: Text.Wrap
        }
        PxSegmented {
            model: [{"label": "По часам", "value": "auto"}, {"label": "Всегда день", "value": "day"}, {"label": "Всегда ночь", "value": "night"}]
            currentValue: Wallpapers.own(root.here, "sceneTime")
            onActivated: v => Wallpapers.setOwn(root.here, "sceneTime", v)
        }
    }
    PxGroup {
        title: "Звуки обоев"
        icon: "volume"
        width: parent.width
        PxToggle {
            text: "Звуки обоев"
            checked: root.soundsOn
            onToggled: c => Wallpapers.setOwn(root.here, "sceneSounds", c)
        }
        PxText {
            visible: root.soundsOn
            text: "Воздух — сверчки ночью, птицы днём, листва на ветру"
        }
        PxSlider {
            visible: root.soundsOn
            width: parent.width
            from: 0
            to: 100
            stepSize: 5
            suffix: " %"
            value: Wallpapers.own(root.here, "sceneSoundAir")
            onMoved: v => Wallpapers.setOwn(root.here, "sceneSoundAir", Math.round(v))
        }
        PxText {
            visible: root.soundsOn
            text: "События — метеор: гул, свист, удар, огонь, сирены (поверх музыки и окон)"
        }
        PxSlider {
            visible: root.soundsOn
            width: parent.width
            from: 0
            to: 100
            stepSize: 5
            suffix: " %"
            value: Wallpapers.own(root.here, "sceneSoundEvent")
            onMoved: v => Wallpapers.setOwn(root.here, "sceneSoundEvent", Math.round(v))
        }
        PxText {
            visible: root.soundsOn
            // angelOS c4795df: one «air while a program sounds» instead of desk / window
            text: "Когда звучит программа (музыка, звонок, браузер, игра в окне) — сколько воздуха остаётся; видео и полный экран — воздух молчит"
        }
        PxSlider {
            visible: root.soundsOn
            width: parent.width
            from: 0
            to: 100
            stepSize: 5
            suffix: " %"
            value: Config.wallpaper.sceneDuck
            onMoved: v => Config.wallpaper.sceneDuck = Math.round(v)
        }
        PxToggle {
            text: "Волна под бас — от каждого удара музыки из телевизора расходится волна"
            checked: Wallpapers.own(root.here, "sceneBass") === true
            onToggled: c => Wallpapers.setOwn(root.here, "sceneBass", c)
        }
    }
    PxGroup {
        title: "Удаление"
        icon: "trash"
        width: parent.width
        PxText {
            width: parent.width
            text: "Когда автор выпустит свою ночь — отключите плагин (вернутся прежние обои), затем удалите папку ~/.config/angelos/plugins/angelos-night-2004 и ссылку ~/Pictures/AngelOS-Night."
            wrapMode: Text.Wrap
        }
    }
}
