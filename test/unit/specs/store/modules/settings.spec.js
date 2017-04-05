import * as api from 'src/api/monitorrent'
import store from 'src/store/modules/settings'
import types from 'src/store/types'
import { expect } from 'chai'
import fetchMock from 'fetch-mock'
import Deferred from 'es2015-deferred'
import delay from 'delay'

describe('store/modules/settings', () => {
    const sandbox = sinon.sandbox.create()

    afterEach(() => {
        sandbox.restore()
        fetchMock.restore()
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
})
