import * as api from 'src/api/monitorrent'
import store from 'src/store/modules/trackers'
import types from 'src/store/types'
import delay from 'delay'
import { expect } from 'chai'

describe('store/modules/trackers', () => {
    const sandbox = sinon.sandbox.create()

    afterEach(() => {
        sandbox.restore()
    })

    describe('mutations', () => {
        const stateBase = { loading: true, error: null, trackers: [] }

        it('SET_TRACKERS', () => {
            const state = {...stateBase}
            const trackers = [
                {name: 'tracker1.com', form: null},
                {name: 'tracker2.com', form: null}
            ]
            store.mutations[types.SET_TRACKERS](state, trackers)

            expect(state).to.be.eql({ loading: false, error: null, trackers: [...trackers] })
        })

        it('LOAD_TRACKERS_FAILED', () => {
            const trackers = [
                {name: 'tracker1.com', form: null},
                {name: 'tracker2.com', form: null}
            ]
            const state = {...stateBase, trackers}
            const error = Error('Error')
            store.mutations[types.LOAD_TRACKERS_FAILED](state, error)

            expect(state).to.be.eql({ loading: false, error: error, trackers: [] })
        })
    })

    describe('actions', () => {
        const trackers = [
            {name: 'tracker1.com', form: null},
            {name: 'tracker2.com', form: null}
        ]

        it('loadTrackers should works', async () => {
            sandbox.stub(api.default.trackers, 'all', () => delay(0, trackers))

            const commit = sandbox.spy()

            await store.actions.loadTrackers({ commit })

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_TRACKERS, trackers)
        })

        it('loadTrackers should fails on error', async () => {
            const error = Error()
            sandbox.stub(api.default.trackers, 'all', () => delay.reject(0, error))

            const commit = sandbox.spy()

            await store.actions.loadTrackers({ commit })

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.LOAD_TRACKERS_FAILED, error)
        })
    })
})
