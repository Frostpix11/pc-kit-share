import QtQuick
import qs.services

// serp-skin: a card on a panel — surface0, the skin's radius, a hair of a line
Rectangle {
    radius: Serp.radius
    color: Serp.surface0
    border.width: 1
    border.color: Serp.line
}
