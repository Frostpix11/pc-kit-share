# the Halo's pill on the islands' line (its float look stands u·4 + the bass glow's room down)
HUNKS = {
    "modules/halo/HaloWindow.qml": [
        ('    readonly property int pillY: glued ? 0 : skin === "float" ? u * 4 + topGap : u + topGap\n',
         '    readonly property int pillY: glued ? 0 : skin === "float" ? (Serp.on ? u * 4 : u * 4 + topGap) : u + topGap  // serp-skin: on the islands\' line\n'),
    ],
}
