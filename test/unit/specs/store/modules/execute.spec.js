import * as api from 'src/api/monitorrent'
import store from 'src/store/modules/execute'
import types from 'src/store/types'
import { expect } from 'chai'
import fetchMock from 'fetch-mock'

describe('store/modules/execute', () => {
    const sandbox = sinon.sandbox.create()

    afterEach(() => {
        sandbox.restore()
        fetchMock.restore()
    })

    describe('mutations', () => {
        const stateBase = { loading: true, last_execute: null }

        it('SET_LAST_EXECUTE', () => {
            let state = { ...stateBase }
            const execute = {finish_time: '2017-02-14T00:25:17+00:00'}

            expect(state.loading).to.be.true
            expect(state.last_execute).to.be.null

            store.mutations[types.SET_LAST_EXECUTE](state, { execute })

            expect(state.loading).to.be.false
            expect(state.last_execute).to.equal(execute)
        })

        it('LOAD_EXECUTE_FAILED', () => {
            const execute = {finish_time: '2017-02-14T00:25:17+00:00'}
            const state = { ...stateBase, last_execute: execute }
            const err = new Error('Can not reach remote server')

            expect(state.last_execute).to.equal(execute)
            expect(state.loading).to.be.true

            store.mutations[types.LOAD_EXECUTE_FAILED](state, { err })

            expect(state.last_execute).to.equal(null)
            expect(state.loading).to.be.false
        })
    })

    describe('actions', () => {
        const logs = {
            count: 1,
            data: [
                {finish_time: '2017-02-14T01:35:47+00:00'}
            ]
        }

        it('loadLastExecute should works', async () => {
            sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(logs))

            const commit = sandbox.spy()

            await store.actions.loadLastExecute({ commit })

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_LAST_EXECUTE, { execute: logs.data[0] })
        })

        it('loadLastExecute should works with empty logs', async () => {
            const emptyLogs = {count: 0, data: []}
            sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(emptyLogs))

            const commit = sandbox.spy()

            await store.actions.loadLastExecute({ commit })

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_LAST_EXECUTE, { execute: null })
        })

        it('should throw on 3xx error response', async () => {
            var error = {topic: 'NotModified', description: 'Not Modified'}
            fetchMock.get(`/api/execute/logs?skip=0&take=1`, { status: 304, body: JSON.stringify(error) })

            const commit = sandbox.spy()

            await store.actions.loadLastExecute({ commit })

            expect(commit).have.been.calledOnce
            expect(commit.lastCall.args[0]).to.be.equal(types.LOAD_EXECUTE_FAILED)
        })
    })
})
