// Graphics+: one full-screen pass (api.graphics.registerPass) doing several
// effects, each set by its own setting, 0 meaning off. One pass rather than
// one per effect, so turning more of them on costs a few shader instructions,
// not another trip over the whole screen.
//
// What the pass is handed (the frame, its depth, the map's sun and its lights
// already on screen) is described in docs/MODDING.md, "client/".

const FRAGMENT = `
uniform float uGrade, uGlow, uFog, uTonemap, uVignette, uTilt, uFringe, uRain;

vec3 aces(vec3 x) {
	return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

vec3 frame(vec2 uv) {
	if (uFringe <= 0.0) return texture(uTexture, uv).rgb;
	vec2 shift = (uv - 0.5) * uFringe * 0.006;
	return vec3(texture(uTexture, uv + shift).r, texture(uTexture, uv).g, texture(uTexture, uv - shift).b);
}

void main() {
	vec2 uv = vUv;
	vec3 color = frame(uv);

	// Tilt-shift: blur grows away from a band across the middle.
	if (uTilt > 0.0) {
		float amount = smoothstep(0.12, 0.5, abs(uv.y - 0.5)) * uTilt;
		if (amount > 0.001) {
			vec2 stride = amount * 5.0 / uResolution;
			vec3 sum = color;
			float weight = 1.0;
			for (int i = -3; i <= 3; i++) {
				for (int j = -3; j <= 3; j++) {
					if (i == 0 && j == 0) continue;
					sum += frame(uv + vec2(float(i), float(j)) * stride);
					weight += 1.0;
				}
			}
			color = sum / weight;
		}
	}

	// Distance haze, in the map's own light colour.
	if (uFog > 0.0 && uHasDepth) {
		float far = linearDepth(uv);
		float amount = smoothstep(uNear + 60.0, uFar * 0.3, far) * uFog;
		vec3 haze = clamp(mix(uAmbient, uSunColor, 0.5) * 0.85 + 0.15, 0.0, 1.0);
		color = mix(color, haze, clamp(amount, 0.0, 0.8));
	}

	// Lamp glow: a soft additive halo at each of the map's lights.
	if (uGlow > 0.0) {
		vec3 glow = vec3(0.0);
		float aspect = uResolution.x / uResolution.y;
		for (int i = 0; i < ${32}; i++) {
			if (i >= uLightCount) break;
			vec4 light = uLights[i];
			vec2 offset = (uv - light.xy) * vec2(aspect, 1.0);
			float radius = max(light.z, 0.01);
			glow += uLightColors[i] * exp(-dot(offset, offset) / (radius * radius * 0.3));
		}
		color += glow * uGlow * 0.55;
	}

	// Grading: warm light, cool shadows, a little contrast.
	if (uGrade > 0.0) {
		float luma = dot(color, vec3(0.299, 0.587, 0.114));
		vec3 warm = color * vec3(1.08, 1.0, 0.86);
		vec3 cool = color * vec3(0.9, 0.97, 1.1);
		vec3 graded = mix(cool, warm, smoothstep(0.15, 0.85, luma));
		graded = (graded - 0.5) * 1.08 + 0.5;
		color = mix(color, graded, uGrade);
	}

	if (uTonemap > 0.0) color = mix(color, aces(color * 1.1), uTonemap);

	if (uVignette > 0.0) color *= mix(1.0, smoothstep(0.9, 0.3, length(uv - 0.5)), uVignette);

	// Rain: thin streaks falling at a slight slant, and a duller sky.
	if (uRain > 0.0) {
		vec2 p = uv * vec2(90.0, 3.0);
		p.y += uTime * 5.0;
		p.x += p.y * 0.12;
		float streak = step(0.986, hash(floor(p))) * smoothstep(0.0, 0.25, fract(p.y)) * (1.0 - fract(p.y));
		color = mix(color, vec3(0.82, 0.88, 0.95), streak * 0.4 * uRain);
		color *= mix(1.0, 0.86, uRain);
	}

	fragColor = vec4(color, 1.0);
}
`;

const SETTINGS = ['grade', 'glow', 'fog', 'tonemap', 'vignette', 'tilt_shift', 'fringe', 'rain'];
const UNIFORM = { grade: 'uGrade', glow: 'uGlow', fog: 'uFog', tonemap: 'uTonemap', vignette: 'uVignette', tilt_shift: 'uTilt', fringe: 'uFringe', rain: 'uRain' };

// A setting as 0..1. Read defensively: a missing or odd value is off.
export function strengths(parameters = {}) {
    const out = {};
    for (const key of SETTINGS) {
        const value = Number(parameters?.[key]);
        out[UNIFORM[key]] = Number.isFinite(value) ? Math.min(Math.max(value, 0), 100) / 100 : 0;
    }
    return out;
}

export default function init(parameters, api) {
    if (api?.version !== 1) throw new Error('graphics-plus requires client API 1');
    if (!api.graphics?.supported()) {
        console.warn('[graphics-plus] this client cannot run graphics passes; nothing to do');
        return;
    }
    const uniforms = strengths(parameters);
    const anything = Object.values(uniforms).some(value => value > 0);
    // Reflections, grass and shadows are drawn inside the renderer, not in
    // this pass.
    const percent = key => { const value = Number(parameters?.[key]); return Number.isFinite(value) ? Math.min(Math.max(value, 0), 100) / 100 : 0; };
    const features = {};
    if (percent('water') > 0) features.waterReflection = percent('water');
    if (percent('shadows') > 0) features.shadows = percent('shadows');
    if (percent('grass') > 0) features.grass = {
        // Ground textures whose names say grass: the client's are Korean
        // (풀 grass, 잔디 lawn, 초원 meadow, 들판 field), a mod's often English.
        textures: ['풀', '잔디', '초원', '들판', 'grass'],
        density: percent('grass'),
        wind: 0.3,
    };
    if (Object.keys(features).length) api.graphics.configure(features);
    api.graphics.registerPass({
        name: 'Graphics+',
        fragment: FRAGMENT,
        enabled: () => anything,
        uniforms: () => uniforms,
    });
}
