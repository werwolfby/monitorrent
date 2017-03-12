import Vue from 'vue'
import Vuex from 'vuex'
import _ from 'lodash'
import * as api from 'src/api/monitorrent'
import { options } from 'src/store'
import types from 'src/store/types'
import Topics from 'src/components/Topics/Topics'

describe('Topics.vue', () => {
    const topics = [
        {display_name: 'Zeta', tracker: 'lostfilm.tv', last_update: '2017-02-13T23:00:00+00:00'},
        {display_name: 'Yota', tracker: 'lostfilm.tv', last_update: null}
    ]

    const logs = {
        count: 1,
        data: [
            {finish_time: '2017-02-14T01:35:47+00:00'}
        ]
    }

    let watchExecuteStub
    let testOptions
    beforeEach(function () {
        testOptions = _.cloneDeep(options)
        // we have to stub watchExecute, because
        // original implementation run 'infinite`
        watchExecuteStub = sandbox.stub()
        testOptions.modules.execute.actions.watchExecute = watchExecuteStub
    })

    const sandbox = sinon.sandbox.create()

    afterEach(function () {
        sandbox.restore()
    })

    it('should call action loadTopics on mount', async () => {
        const getTopics = sandbox.stub(api.default.topics, 'all', () => Promise.resolve(topics))
        const getLogs = sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(logs))

        const store = new Vuex.Store(testOptions)
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        expect(getTopics).to.have.been.calledWith()
        expect(getLogs).to.have.been.calledWith(0, 1)
        expect(watchExecuteStub).to.have.been.called

        expect(vm.executeLoading).to.be.true
        expect(vm.topicsLoading).to.be.true

        await Vue.nextTick()

        expect(vm.executeLoading).to.be.false
        expect(vm.topicsLoading).to.be.false
    })

    it('should call Header.setFilter should raise change-filter event', async () => {
        const getTopics = sandbox.stub(api.default.topics, 'all', () => Promise.resolve(topics))
        const getLogs = sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(logs))

        const store = new Vuex.Store(testOptions)
        const commit = sandbox.stub(store, 'commit')
        const Constructor = Vue.extend({...Topics, store})

        const vm = new Constructor().$mount()

        expect(getTopics).to.have.been.calledWith()
        expect(getLogs).to.have.been.calledWith(0, 1)
        expect(watchExecuteStub).to.have.been.called

        await Vue.nextTick()

        vm.$refs.header.setFilter('lostfilm')

        expect(commit).to.have.been.calledWith(types.SET_FILTER_STRING, { value: 'lostfilm' })
    })

    it('should call Header.setOrder should raise change-order event', async () => {
        const getTopics = sandbox.stub(api.default.topics, 'all', () => Promise.resolve(topics))
        const getLogs = sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(logs))

        const store = new Vuex.Store(testOptions)
        const commit = sandbox.stub(store, 'commit')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        expect(getTopics).to.have.been.calledWith()
        expect(getLogs).to.have.been.calledWith(0, 1)
        expect(watchExecuteStub).to.have.been.called

        await Vue.nextTick()

        vm.$refs.header.setOrder('-last_update')

        expect(commit).to.have.not.been.calledWith(types.SET_FILTER_STRING, sinon.match.any)
        expect(commit).to.have.been.calledWith(types.SET_ORDER, { order: '-last_update' })
    })

    it('should return not paused trackers', async () => {
        const topics = [
            {display_name: 'Zeta', tracker: 'lostfilm.tv', paused: false, last_update: '2017-02-13T23:00:00+00:00'},
            {display_name: 'Yota', tracker: 'lostfilm.tv', paused: false, last_update: null},
            {display_name: 'Alpha', tracker: 'rutracker.org', paused: true, last_update: null},
            {display_name: 'Beta', tracker: 'rutracker.org', paused: false, last_update: null},
            {display_name: 'Gamma', tracker: 'hdclub.org', paused: true, last_update: null},
            {display_name: 'Delta', tracker: 'hdclub.org', paused: true, last_update: null}
        ]

        sandbox.stub(api.default.topics, 'all', () => Promise.resolve(topics))
        sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(logs))

        const store = new Vuex.Store(testOptions)
        sandbox.stub(store, 'commit')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.canExecuteTracker('lostfilm.tv')).to.be.ok
        expect(vm.canExecuteTracker('rutracker.org')).to.be.ok
        expect(vm.canExecuteTracker('hdclub.org')).to.be.not.ok
        expect(watchExecuteStub).to.have.been.called
    })

    it('should call action setTopicPaused on set-paused event from TopicsList', async () => {
        const store = new Vuex.Store(testOptions)
        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        dispatch.reset()

        vm.$refs.list.setPaused(10, false)

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledOnce
        expect(dispatch).to.have.been.calledWith('setTopicPaused', {id: 10, value: false})
    })

    it('should call action resetTopicStatus on set-paused event from TopicsList', async () => {
        const store = new Vuex.Store(testOptions)
        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        dispatch.reset()

        vm.$refs.list.resetStatus(10)

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledOnce
        expect(dispatch).to.have.been.calledWith('resetTopicStatus', 10)
    })

    it('should display dialog DeleteTopic on on delete-topic event from TopicsList', async () => {
        const store = new Vuex.Store(testOptions)

        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        expect(vm.$refs.deleteTopicDialog.$el.className).to.not.contain('md-active')

        vm.$refs.list.deleteTopic(10)

        await new Promise((resolve, reject) => setTimeout(resolve, 0))

        expect(vm.$refs.deleteTopicDialog.$el.className).to.contain('md-active')
    })

    it('should display dialog DeleteTopic on on delete-topic event from TopicsList, and close dialog on cancel', async () => {
        const store = new Vuex.Store(testOptions)

        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        dispatch.reset()

        expect(vm.$refs.deleteTopicDialog.$el.className).to.not.contain('md-active')

        vm.$refs.list.deleteTopic(10)

        // https://github.com/marcosmoura/vue-material/blob/master/src/components/mdDialog/mdDialog.vue#L130
        // mdDialog used windwow.setTimeout for some features
        await new Promise((resolve, reject) => setTimeout(resolve, 0))

        expect(vm.$refs.deleteTopicDialog.$el.className).to.contain('md-active')

        vm.$refs.deleteTopicDialogNo.$el.click()

        await Vue.nextTick()
        await new Promise((resolve, reject) => setTimeout(resolve, 0))

        expect(vm.$refs.deleteTopicDialog.$el.className).to.not.contain('md-active')

        expect(dispatch).to.have.not.been.called
    })

    it('should display dialog DeleteTopic on on delete-topic event from TopicsList, and close dialog on ok', async () => {
        const store = new Vuex.Store(testOptions)

        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        dispatch.reset()

        expect(vm.$refs.deleteTopicDialog.$el.className).to.not.contain('md-active')

        vm.$refs.list.deleteTopic(10)

        // https://github.com/marcosmoura/vue-material/blob/master/src/components/mdDialog/mdDialog.vue#L130
        // mdDialog used windwow.setTimeout for some features
        await new Promise((resolve, reject) => setTimeout(resolve, 0))

        expect(vm.$refs.deleteTopicDialog.$el.className).to.contain('md-active')

        vm.$refs.deleteTopicDialogYes.$el.click()

        await Vue.nextTick()
        await new Promise((resolve, reject) => setTimeout(resolve, 0))

        expect(vm.$refs.deleteTopicDialog.$el.className).to.not.contain('md-active')

        expect(dispatch).to.have.been.calledWith('deleteTopic', 10)
    })

    it('should display dialog AddTopic on on add-topic event from TopicsHeader', async () => {
        const store = new Vuex.Store(testOptions)

        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        dispatch.reset()

        const openAddTopicDialogStub = sandbox.stub(vm.$refs.addEditTopicDialog, 'open')

        vm.$refs.header.addTopic()

        await Vue.nextTick()

        expect(openAddTopicDialogStub).have.been.calledOnce
    })

    it('on add-topic event action addTopic should be dispatched', async () => {
        const store = new Vuex.Store(testOptions)

        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        dispatch.reset()

        vm.$refs.addEditTopicDialog.addEdit()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledOnce
        expect(dispatch).to.have.been.calledWith('addTopic')
    })

    it('on edit-topic event action editTopic should be dispatched', async () => {
        const store = new Vuex.Store(testOptions)

        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        dispatch.reset()

        vm.$refs.addEditTopicDialog.mode = 'edit'
        vm.$refs.addEditTopicDialog.addEdit()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledOnce
        expect(dispatch).to.have.been.calledWith('editTopic')
    })

    it('on edit-topic event from topic list openEdit should be called', async () => {
        const store = new Vuex.Store(testOptions)

        const dispatch = sandbox.stub(store, 'dispatch')
        const Constructor = Vue.extend({...Topics, store})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(dispatch).to.have.been.calledThrice
        expect(dispatch).to.have.been.calledWith('loadLastExecute')
        expect(dispatch).to.have.been.calledWith('loadTopics')
        expect(dispatch).to.have.been.calledWith('watchExecute')

        dispatch.reset()

        const openEditStub = sandbox.stub(vm.$refs.addEditTopicDialog, 'openEdit', () => new Promise((resolve, reject) => resolve()))

        vm.$refs.list.editTopic(12)

        await Vue.nextTick()

        expect(openEditStub).to.have.been.calledOnce
        expect(openEditStub).to.have.been.calledWith(12)
    })
})
