# Plan: angelOS Settings in the serp look + a serp Start launcher (agent survey, 2026-11-13)

## Settings ("serp" view on the Mac path)
- Kit (Cat*) is data only; CatalogPage draws with Px* widgets which pick their look from parents' `settingsSkin`
  (Theme.settingsSkinFor). A NEW settingsSkin value breaks them (falls into windose/stream) → serp view keeps
  settingsSkin "goldengate" and re-colours GoldenGate tokens under Serp.on.
- SettingsView.qml hunks: L129 skins list +"serp"; L130 mac: (goldengate||serp) && !hellDress; L150 viewId serp;
  L153 fluent += serp; L976-978 load views/SerpView.qml; L916 macFrame colour transparent for serp.
- SettingsWindow.qml L31 blur radius under serp.
- GoldenGate.qml: ONLY L54-57 (label/secondary/tertiary/separator) and L61-63 (groupBg/controlBg/hoverBg) are free
  (L21 skin-morph, L58-60 mac-tint). Optional L29 dark from Serp.base lightness (light palettes!).
- Optional: PxText L21 / PxField L108 font → Serp.font (PxText needs import qs.services); PxGroup L101/L111 and
  SettingRow L69-73 hard-coded rgba → Serp tokens.
- New file views/SerpView.qml (~500 lines): MacView contract (view, searchSlot, resultsSlot, pageSlot,
  sidebarVisible, navKey) + Guide sidebar (sliding accent plate, sections → pages), header ‹ › crumbs undo.
  DON'T patch MacView (pc-kit mac-settings-lights owns L82-84).
- Phase B: CatalogPage Entry hunk → modules/serp/settings/CatRow.qml (SetRow + STog/SChoice/SSlide/SNumber).

## Start (serp launcher)
- StartOverlay.qml hunks (NEVER L141-180: codex-fixes spotlight-blur patch): L9 import serp; L34 style serp;
  L36 spot += serp; L40 prefs serp→spotlight; L250 map "serp": serpComp + Component{SerpLauncher{}}; opt L237 y
  under islands.
- SerpLauncher.qml (~600): MacSpotlight logic (searchAll, plugin providers Instantiator L82-140, files mode,
  key() L263-317) + Serpantinum Launcher look: 600 wide, tabs Apps/Files/Emoji (SSwitch), 44px rows, sliding
  plate, footer user + power (StartItems.power), `>` run command, `?` web. EmojiData.js from the reference (AGPL,
  local only).
