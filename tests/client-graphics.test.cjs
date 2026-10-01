'use strict';
// api.graphics: the client API side of plugin graphics passes. The GL side
// (patches/client/GraphicsPasses.mjs) needs a browser; this checks what a
// plugin is allowed to hand over, and that its passes go when it does.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const runtimeModule = import('../patches/client/ExtensionRuntime.mjs');

test('a pass is handed to the bridge checked, and removed when the plugin is disposed', async () => {
    const { createRuntime } = await runtimeModule;
    const runtime = createRuntime();
    const added = [];
    let removed = 0;
    runtime.configure({
        registerPass: (spec, report) => { added.push({ spec, report }); return () => { removed++; }; },
        graphicsSupported: () => true,
        mapLights: () => [{ x: 10, y: 20, height: 3, color: [1, 0.8, 0.5], radius: 4 }],
    });
    const scope = runtime.scope('graphics-plus');
    const enabled = () => true;
    const remove = scope.api.graphics.registerPass({ name: 'Grade', fragment: 'void main() { fragColor = texture(uTexture, vUv); }', enabled, extra: 'ignored' });
    assert.equal(added.length, 1);
    assert.deepEqual(Object.keys(added[0].spec).sort(), ['enabled', 'fragment', 'name', 'uniforms']);
    assert.equal(added[0].spec.name, 'Grade');
    assert.equal(added[0].spec.enabled, enabled);
    assert.equal(added[0].spec.uniforms, undefined);
    assert.equal(typeof added[0].report, 'function');
    assert.equal(scope.api.graphics.supported(), true);
    assert.deepEqual(scope.api.graphics.lights(), [{ x: 10, y: 20, height: 3, color: [1, 0.8, 0.5], radius: 4 }]);
    assert.ok(Object.isFrozen(scope.api.graphics.lights()));

    remove();
    assert.equal(removed, 1, 'the returned function removes it');
    scope.api.graphics.registerPass({ fragment: 'void main() {}' });
    scope.dispose();
    assert.equal(removed, 2, 'disposing the plugin removes what is left');
});

test('renderer features are configured through the bridge and withdrawn with the plugin', async () => {
    const { createRuntime } = await runtimeModule;
    const runtime = createRuntime();
    const set = [];
    let withdrawn = 0;
    runtime.configure({
        configureGraphics: (settings, report) => { set.push(settings); return () => { withdrawn++; }; },
        graphicsFeatures: () => ({ waterReflection: 0 }),
    });
    const scope = runtime.scope('graphics-plus');
    scope.api.graphics.configure({ waterReflection: 0.6 });
    assert.deepEqual(set, [{ waterReflection: 0.6 }]);
    assert.deepEqual(scope.api.graphics.features(), { waterReflection: 0 });
    assert.throws(() => scope.api.graphics.configure('water'), TypeError);
    scope.dispose();
    assert.equal(withdrawn, 1);
});

test('what is not a shader is refused before it reaches the GPU', async () => {
    const { createRuntime } = await runtimeModule;
    const runtime = createRuntime();
    runtime.configure({ registerPass: () => () => {} });
    const { api } = runtime.scope('bad');
    assert.throws(() => api.graphics.registerPass(), TypeError);
    assert.throws(() => api.graphics.registerPass({ fragment: 42 }), TypeError);
    assert.throws(() => api.graphics.registerPass({ fragment: 'no entry point' }), TypeError);
    assert.throws(() => api.graphics.registerPass({ fragment: 'void main(){}' + ' '.repeat(70000) }), TypeError);
});

test('on a client without graphics passes, registering does nothing and says so', async () => {
    const { createRuntime } = await runtimeModule;
    const runtime = createRuntime();
    const { api } = runtime.scope('old-client');
    assert.equal(api.graphics.supported(), false);
    assert.equal(typeof api.graphics.registerPass({ fragment: 'void main() {}' }), 'function');
    assert.deepEqual(api.graphics.lights(), []);
});
