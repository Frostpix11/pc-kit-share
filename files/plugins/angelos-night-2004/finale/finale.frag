#version 440
// angelos-night-2004: the meteor's last seconds over the wallpaper. Everything is light added
// (alpha 0 out: the compositor adds it to the picture under the window): the plunging meteor and
// its shock ring only in the sky (the scene's nearer layers, `front`, cover them), the flash
// everywhere, nearest the impact the brightest, in a few steps dithered on the art-pixel grid.
// On a night of another colour (SceneWall.fires) the art goes through that night's ramp, as the
// author's scene_event.frag does with his sprites.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 canvas;       // art px of the whole canvas
    vec2 origin;       // the impact, art px
    float flash;       // 0..1
    vec4 flashColor;
    float tint;        // 1: tonight's colours instead of the art's own
    vec4 deep;
    vec4 mid;
    vec4 hot;
};
layout(binding = 1) uniform sampler2D art;
layout(binding = 2) uniform sampler2D front;

float bayer(vec2 p) {
    ivec2 i = ivec2(mod(p, 4.0));
    int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
    return (float(m[i.y * 4 + i.x]) + 0.5) / 16.0;
}

// a lightness through tonight's ramp, in eight flat steps (the author's)
vec3 ramp(float l) {
    l = floor(clamp(l, 0.0, 1.0) * 8.0 + 0.5) / 8.0;
    return l < 0.5 ? mix(deep.rgb, mid.rgb, l * 2.0) : mix(mid.rgb, hot.rgb, l * 2.0 - 1.0);
}

void main() {
    vec2 px = floor(qt_TexCoord0 * canvas);
    vec2 uv = (px + 0.5) / canvas;
    float sky = 1.0 - texture(front, uv).r;
    vec3 a = texture(art, uv).rgb;
    float al = max(a.r, max(a.g, a.b));
    vec3 add = (tint > 0.5 ? ramp(al) * al : a) * sky;
    if (flash > 0.0) {
        float d = length(px - origin) / 220.0;
        float l = flash * (0.28 + 0.72 * exp(-d * d * 3.0)) * (0.55 + 0.45 * sky);
        l = floor(l * 5.0 + bayer(px)) / 5.0;
        add += flashColor.rgb * l;
    }
    fragColor = vec4(add, 0.0) * qt_Opacity;
}
