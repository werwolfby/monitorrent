import Vue from 'vue'
import Vuex from 'vuex'
import _ from 'lodash'
import * as api from 'src/api/monitorrent'
import { options } from 'src/store'
import types from 'src/store/types'
import Topics from 'src/components/Topics/Topics'

describe('Topics.vue', () => {
    let testOptions
    beforeEach(() => {
        testOptions = _.cloneDeep(options)
    })

    it('should call action loadTopics on mount', async () => {
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

        try {
            const getTopics = sinon.stub(api.default, 'getTopics', () => Promise.resolve(topics))
            const getLogs = sinon.stub(api.default, 'getLogs', () => Promise.resolve(logs))

            const store = new Vuex.Store(testOptions)
            const Constructor = Vue.extend({...Topics, store})
            new Constructor().$mount()

            expect(getTopics).to.have.been.calledWith()
            expect(getLogs).to.have.been.calledWith(0, 1)

            await Vue.nextTick()
        } finally {
            api.default.getTopics.restore()
            api.default.getLogs.restore()
        }
    })

    it('should call Header.setFilter should raise change-filter event', async () => {
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

        try {
            const getTopics = sinon.stub(api.default, 'getTopics', () => Promise.resolve(topics))
            const getLogs = sinon.stub(api.default, 'getLogs', () => Promise.resolve(logs))

            const store = new Vuex.Store(testOptions)
            try {
                const commit = sinon.stub(store, 'commit')
                const Constructor = Vue.extend({...Topics, store})

                const vm = new Constructor().$mount()

                expect(getTopics).to.have.been.calledWith()
                expect(getLogs).to.have.been.calledWith(0, 1)

                await Vue.nextTick()

                vm.$refs.header.setFilter('lostfilm')

                expect(commit).to.have.been.calledWith(types.SET_FILTER_STRING, { value: 'lostfilm' })
            } finally {
                store.commit.restore()
            }
        } finally {
            api.default.getTopics.restore()
            api.default.getLogs.restore()
        }
    })

    it('should call Header.setOrder should raise change-order event', async () => {
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

        try {
            const getTopics = sinon.stub(api.default, 'getTopics', () => Promise.resolve(topics))
            const getLogs = sinon.stub(api.default, 'getLogs', () => Promise.resolve(logs))

            const store = new Vuex.Store(testOptions)
            try {
                const commit = sinon.stub(store, 'commit')
                const Constructor = Vue.extend({...Topics, store})
                const vm = new Constructor().$mount()

                expect(getTopics).to.have.been.calledWith()
                expect(getLogs).to.have.been.calledWith(0, 1)

                await Vue.nextTick()

                vm.$refs.header.setOrder('-last_update')

                expect(commit).to.have.not.been.calledWith(types.SET_FILTER_STRING, sinon.match.any)
                expect(commit).to.have.been.calledWith(types.SET_ORDER, { order: '-last_update' })
            } finally {
                store.commit.restore()
            }
        } finally {
            api.default.getTopics.restore()
            api.default.getLogs.restore()
        }
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

        const logs = {
            count: 1,
            data: [
                {finish_time: '2017-02-14T01:35:47+00:00'}
            ]
        }

        try {
            sinon.stub(api.default, 'getTopics', () => Promise.resolve(topics))
            sinon.stub(api.default, 'getLogs', () => Promise.resolve(logs))

            const store = new Vuex.Store(testOptions)
            try {
                sinon.stub(store, 'commit')
                const Constructor = Vue.extend({...Topics, store})
                const vm = new Constructor().$mount()

                await Vue.nextTick()

                expect(vm.canExecuteTracker('lostfilm.tv')).to.be.ok
                expect(vm.canExecuteTracker('rutracker.org')).to.be.ok
                expect(vm.canExecuteTracker('hdclub.org')).to.be.not.ok
            } finally {
                store.commit.restore()
            }
        } finally {
            api.default.getTopics.restore()
            api.default.getLogs.restore()
        }
    })

    it('should call action setTopicPaused on set-paused event from TopicsList', async () => {
        const store = new Vuex.Store(testOptions)
        try {
            const dispatch = sinon.stub(store, 'dispatch')
            const Constructor = Vue.extend({...Topics, store})
            const vm = new Constructor().$mount()

            await Vue.nextTick()

            expect(dispatch).to.have.been.calledOnce
            expect(dispatch).to.have.been.calledWith('loadTopics')

            dispatch.reset()

            vm.$refs.list.setPaused(10, false)

            await Vue.nextTick()

            expect(dispatch).to.have.been.calledOnce
            expect(dispatch).to.have.been.calledWith('setTopicPaused', {id: 10, value: false})
        } finally {
            store.dispatch.restore()
        }
    })

    it('should call action resetTopicStatus on set-paused event from TopicsList', async () => {
        const store = new Vuex.Store(testOptions)
        try {
            const dispatch = sinon.stub(store, 'dispatch')
            const Constructor = Vue.extend({...Topics, store})
            const vm = new Constructor().$mount()

            await Vue.nextTick()

            expect(dispatch).to.have.been.calledOnce
            expect(dispatch).to.have.been.calledWith('loadTopics')

            dispatch.reset()

            vm.$refs.list.resetStatus(10)

            await Vue.nextTick()

            expect(dispatch).to.have.been.calledOnce
            expect(dispatch).to.have.been.calledWith('resetTopicStatus', 10)
        } finally {
            store.dispatch.restore()
        }
    })

    it('should display dialog DeleteTopic on on delete-topic event from TopicsList', async () => {
        const store = new Vuex.Store(testOptions)

        try {
            const dispatch = sinon.stub(store, 'dispatch')
            const Constructor = Vue.extend({...Topics, store})
            const vm = new Constructor().$mount()

            await Vue.nextTick()

            expect(dispatch).to.have.been.calledOnce
            expect(dispatch).to.have.been.calledWith('loadTopics')

            expect(vm.$refs.deleteTopicDialog.$el.className).to.not.contain('md-active')

            vm.$refs.list.deleteTopic(10)

            await new Promise((resolve, reject) => setTimeout(resolve, 0))

            expect(vm.$refs.deleteTopicDialog.$el.className).to.contain('md-active')
        } finally {
            store.dispatch.restore()
        }
    })

    it('should display dialog DeleteTopic on on delete-topic event from TopicsList, and close dialog on cancel', async () => {
        const store = new Vuex.Store(testOptions)

        try {
            const dispatch = sinon.stub(store, 'dispatch')
            const Constructor = Vue.extend({...Topics, store})
            const vm = new Constructor().$mount()

            await Vue.nextTick()

            expect(dispatch).to.have.been.calledOnce
            expect(dispatch).to.have.been.calledWith('loadTopics')

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
        } finally {
            store.dispatch.restore()
        }
    })

    it('should display dialog DeleteTopic on on delete-topic event from TopicsList, and close dialog on ok', async () => {
        const store = new Vuex.Store(testOptions)

        try {
            const dispatch = sinon.stub(store, 'dispatch')
            const Constructor = Vue.extend({...Topics, store})
            const vm = new Constructor().$mount()

            await Vue.nextTick()

            expect(dispatch).to.have.been.calledOnce
            expect(dispatch).to.have.been.calledWith('loadTopics')

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
        } finally {
            store.dispatch.restore()
        }
    })
})
