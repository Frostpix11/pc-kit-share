# Classic (pixel) leftovers under the serp skin — survey 2026-11-13

Scope: shell.qml instances + LazyWindows + modules/*. Excluded: Settings app, Start menu (other
agent), bar / dock / panels / halo / voxtype / toasts (done or in progress), and the dialogs done in
hunks/dialogs.py (session menu + confirm, polkit, Update/MainScreen/Telemetry/SettingsLook/AppsSync
prompts).

How a surface decides its look (the levers):
- `Skin.mac` — apply.py already makes it true under Serp.on (+ Skin colours/fonts → Serp). Anything
  gated on Skin.mac is already modern (AchievementToast, BarPopup).
- `Theme.settingsSkinFor(item)` — the nearest ancestor with a `settingsSkin` property wins. Px*
  that follow it: PxText/Icon/Button/Box/Field/Check/Toggle/Slider/Combo/Progress/Spin/Group/Page/
  TextArea. They do NOT follow it: PxWindow (its own skin: windose/stream/classic only, and it
  *declares* settingsSkin itself, so its children see "classic"), PxMenu*/PxScroll/PxTile/PxPill.
  So option (a) needs an Item *inside* the PxWindow body carrying `settingsSkin: Serp.on ?
  "goldengate" : …`; the frame stays pixel → (a) alone is half a fix.
- `GoldenGate.on` — false under serp (Serp.on is its own skin), so GG-only branches don't fire.
- none — fixed pixel look / own style setting (lock look, Alt+Tab style).

Options: (a) settingsSkin "goldengate" on an inner wrapper; (b) hunk: frame → SGlass under Serp.on
(the SerpDialog pattern: hide frame with opacity 0 / visible false, lay a modules/serp face over it
calling the window's own functions); (c) hide under Serp.on, mount our own window in SerpWindows.

## Top 10 by visibility

| # | Surface | File | Shows | Decides look by | Cheapest |
|---|---|---|---|---|---|
| 1 | Every pixel context menu: desktop right-click, widget menus, a task's WindowMenu, tray, Halo's, notification's | widgets/PxMenu*.qml, services/MenuLook.qml, modules/background/DesktopMenu.qml (Background.qml onMenu) | constantly | MenuLook token table (classic / classicHell); Background: `GoldenGate.on ? MacMenus.openDesktop : menu.openAt` | (b) one hunk in MenuLook: a `serp` token set (Serp colours, flat, no outline/bevel, soft shadow) returned by `classic` under Serp.on; fonts/icons stay pixel → later PxMenuItem hunk for SText/SIcon. Alternative for the desktop only: route onMenu to MacMenus under Serp.on (but apply.py already hunks Background.qml — anchor carefully) |
| 2 | Launcher (Mod+Space) | modules/launcher/Launcher.qml (LazyWindows) | many times a day | none (PxWindow + 30 Px*) | (c) hide its LazyLoader under Serp.on (LazyWindows: next to the clipboard's hunk) and mount a SerpLauncher; the search logic (FileSearch, Vault, ">" cmds) is big → reuse by wrapping Launcher's model/functions, or interim: (b) frame→SGlass + (a) wrapper for the rows |
| 3 | Lock screen | modules/lock/Lock.qml, LockScreen.qml (+ NgoLock/HeavenLock/SaveLock) | every lock / wake | Config.lock.style (ngo/heaven/2004), no skin check | (b) one hunk in LockScreen's Loader `sourceComponent`: `Serp.on ? serpLook : …` with a SerpLock face (clock + SText + a pill field mirroring the hidden HeartPassword, like SerpDialogPolkit does) |
| 4 | Alt+Tab | modules/alttab/AltTabHost.qml (+ AltTabAngel/Ngo/Y2k/Mac/Hell) | many times a day | AltTab.style; `AltTab.mode === "apps"` → AltTabMac | (b) hunk the Loader (line ~148): `Serp.on ? mac : …` — AltTabMac reads Skin/GoldenGate tokens, already serp-coloured via Skin.mac hunks; plus the blurRegion line (`GoldenGate.on` → `|| Serp.on`). Own SerpAltTab later |
| 5 | Mission control | modules/mission/MissionControl.qml | the overview (its key / gesture) | none (PxBox tiles, PxText labels) | (b) hunks on its 4 PxBox frames → Rectangle/SGlass under Serp.on; labels via (a) wrapper |
| 6 | Phone sidebar panel | modules/sidebar/SidebarPanel.qml (PxWindow), SidebarToggles, Phone*.qml | on the heart tab | none (the tab itself is done: apply.py SidebarHost hunks) | (b) hide the PxWindow frame under Serp.on + SGlass behind its body; (a) wrapper for SidebarToggles' Px controls; the 3D phone stays (it is art) |
| 7 | Idle screen / screensaver | modules/idle/IdleScreen.qml | every idle | none (PxText-heavy) | (b) swap its PxText for SText under Serp.on, or (c) a SerpIdle clock face |
| 8 | Screenshot preview + editor, share sheet | modules/capture/ShotPreview.qml, ShotEditor.qml, modules/quickshare/ShareView.qml | every screenshot / share | hardcoded `settingsSkin: "classic"` (ShotEditor:599, ShareView:70) + PxWindow | (a) flip those two lines to `Serp.on ? "goldengate" : "classic"` (two tiny hunks — the inner controls go modern at once), then (b) for the PxWindow frames |
| 9 | Quick Look (Space on a file) | modules/quicklook/QuickLookWindow.qml | often in Strata | none (PxWindow + 3 PxBox) | (b) frame → SGlass, PxBox → Rectangle; (a) wrapper for the text |
| 10 | Corner angel's bubbles / helper | modules/y2k/AngelHelper.qml | game on: tips, pranks | none (34 Px*) | (a) wrapper `settingsSkin` on its bubble + (b) PxBox→SGlass; or leave: it is the game's art |

## The rest (less visible)

| Surface | File | Shows | Decides | Cheapest |
|---|---|---|---|---|
| Snap assist / snap bar | modules/snap/SnapAssistView.qml, SnapBarView.qml | window drag to edge | none (PxBox) | (b) PxBox → rounded Rectangle under Serp.on |
| Project menu (laptop) | modules/laptop/ProjectMenu.qml | on its key (laptop) | none (PxWindow) | (b) SerpDialog pattern (a list of pills) |
| Key cast | modules/keycast/KeyCastOverlay.qml | Mod+Shift+K (LazyWindows comment) | none | (b) PxBox keycaps → Serp pills |
| Game note (new Steam game) | modules/gametune/GameNote.qml | rare | none | (b) SerpDialog pattern |
| Diary book + tab | modules/diary/DiaryBook.qml, DiaryTab.qml | game: diary | none | leave (game art) or (b) tab only |
| Heaven's chest | modules/chest/ChestOverlay.qml | game | none | leave (game art) |
| Convert ring | modules/convert/ConvertRing.qml | file convert | none | (b) PxBox/PxText → Serp |
| Lens search window | modules/lenssearch/LensWindow.qml | Circle-to-search | hardcoded settingsSkin "classic" (71) | (a) flip that line + (b) frame |
| Desktop note editor | modules/desktop/widgets/NoteEditor.qml | note widget edit | none (PxBox) | (b) PxBox → SCard |
| Discord crew menu | modules/desktop/DiscordCrew.qml | in a call | PxMenu | follows #1 |
| Setup wizard | modules/settings/SetupWizard.qml | first run only | own look | leave |
| Boot screen | modules/y2k/BootScreen.qml | login | own art | leave or (c) a plain Serp splash |
| Circle transition, heaven rays, hell fx, screen quake | modules/y2k/* | effects | art | leave |
| Streamer/privacy cast | modules/y2k/StreamerCast.qml, PrivacyCast.qml | stream mode | PxText badges | (a)/(b) small |
| Stream chat runners | modules/streamchat/ChatRunners.qml | stream | PxText | (b) small |
| Novel host | modules/novel/NovelHost.qml | the novel | art | leave |
| Tour overlay | modules/tour/TourOverlay.qml | the tour | PxWindow cards | (b) SerpDialog pattern for its cards |
| Reaper mini-game | modules/reaper/ReaperWindow.qml | game | art | leave |
| Scene editor / Wall studio | modules/sceneeditor, modules/wallstudio | tools | hardcoded settingsSkin "classic" | (a) flip line, frame later |
| Shake cursor, lens overlay, cobweb, chalk | modules/cursor, lens, cobweb, chalk | effects | art | leave |
| Workspace strip/popup, OSD | modules/workspace, modules/osd | — | already hidden under Serp.on (apply.py) | done |
