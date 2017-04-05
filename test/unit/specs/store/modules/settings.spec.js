import * as api from 'src/api/monitorrent'
import store from 'src/store/modules/settings'
import types from 'src/store/types'
import { expect } from 'chai'
import delay from 'delay'

describe('store/modules/settings', () => {
    const sandbox = sinon.sandbox.create()

    afterEach(() => {
        sandbox.restore()
    })

    describe('mutations', () => {
        const stateBase = {
            loading: true,
            settings: {
                updateInterval: null,
                proxy: {
                    enabled: false,
                    http: null,
                    https: null
                },
                newVersionCheck: {
                    enabled: false,
                    preRelease: false,
                    interval: null
                }
            }
        }

        it('SET_SETTINGS', () => {
            let state = { ...stateBase }
            const settings = {
                updateInterval: 123,
                proxy: {
                    enabled: false,
                    http: 'http://localhost',
                    https: 'https://localhost'
                },
                newVersionCheck: {
                    enabled: true,
                    preRelease: true,
                    interval: 321
                }
            }

            expect(state.loading).to.be.true

            store.mutations[types.SET_SETTINGS](state, settings)

            expect(state.loading).to.be.false
            expect(state.settings).to.eql({...settings})
        })

        it('SET_UPDATE_INTERVAL', () => {
            let state = { ...stateBase }

            expect(state.settings.updateInterval).to.be.null

            store.mutations[types.SET_UPDATE_INTERVAL](state, 123)

            expect(state.settings.updateInterval).to.be.equal(123)
        })

        it('SET_PROXY_ENABLED', () => {
            let state = { ...stateBase }

            expect(state.settings.proxy.enabled).to.be.false

            store.mutations[types.SET_PROXY_ENABLED](state, true)

            expect(state.settings.proxy.enabled).to.be.true
        })

        const proxyTypes = ['http', 'https']

        proxyTypes.forEach(function (type) {
            it(`SET_PROXY(${type})`, () => {
                let state = { ...stateBase }

                expect(state.settings.proxy[type]).to.be.null

                store.mutations[types.SET_PROXY](state, {type, value: 'http://localhost'})

                expect(state.settings.proxy[type]).to.be.equal('http://localhost')
            })
        })

        it('SET_NEW_VERSION_CHECKED_ENABLED', () => {
            let state = { ...stateBase }

            expect(state.settings.newVersionCheck.enabled).to.be.false

            store.mutations[types.SET_NEW_VERSION_CHECKED_ENABLED](state, true)

            expect(state.settings.newVersionCheck.enabled).to.be.true
        })

        it('SET_NEW_VERSION_CHECKED_INCLUDE_PRERELEASE', () => {
            let state = { ...stateBase }

            expect(state.settings.newVersionCheck.preRelease).to.be.false

            store.mutations[types.SET_NEW_VERSION_CHECKED_INCLUDE_PRERELEASE](state, true)

            expect(state.settings.newVersionCheck.preRelease).to.be.true
        })

        it('SET_NEW_VERSION_CHECKED_INTERVAL', () => {
            let state = { ...stateBase }

            expect(state.settings.newVersionCheck.interval).to.be.null

            store.mutations[types.SET_NEW_VERSION_CHECKED_INTERVAL](state, 111)

            expect(state.settings.newVersionCheck.interval).to.be.equal(111)
        })
    })

    describe('actions', () => {
        it('loadSettings should load many settings', async () => {
            const newVersionChecker = {
                enabled: true,
                include_prerelease: true,
                interval: 321
            }

            const getUpdateIntervalStub = sandbox.stub(api.default.settings, 'getUpdateInterval', () => delay(0, 123))
            const proxyIsEnabledStub = sandbox.stub(api.default.settings.proxy, 'isEnabled', () => delay(0, true))
            const proxyGetUrlStub = sandbox.stub(api.default.settings.proxy, 'getUrl', type => delay(0, `${type}://localhost`))
            const getNewVersionCheckerStub = sandbox.stub(api.default.settings, 'getNewVersionChecker', () => delay(0, newVersionChecker))

            const commit = sandbox.spy()

            await store.actions.loadSettings({ commit })

            const expectedSettings = {
                updateInterval: 123,
                proxy: {
                    enabled: true,
                    http: 'http://localhost',
                    https: 'https://localhost'
                },
                newVersionCheck: {
                    enabled: true,
                    preRelease: true,
                    interval: 321
                }
            }

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_SETTINGS, expectedSettings)

            expect(getUpdateIntervalStub).to.have.been.calledOnce
            expect(proxyIsEnabledStub).to.have.been.calledOnce
            expect(proxyGetUrlStub).to.have.been.calledTwice
            expect(proxyGetUrlStub).to.have.been.calledWith('http')
            expect(proxyGetUrlStub).to.have.been.calledWith('https')
            expect(getNewVersionCheckerStub).to.have.been.calledOnce
        })

        it('setUpdateInterval should update settings on backend', async () => {
            const setUpdateIntervalStub = sandbox.stub(api.default.settings, 'setUpdateInterval', () => delay(0, true))

            const commit = sandbox.spy()

            await store.actions.setUpdateInterval({ commit }, 123)

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_UPDATE_INTERVAL, 123)

            expect(setUpdateIntervalStub).to.have.been.calledOnce
        })

        it('setProxyEnabled should update settings on backend', async () => {
            const setProxyEnabledStub = sandbox.stub(api.default.settings.proxy, 'setEnabled', () => delay(0, true))

            const commit = sandbox.spy()

            await store.actions.setProxyEnabled({ commit }, true)

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_PROXY_ENABLED, true)

            expect(setProxyEnabledStub).to.have.been.calledOnce
            expect(setProxyEnabledStub).to.have.been.calledWith(true)
        })

        it('setProxy should update settings on backend', async () => {
            const setProxyStub = sandbox.stub(api.default.settings.proxy, 'setUrl', () => delay(0, true))

            const commit = sandbox.spy()

            await store.actions.setProxy({ commit }, {type: 'http', value: 'http://localhost'})

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_PROXY, {type: 'http', value: 'http://localhost'})

            expect(setProxyStub).to.have.been.calledOnce
        })

        it('setNewVersionCheckEnabled should update settings on backend', async () => {
            const updateNewVersionCheckerStub = sandbox.stub(api.default.settings, 'updateNewVersionChecker', () => delay(0, true))

            const commit = sandbox.spy()

            await store.actions.setNewVersionCheckEnabled({ commit }, true)

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_NEW_VERSION_CHECKED_ENABLED, true)

            expect(updateNewVersionCheckerStub).to.have.been.calledOnce
            expect(updateNewVersionCheckerStub).to.have.been.calledWith({enabled: true})
        })

        it('setNewVersionCheckIncludePrerelease should update settings on backend', async () => {
            const updateNewVersionCheckerStub = sandbox.stub(api.default.settings, 'updateNewVersionChecker', () => delay(0, true))

            const commit = sandbox.spy()

            await store.actions.setNewVersionCheckIncludePrerelease({ commit }, true)

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_NEW_VERSION_CHECKED_INCLUDE_PRERELEASE, true)

            expect(updateNewVersionCheckerStub).to.have.been.calledOnce
            expect(updateNewVersionCheckerStub).to.have.been.calledWith({include_prerelease: true})
        })

        it('setNewVersionCheckInterval should update settings on backend', async () => {
            const updateNewVersionCheckerStub = sandbox.stub(api.default.settings, 'updateNewVersionChecker', () => delay(0, true))

            const commit = sandbox.spy()

            await store.actions.setNewVersionCheckInterval({ commit }, 123)

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_NEW_VERSION_CHECKED_INTERVAL, 123)

            expect(updateNewVersionCheckerStub).to.have.been.calledOnce
            expect(updateNewVersionCheckerStub).to.have.been.calledWith({interval: 123})
        })
    })
})
