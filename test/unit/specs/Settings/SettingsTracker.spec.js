import Vue from 'vue'
import Vuex from 'vuex'
import _ from 'lodash'
import Deferred from 'es2015-deferred'
import { options } from 'src/store'
import types from 'src/store/types'
import SettingsTracker from 'src/components/Settings/SettingsTracker'

const trackers = [
    {name: 'tracker1.com', form: null},
    {
        name: 'tracker2.com',
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
        name: 'tracker3.com',
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

describe('SettingsTracker.vue', function () {
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
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'tracker1.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.dynamicForm).to.be.not.ok
        expect(vm.$refs.noSettings).to.be.not.ok
        expect(vm.$refs.saveButton).to.be.not.ok
        expect(vm.$refs.checkButton).to.be.not.ok

        expect(actions.loadTracker).have.been.calledOnce
        expect(actions.loadTracker).have.been.calledWith(sinon.match.any, 'tracker1.com')
    })

    it(`should show that tracker doesn't support settings on unknown tracker`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'not-existing-tracker.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.dynamicForm).to.be.not.ok
        expect(vm.$refs.noSettings).to.be.not.ok
        expect(vm.$refs.saveButton).to.be.not.ok
        expect(vm.$refs.checkButton).to.be.not.ok

        expect(actions.loadTracker).have.been.calledOnce

        results.loadTracker.commit(types.SET_TRACKERS, testTrackers)
        results.loadTracker.commit(types.SET_TRACKER_MODEL, {tracker: 'not-existing-tracker.com', model: null, canCheck: false})

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.dynamicForm).to.be.not.ok
        expect(vm.$refs.noSettings).to.be.ok
        expect(vm.$refs.saveButton).to.be.not.ok
        expect(vm.$refs.checkButton).to.be.not.ok
    })

    it(`should show that tracker doesn't support settings on empty trackers`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'not-existing-tracker.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.dynamicForm).to.be.not.ok
        expect(vm.$refs.noSettings).to.be.not.ok
        expect(vm.$refs.saveButton).to.be.not.ok
        expect(vm.$refs.checkButton).to.be.not.ok

        expect(actions.loadTracker).have.been.calledOnce

        results.loadTracker.commit(types.SET_TRACKERS, null)

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.dynamicForm).to.be.not.ok
        expect(vm.$refs.noSettings).to.be.ok
        expect(vm.$refs.saveButton).to.be.not.ok
        expect(vm.$refs.checkButton).to.be.not.ok
    })

    it(`should hide loading after complete tracker loading and show that tracker doesn't support settings`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'tracker1.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok

        expect(actions.loadTracker).have.been.calledOnce

        results.loadTracker.commit(types.SET_TRACKERS, testTrackers)
        results.loadTracker.commit(types.SET_TRACKER_MODEL, {tracker: 'tracker1.com', model: null, canCheck: false})

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.dynamicForm).to.be.not.ok
        expect(vm.$refs.noSettings).to.be.ok
        expect(vm.$refs.saveButton).to.be.not.ok
        expect(vm.$refs.checkButton).to.be.not.ok
    })

    it(`should hide loading after complete tracker loading and show dynamic settings form`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'tracker2.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok

        expect(actions.loadTracker).have.been.calledOnce

        const model = {username: 'username2', password: 'password2'}

        results.loadTracker.commit(types.SET_TRACKERS, testTrackers)
        results.loadTracker.commit(types.SET_TRACKER_MODEL, {tracker: 'tracker2.com', model: model, canCheck: true})

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.dynamicForm).to.be.ok
        expect(vm.$refs.noSettings).to.be.not.ok
        expect(vm.$refs.saveButton).to.be.ok
        expect(vm.$refs.checkButton).to.be.ok
    })

    it(`should hide loading after complete tracker loading and show dynamic settings form and hide check button`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'tracker2.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok

        expect(actions.loadTracker).have.been.calledOnce

        const model = {username: 'username2', password: 'password2'}

        results.loadTracker.commit(types.SET_TRACKERS, testTrackers)
        results.loadTracker.commit(types.SET_TRACKER_MODEL, {tracker: 'tracker2.com', model: model, canCheck: false})

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.dynamicForm).to.be.ok
        expect(vm.$refs.noSettings).to.be.not.ok
        expect(vm.$refs.saveButton).to.be.ok
        expect(vm.$refs.checkButton).to.be.not.ok
    })

    it(`should reset password and enable save button when username text box change`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'tracker2.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok

        expect(actions.loadTracker).have.been.calledOnce

        const model = {username: 'username2', password: 'password2'}

        results.loadTracker.commit(types.SET_TRACKERS, testTrackers)
        results.loadTracker.commit(types.SET_TRACKER_MODEL, {tracker: 'tracker2.com', model: model, canCheck: true})

        await Vue.nextTick()

        expect(vm.$refs.dynamicForm).to.be.ok
        expect(vm.$refs.saveButton.disabled).to.be.true
        expect(vm.model).to.be.eql({...model, password: '******'})

        vm.$refs.dynamicForm.$refs['input-username'].$el.value = 'username3'
        vm.$refs.dynamicForm.$refs['input-username'].onInput()

        await Vue.nextTick()

        expect(vm.$refs.saveButton.disabled).to.be.false
        expect(vm.model).to.be.eql({username: 'username3', password: ''})

        vm.$refs.dynamicForm.$refs['input-username'].$el.value = 'username4'
        vm.$refs.dynamicForm.$refs['input-username'].onInput()

        await Vue.nextTick()
    })

    it(`should reset password and enable save button when password text box focused`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'tracker2.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok

        expect(actions.loadTracker).have.been.calledOnce

        const model = {username: 'username2', password: 'password2'}

        results.loadTracker.commit(types.SET_TRACKERS, testTrackers)
        results.loadTracker.commit(types.SET_TRACKER_MODEL, {tracker: 'tracker2.com', model: model, canCheck: true})

        await Vue.nextTick()

        expect(vm.$refs.dynamicForm).to.be.ok
        expect(vm.$refs.saveButton.disabled).to.be.true
        expect(vm.model).to.be.eql({...model, password: '******'})

        // TODO: don't know why this doesn't work: vm.$refs.dynamicForm.$refs['input-password'].focus()
        vm.$refs.dynamicForm.focused('password')

        await Vue.nextTick()

        expect(vm.$refs.saveButton.disabled).to.be.true
        expect(vm.model).to.be.eql({username: 'username2', password: ''})

        vm.$refs.dynamicForm.focused('password')

        await Vue.nextTick()
    })

    it(`should reset password and enable save button when select changed`, async () => {
        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...SettingsTracker, store})
        const vm = new Constructor({propsData: {tracker: 'tracker3.com'}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok

        expect(actions.loadTracker).have.been.calledOnce

        const model = {username: 'username2', password: 'password2', quality: '720p'}

        results.loadTracker.commit(types.SET_TRACKERS, testTrackers)
        results.loadTracker.commit(types.SET_TRACKER_MODEL, {tracker: 'tracker3.com', model: model, canCheck: true})

        await Vue.nextTick()

        expect(vm.$refs.dynamicForm).to.be.ok
        expect(vm.$refs.saveButton.disabled).to.be.true
        expect(vm.model).to.be.eql({...model, password: '******', quality: '720p'})

        const qualityInput = vm.$refs.dynamicForm.$refs['input-quality']
        qualityInput.setTextAndValue('1080p')
        qualityInput.changeValue('1080p')

        await Vue.nextTick()

        expect(vm.$refs.saveButton.disabled).to.be.false
        expect(vm.model).to.be.eql({username: 'username2', password: '', quality: '1080p'})
    })
})
