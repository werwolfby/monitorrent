import Vue from 'vue'
import Vuex from 'vuex'
import _ from 'lodash'
import Deferred from 'es2015-deferred'
import { options } from 'src/store'
import types from 'src/store/types'
import router from 'src/router'
import SettingsTrackers from 'src/components/Settings/SettingsTrackers'

const trackers = [
    {name: 'lostfilm.tv', form: null},
    {
        name: 'rutor.info',
        form: [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 50
                }, {
                    type: 'password',
                    model: 'password',
                    label: 'Password',
                    flex: 50
                }]
            }
        ]
    },
    {
        name: 'rutracker.org',
        form: [
            {
                type: 'row',
                content: [
                    {
                        type: 'text',
                        model: 'username',
                        label: 'Username',
                        flex: 45
                    },
                    {
                        type: 'password',
                        model: 'password',
                        label: 'Password',
                        flex: 45
                    },
                    {
                        type: 'select',
                        model: 'quality',
                        label: 'Quality',
                        options: [
                            'SD',
                            '720p',
                            '1080p'
                        ],
                        flex: 10
                    }
                ]
            }
        ]
    }
]

describe('SettingsTrackers.vue', function () {
    const sandbox = sinon.sandbox.create()

    let testOptions
    let testTrackers
    let actions
    let results

    beforeEach(function () {
        testOptions = _.cloneDeep(options)
        testTrackers = trackers.map(t => _.cloneDeep(t))

        results = {}
        testOptions.modules.trackers.actions = actions = {}
        for (const key of Object.keys(options.modules.trackers.actions)) {
            actions[key] = function ({ commit }, params) {
                const result = results[key] = new Deferred()
                result.commit = commit
                result.params = params
                return result
            }
            sandbox.spy(actions, key)
        }
    })

    afterEach(function () {
        sandbox.restore()
    })

    it(`should show loading`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTrackers, store})
        const vm = new Constructor({propsData: {tracker: 'tracker1.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.list).to.be.not.ok

        expect(actions.loadTrackers).have.been.calledOnce
        expect(actions.loadTrackers).have.been.calledWith(sinon.match.any)
    })

    it(`should show trackers list`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTrackers, router, store})
        const vm = new Constructor({propsData: {tracker: 'tracker1.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.list).to.be.not.ok

        expect(actions.loadTrackers).have.been.calledOnce
        expect(actions.loadTrackers).have.been.calledWith(sinon.match.any)

        results.loadTrackers.commit(types.SET_TRACKERS, testTrackers)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.list).to.be.ok

        expect(vm.$refs.link).to.have.lengthOf(3)
    })
})
