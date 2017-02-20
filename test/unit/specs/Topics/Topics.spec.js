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

                const vm = new Constructor({ '$store': { 'dispatch': () => {} } }).$mount()

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
                const vm = new Constructor({ '$store': { 'dispatch': () => {} } }).$mount()

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
})
