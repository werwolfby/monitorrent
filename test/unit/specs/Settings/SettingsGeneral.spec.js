import Vue from 'vue'
import Vuex from 'vuex'
import _ from 'lodash'
import Deferred from 'es2015-deferred'
import delay from 'delay'
import { options } from 'src/store'
import types from 'src/store/types'
import SettingsGeneral from 'src/components/Settings/SettingsGeneral'

describe('SettingsGeneral.vue', function () {
    const settings = {
        updateInterval: 123,
        proxy: {
            enabled: false,
            http: 'http://login:password@proxy.local:8888',
            https: 'https://login:password@proxy.local:8888'
        },
        newVersionCheck: {
            enabled: false,
            preRelease: true,
            interval: 321
        }
    }

    const sandbox = sinon.sandbox.create()

    let loadSettingsDeferred
    let setUpdateIntervalDeferred
    let setProxyEnabledDeferred
    let setProxyDeferred
    let setNewVersionCheckEnabledDeferred
    let setNewVersionCheckIncludePrereleaseDeferred
    let setNewVersionCheckIntervalDeferred
    let testOptions

    beforeEach(function () {
        loadSettingsDeferred = new Deferred()
        setUpdateIntervalDeferred = new Deferred()
        setProxyEnabledDeferred = new Deferred()
        setProxyDeferred = new Deferred()
        setNewVersionCheckEnabledDeferred = new Deferred()
        setNewVersionCheckIncludePrereleaseDeferred = new Deferred()
        setNewVersionCheckIntervalDeferred = new Deferred()

        const actions = {
            loadSettings ({ commit }) {
                loadSettingsDeferred.commit = commit
                return loadSettingsDeferred.promise
            },
            setUpdateInterval ({ commit }, value) {
                setUpdateIntervalDeferred.commit = commit
                setUpdateIntervalDeferred.value = value
                return setUpdateIntervalDeferred.promise
            },
            setProxyEnabled ({ commit }, value) {
                setProxyEnabledDeferred.commit = commit
                setProxyEnabledDeferred.value = value
                return setProxyEnabledDeferred.promise
            },
            setProxy ({ commit }, params) {
                setProxyDeferred.commit = commit
                setProxyDeferred.params = params
                return setProxyDeferred.promise
            },
            setNewVersionCheckEnabled ({ commit }, value) {
                setNewVersionCheckEnabledDeferred.commit = commit
                setNewVersionCheckEnabledDeferred.value = value
                return setNewVersionCheckEnabledDeferred.promise
            },
            setNewVersionCheckIncludePrerelease ({ commit }, value) {
                setNewVersionCheckIncludePrereleaseDeferred.commit = commit
                setNewVersionCheckIncludePrereleaseDeferred.value = value
                return setNewVersionCheckIncludePrereleaseDeferred.promise
            },
            setNewVersionCheckInterval ({ commit }, value) {
                setNewVersionCheckIntervalDeferred.commit = commit
                setNewVersionCheckIntervalDeferred.value = value
                return setNewVersionCheckIntervalDeferred.promise
            }
        }

        Object.keys(actions).forEach(key => {
            sandbox.spy(actions, key)
        })

        testOptions = _.cloneDeep(options)
        testOptions.modules.settings.actions = actions
    })

    afterEach(function () {
        sandbox.restore()
    })

    it('should show loading', async function () {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsGeneral, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

        expect(vm.$refs.loading).to.be.ok
    })

    it('should display collapsed controls', async function () {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsGeneral, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

        expect(vm.$refs.loading).to.be.ok

        const resultSettings = _.cloneDeep(settings)
        resultSettings.updateInterval = 123
        resultSettings.proxy.enabled = false
        resultSettings.newVersionCheck.enabled = false

        loadSettingsDeferred.resolve()
        loadSettingsDeferred.commit(types.SET_SETTINGS, resultSettings)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok

        expect(vm.$refs.updateIntervalInput).to.be.ok
        expect(vm.$refs.updateIntervalInput.value).to.be.equal(123)

        expect(vm.$refs.proxyEnableSwitch).to.be.ok
        expect(vm.$refs.proxyEnableSwitch.value).to.be.false

        expect(vm.$refs.newVersionCheckSwitch).to.be.ok
        expect(vm.$refs.newVersionCheckSwitch.value).to.be.false

        expect(vm.$refs.httpProxyInput).to.be.not.ok
        expect(vm.$refs.httpsProxyInput).to.be.not.ok
        expect(vm.$refs.newVersionCheckPrereleaseCheckbox).to.be.not.ok
        expect(vm.$refs.newVersionCheckIntervalInput).to.be.not.ok
    })

    it('should display expanded controls', async function () {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsGeneral, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

        expect(vm.$refs.loading).to.be.ok

        const resultSettings = {
            updateInterval: 123,
            proxy: {
                enabled: true,
                http: 'http://login:password@proxy.local:8888',
                https: 'https://login:password@proxy.local:8888'
            },
            newVersionCheck: {
                enabled: true,
                preRelease: true,
                interval: 321
            }
        }

        loadSettingsDeferred.resolve()
        loadSettingsDeferred.commit(types.SET_SETTINGS, resultSettings)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok

        expect(vm.$refs.updateIntervalInput).to.be.ok
        expect(vm.$refs.updateIntervalInput.value).to.be.equal(123)

        expect(vm.$refs.proxyEnableSwitch).to.be.ok
        expect(vm.$refs.proxyEnableSwitch.value).to.be.true

        expect(vm.$refs.httpProxyInput).to.be.ok
        expect(vm.$refs.httpProxyInput.value).to.be.equal('http://login:password@proxy.local:8888')

        expect(vm.$refs.httpsProxyInput).to.be.ok
        expect(vm.$refs.httpsProxyInput.value).to.be.equal('https://login:password@proxy.local:8888')

        expect(vm.$refs.newVersionCheckSwitch).to.be.ok
        expect(vm.$refs.newVersionCheckSwitch.value).to.be.true

        expect(vm.$refs.newVersionCheckPrereleaseCheckbox).to.be.ok
        expect(vm.$refs.newVersionCheckPrereleaseCheckbox.value).to.be.true

        expect(vm.$refs.newVersionCheckIntervalInput).to.be.ok
        expect(vm.$refs.newVersionCheckIntervalInput.value).to.be.equal(321)
    })

    it('should display proxy controls on enable proxy click', async function () {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsGeneral, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

        expect(vm.$refs.loading).to.be.ok

        const resultSettings = {
            updateInterval: 123,
            proxy: {
                enabled: false,
                http: 'http://login:password@proxy.local:8888',
                https: 'https://login:password@proxy.local:8888'
            },
            newVersionCheck: {
                enabled: false,
                preRelease: true,
                interval: 321
            }
        }

        loadSettingsDeferred.resolve()
        loadSettingsDeferred.commit(types.SET_SETTINGS, resultSettings)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok

        expect(vm.$refs.updateIntervalInput).to.be.ok
        expect(vm.$refs.updateIntervalInput.value).to.be.equal(123)

        expect(vm.$refs.proxyEnableSwitch).to.be.ok
        expect(vm.$refs.proxyEnableSwitch.value).to.be.false

        expect(vm.$refs.httpProxyInput).to.be.not.ok
        expect(vm.$refs.httpsProxyInput).to.be.not.ok

        expect(testOptions.modules.settings.actions.setProxyEnabled).have.not.been.called

        vm.$refs.proxyEnableSwitch.changeState(true, {})

        await Vue.nextTick()

        setProxyEnabledDeferred.resolve()
        setProxyEnabledDeferred.commit(types.SET_PROXY_ENABLED, setProxyEnabledDeferred.value)

        expect(testOptions.modules.settings.actions.setProxyEnabled).have.been.calledOnce

        await Vue.nextTick()

        expect(vm.$refs.httpProxyInput).to.be.ok
        expect(vm.$refs.httpProxyInput.value).to.be.equal('http://login:password@proxy.local:8888')

        expect(vm.$refs.httpsProxyInput).to.be.ok
        expect(vm.$refs.httpsProxyInput.value).to.be.equal('https://login:password@proxy.local:8888')
    })

    it('should display new version check controls on enable new version check click', async function () {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsGeneral, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

        expect(vm.$refs.loading).to.be.ok

        const resultSettings = {
            updateInterval: 123,
            proxy: {
                enabled: false,
                http: 'http://login:password@proxy.local:8888',
                https: 'https://login:password@proxy.local:8888'
            },
            newVersionCheck: {
                enabled: false,
                preRelease: true,
                interval: 321
            }
        }

        loadSettingsDeferred.resolve()
        loadSettingsDeferred.commit(types.SET_SETTINGS, resultSettings)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok

        expect(vm.$refs.updateIntervalInput).to.be.ok
        expect(vm.$refs.updateIntervalInput.value).to.be.equal(123)

        expect(vm.$refs.newVersionCheckSwitch).to.be.ok
        expect(vm.$refs.newVersionCheckSwitch.value).to.be.false

        expect(vm.$refs.newVersionCheckPrereleaseCheckbox).to.be.not.ok
        expect(vm.$refs.newVersionCheckIntervalInput).to.be.not.ok

        expect(testOptions.modules.settings.actions.setNewVersionCheckEnabled).have.not.been.called

        vm.$refs.newVersionCheckSwitch.changeState(true, {})

        await Vue.nextTick()

        setNewVersionCheckEnabledDeferred.resolve()
        setNewVersionCheckEnabledDeferred.commit(types.SET_NEW_VERSION_CHECKED_ENABLED, setNewVersionCheckEnabledDeferred.value)

        expect(testOptions.modules.settings.actions.setNewVersionCheckEnabled).have.been.calledOnce

        await Vue.nextTick()

        expect(vm.$refs.newVersionCheckPrereleaseCheckbox).to.be.ok
        expect(vm.$refs.newVersionCheckPrereleaseCheckbox.value).to.be.true

        expect(vm.$refs.newVersionCheckIntervalInput).to.be.ok
        expect(vm.$refs.newVersionCheckIntervalInput.value).to.be.equal(321)
    })

    it('should change update interval', async function () {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsGeneral, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

        expect(vm.$refs.loading).to.be.ok

        const resultSettings = {
            updateInterval: 123,
            proxy: {
                enabled: false,
                http: 'http://login:password@proxy.local:8888',
                https: 'https://login:password@proxy.local:8888'
            },
            newVersionCheck: {
                enabled: false,
                preRelease: true,
                interval: 321
            }
        }

        loadSettingsDeferred.resolve()
        loadSettingsDeferred.commit(types.SET_SETTINGS, resultSettings)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok

        expect(vm.$refs.updateIntervalInput).to.be.ok
        expect(vm.$refs.updateIntervalInput.value).to.be.equal(123)

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.setUpdateInterval).have.not.been.called

        vm.$refs.updateIntervalInput.$el.value = '124'
        vm.$refs.updateIntervalInput.onInput()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.setUpdateInterval).have.not.been.called

        await delay(510)

        expect(testOptions.modules.settings.actions.setUpdateInterval).have.been.calledOnce
        expect(testOptions.modules.settings.actions.setUpdateInterval).have.been.calledWith(sinon.match.any, '124')
    })

    it('should change update interval debounced', async function () {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsGeneral, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

        expect(vm.$refs.loading).to.be.ok

        const resultSettings = {
            updateInterval: 123,
            proxy: {
                enabled: false,
                http: 'http://login:password@proxy.local:8888',
                https: 'https://login:password@proxy.local:8888'
            },
            newVersionCheck: {
                enabled: false,
                preRelease: true,
                interval: 321
            }
        }

        loadSettingsDeferred.resolve()
        loadSettingsDeferred.commit(types.SET_SETTINGS, resultSettings)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok

        expect(vm.$refs.updateIntervalInput).to.be.ok
        expect(vm.$refs.updateIntervalInput.value).to.be.equal(123)

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.setUpdateInterval).have.not.been.called

        async function updateIntervalValue (value, delayTimeout = 100) {
            vm.$refs.updateIntervalInput.$el.value = value
            vm.$refs.updateIntervalInput.onInput()

            await delay(delayTimeout)
        }

        await updateIntervalValue('124', 30)
        await updateIntervalValue('125', 100)
        await updateIntervalValue('126', 210)
        await updateIntervalValue('127', 70)

        expect(testOptions.modules.settings.actions.setUpdateInterval).have.not.been.called

        await delay(510)

        expect(testOptions.modules.settings.actions.setUpdateInterval).have.been.calledOnce
        expect(testOptions.modules.settings.actions.setUpdateInterval).have.been.calledWith(sinon.match.any, '127')
    })

    const proxies = ['http', 'https']

    proxies.forEach(function (proxy) {
        it(`should change update ${proxy} proxy debounced`, async function () {
            const store = new Vuex.Store(testOptions)
            const Constructor = Vue.extend({...SettingsGeneral, store})
            const vm = new Constructor().$mount()

            await Vue.nextTick()

            expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

            expect(vm.$refs.loading).to.be.ok

            const resultSettings = {
                updateInterval: 123,
                proxy: {
                    enabled: true,
                    http: null,
                    https: null
                },
                newVersionCheck: {
                    enabled: false,
                    preRelease: true,
                    interval: 321
                }
            }

            loadSettingsDeferred.resolve()
            loadSettingsDeferred.commit(types.SET_SETTINGS, resultSettings)

            await Vue.nextTick()

            expect(vm.$refs.loading).to.be.not.ok

            const input = vm.$refs[proxy + 'ProxyInput']

            expect(input).to.be.ok
            expect(input.value).to.be.null

            await Vue.nextTick()

            expect(testOptions.modules.settings.actions.setProxy).have.not.been.called

            async function updateIntervalValue (value, delayTimeout = 100) {
                input.$el.value = value
                input.onInput()

                await delay(delayTimeout)
            }

            await updateIntervalValue('http://localhost', 30)
            await updateIntervalValue('http://localhost:8888', 100)
            await updateIntervalValue('http://login:localhost:8888', 210)
            await updateIntervalValue('http://login:password@localhost:8888', 70)

            expect(testOptions.modules.settings.actions.setProxy).have.not.been.called

            await delay(510)

            expect(testOptions.modules.settings.actions.setProxy).have.been.calledOnce
            expect(testOptions.modules.settings.actions.setProxy).have.been.calledWith(sinon.match.any, { type: proxy, value: 'http://login:password@localhost:8888' })
        })
    })

    it('should change update interval debounced', async function () {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsGeneral, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.loadSettings).have.been.calledOnce

        expect(vm.$refs.loading).to.be.ok

        const resultSettings = {
            updateInterval: 123,
            proxy: {
                enabled: false,
                http: 'http://login:password@proxy.local:8888',
                https: 'https://login:password@proxy.local:8888'
            },
            newVersionCheck: {
                enabled: true,
                preRelease: true,
                interval: 321
            }
        }

        loadSettingsDeferred.resolve()
        loadSettingsDeferred.commit(types.SET_SETTINGS, resultSettings)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok

        const input = vm.$refs.newVersionCheckIntervalInput

        expect(input).to.be.ok
        expect(input.value).to.be.equal(321)

        await Vue.nextTick()

        expect(testOptions.modules.settings.actions.setNewVersionCheckInterval).have.not.been.called

        async function updateIntervalValue (value, delayTimeout = 100) {
            input.$el.value = value
            input.onInput()

            await delay(delayTimeout)
        }

        await updateIntervalValue('322', 30)
        await updateIntervalValue('323', 100)
        await updateIntervalValue('324', 210)
        await updateIntervalValue('325', 70)

        expect(testOptions.modules.settings.actions.setNewVersionCheckInterval).have.not.been.called

        await delay(510)

        expect(testOptions.modules.settings.actions.setNewVersionCheckInterval).have.been.calledOnce
        expect(testOptions.modules.settings.actions.setNewVersionCheckInterval).have.been.calledWith(sinon.match.any, '325')
    })
})
